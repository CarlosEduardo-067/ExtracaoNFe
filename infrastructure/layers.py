# infrastructure/layers.py
import os
import time
from botocore.exceptions import ClientError
from config.settings import PYTHON_VERSION, LAYERS_CONFIG  # Importando do settings

def create_layer(lambda_client, layer_name, config):
    """Cria ou atualiza um Lambda Layer"""
    # Primeiro verifica se o layer já existe
    try:
        # Lista todas as versões do layer (ordena decrescente por versão)
        response = lambda_client.list_layer_versions(
            LayerName=layer_name,
            MaxItems=1  # Pega apenas a versão mais recente
        )
        
        # Se encontrou versões existentes, retorna a ARN da mais recente
        if response.get('LayerVersions'):
            latest_version = response['LayerVersions'][0]
            print(f"ℹ️ Layer {layer_name} já existe (versão {latest_version['Version']}) - usando versão existente")
            return latest_version['LayerVersionArn']
            
    except ClientError as e:
        # Se o erro for que o layer não existe, continuamos para criá-lo
        if e.response['Error']['Code'] != 'ResourceNotFoundException':
            print(f"❌ Erro ao verificar layer existente {layer_name}: {e}")
            raise

    # Se chegou aqui, o layer não existe ou ocorreu um erro que podemos ignorar
    zip_path = os.path.join(os.path.dirname(__file__), '..', 'layers', config['zip_file'])
    zip_path = os.path.normpath(zip_path)
    
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Arquivo ZIP do layer não encontrado: {zip_path}")

    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    try:
        response = lambda_client.publish_layer_version(
            LayerName=layer_name,
            Description=config['description'],
            Content={'ZipFile': zip_content},
            CompatibleRuntimes=config['compatible_runtimes'],
            LicenseInfo=config['license_info']
        )
        layer_arn = response['LayerVersionArn']
        print(f"✅ Layer {layer_name} criado com sucesso. ARN: {layer_arn}")
        return layer_arn
        
    except ClientError as e:
        print(f"❌ Erro ao criar layer {layer_name}: {e}")
        raise

def create_layers(lambda_client):
    """Cria todos os layers configurados e retorna seus ARNs"""
    layer_arns = {}
    
    for layer_name, config in LAYERS_CONFIG.items():  # Usando LAYERS_CONFIG do settings
        try:
            layer_arn = create_layer(lambda_client, layer_name, config)
            layer_arns[layer_name] = layer_arn
            # Pequena pausa para evitar throttling
            time.sleep(1)
            
        except Exception as e:
            print(f"⚠️ Falha ao processar layer {layer_name}: {e}")
            continue
    
    return layer_arns

def attach_layers_to_functions(lambda_client, lambda_config, layer_arns):
    """
    Anexa os layers específicos a cada função Lambda conforme configuração
    
    Args:
        lambda_client: Cliente boto3 para Lambda
        lambda_config: Dicionário com:
            - 'LAMBDA_NAMES': Mapeamento de tipos para nomes de funções
            - 'LAMBDA_LAYERS': Mapeamento de tipos para lists de layers requeridos
        layer_arns: Dicionário de ARNs dos layers criados
    """
    for lambda_type, function_name in lambda_config['LAMBDA_NAMES'].items():
        # Obtém lista de layers necessários para esta função
        layers_needed = lambda_config['LAMBDA_LAYERS'].get(lambda_type, [])
        
        if not layers_needed:
            print(f"ℹ️ Lambda {function_name} não requer layers - pulando")
            continue
        
        # Filtra apenas layers que existem
        layer_arns_to_attach = [
            layer_arns[layer_name] 
            for layer_name in layers_needed 
            if layer_name in layer_arns
        ]
        
        if not layer_arns_to_attach:
            print(f"⚠️ Nenhum layer válido encontrado para {function_name}")
            continue

        try:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=layer_arns_to_attach
            )
            print(f"✅ Layers anexados à {function_name}: {', '.join(layers_needed)}")
            
            # Pequena pausa entre atualizações
            time.sleep(0.5)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceConflictException':
                print(f"🔄 Tentando novamente para {function_name} após conflito...")
                time.sleep(2)
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Layers=layer_arns_to_attach
                )
            else:
                print(f"❌ Erro ao anexar layers à {function_name}: {e}")