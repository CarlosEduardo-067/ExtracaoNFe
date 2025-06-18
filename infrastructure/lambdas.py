import os
import zipfile
import tempfile
import time
from botocore.exceptions import ClientError
from config.settings import LAMBDA_NAMES, PYTHON_VERSION, LAMBDA_FILES, LAMBDA_ROLES

def create_lambda_functions(lambda_client, lambda_roles):
    lambda_arns = {}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for lambda_type, filename in LAMBDA_FILES.items():
            # Caminho absoluto do arquivo
            source_path = os.path.join(os.path.dirname(__file__), '..', 'lambda_functions', filename)
            source_path = os.path.normpath(source_path)
            
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Arquivo Lambda não encontrado: {source_path}")

            # Cria o ZIP
            zip_path = os.path.join(temp_dir, f'{lambda_type}.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(source_path, os.path.basename(source_path))
            
            # Lê o conteúdo do ZIP
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Obtém a ARN da role correta para esta Lambda
            role_name = LAMBDA_ROLES[lambda_type]
            role_arn = lambda_roles[role_name]
            
            try:
                response = lambda_client.create_function(
                    FunctionName=LAMBDA_NAMES[lambda_type],
                    Runtime=PYTHON_VERSION,
                    Role=role_arn,
                    Handler=f"{filename.replace('.py', '')}.lambda_handler",
                    Code={'ZipFile': zip_content},
                    Timeout=30
                )
                lambda_arns[lambda_type] = response['FunctionArn']
                print(f"✅ Lambda {LAMBDA_NAMES[lambda_type]} criada com sucesso (Role: {role_name}).")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceConflictException':
                    print(f"🔄 Lambda {LAMBDA_NAMES[lambda_type]} já existe. Atualizando...")
                    lambda_client.update_function_code(
                        FunctionName=LAMBDA_NAMES[lambda_type],
                        ZipFile=zip_content
                    )
                    # Atualiza também a role se necessário apos alguns 2 segundos de propagação
                    time.sleep(2)
                    lambda_client.update_function_configuration(
                        FunctionName=LAMBDA_NAMES[lambda_type],
                        Role=role_arn
                    )
                    lambda_info = lambda_client.get_function(FunctionName=LAMBDA_NAMES[lambda_type])
                    lambda_arns[lambda_type] = lambda_info['Configuration']['FunctionArn']
                    
                else:
                    print(f"❌ Erro na Lambda {LAMBDA_NAMES[lambda_type]}: {e}")
                    raise
    
    return lambda_arns