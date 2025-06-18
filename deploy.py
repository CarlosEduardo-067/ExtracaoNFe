# deploy.py (atualizado)
import boto3
import time
from infrastructure.s3 import create_s3_bucket
from infrastructure.iam import create_iam_roles
from infrastructure.lambdas import create_lambda_functions
from infrastructure.step_function import create_step_function 
from infrastructure.api_gateway import create_rest_api
from infrastructure.layers import create_layers, attach_layers_to_functions  # Adicionado
from config.settings import AWS_CREDENTIALS, LAMBDA_NAMES, LAMBDA_LAYERS, BUCKET_NAME, REGION

def get_boto3_client(service_name):
    """Configura o cliente AWS com credenciais temporárias"""
    return boto3.client(
        service_name,
        region_name=REGION,
        aws_access_key_id=AWS_CREDENTIALS['aws_access_key_id'],
        aws_secret_access_key=AWS_CREDENTIALS['aws_secret_access_key'],
        aws_session_token=AWS_CREDENTIALS['aws_session_token']
    )

def main():
    print("--------------------------------------------------------")
    print("Iniciando implantação da infraestrutura...")
    print("--------------------------------------------------------")
    
    try:
        # 1. Criação do S3
        s3_client = get_boto3_client('s3')
        create_s3_bucket(s3_client, BUCKET_NAME, REGION)
        print("--------------------------------------------------------")
        print("Bucket S3 criado")
        print("--------------------------------------------------------")

        # 2. Criação de políticas e roles IAM
        iam_client = get_boto3_client('iam')
        lambda_roles, stepfunctions_role_arn = create_iam_roles(iam_client)
        print("--------------------------------------------------------")
        print("Permissões IAM configuradas")
        print("--------------------------------------------------------")

        # Pausa para propagação das roles IAM
        print("Aguardando 5 segundos para propagação das roles IAM...")
        time.sleep(5)

        # 3. Criação dos Layers
        lambda_client = get_boto3_client('lambda')
        layer_arns = create_layers(lambda_client)
        print("--------------------------------------------------------")
        print("Layers criados")
        print("--------------------------------------------------------")

        # 4. Criação das funções Lambda
        lambda_arns = create_lambda_functions(lambda_client, lambda_roles)

        
        # Anexa layers específicos a cada função
        if layer_arns:
            from config import settings
            attach_layers_to_functions(
                lambda_client,
                {
                    'LAMBDA_NAMES': LAMBDA_NAMES,
                    'LAMBDA_LAYERS': LAMBDA_LAYERS
                },
                layer_arns
            )
            
        print("--------------------------------------------------------")
        print("Funções Lambda criadas com as roles específicas")
        print("--------------------------------------------------------")

        # 5. Criação da Step Function
        stepfunctions_client = get_boto3_client('stepfunctions')
        step_function_arn = create_step_function(
            stepfunctions_client,
            stepfunctions_role_arn,
            lambda_arns
        )
        print("--------------------------------------------------------")
        print("Step Function criada")
        print("--------------------------------------------------------")

        # 6. Criação da API Gateway
        apigateway_client = get_boto3_client('apigateway')
        api_url = create_rest_api(
            apigateway_client, 
            lambda_client, 
            lambda_arns['integracao']
        )
        print("--------------------------------------------------------")
        print(f"API Gateway criada\nURL: {api_url}/invoice")
        print("--------------------------------------------------------")

    except Exception as e:
        print(f"\nErro durante a implantação: {e}")
        raise

if __name__ == '__main__':
    main()