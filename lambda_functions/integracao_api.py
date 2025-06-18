import json
import os
import base64
import logging
import boto3
import time
from botocore.exceptions import NoCredentialsError
from requests_toolbelt.multipart import decoder

# Configuração do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

def upload_to_s3(bucket_name, file_name, file_content):
    """Faz upload de um arquivo para o S3"""
    try:
        logger.info(f"Iniciando upload do arquivo {file_name} para o S3")
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_content
        )
        logger.info(f"Upload do arquivo {file_name} concluído com sucesso")
        return {
            'statusCode': 200,
            'body': json.dumps({'file_name': file_name})
        }
    except Exception as e:
        logger.error(f"Erro ao fazer upload: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno no servidor'})
        }

def validate_and_extract_file(event):
    """Valida o evento e extrai o arquivo"""
    if 'body' not in event:
        logger.warning("Evento sem corpo")
        return False, 'Formato de requisição inválido'
    
    content_type = event['headers'].get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        logger.warning(f"Formato de conteúdo inválido: {content_type}")
        return False, 'Formato inválido. Use multipart/form-data'
    
    body = event['body']
    if event.get('isBase64Encoded', False):
        try:
            body = base64.b64decode(body)
        except Exception as e:
            logger.error(f"Erro ao decodificar Base64: {str(e)}")
            return False, 'Erro ao processar o arquivo'
    
    try:
        multipart_data = decoder.MultipartDecoder(body, content_type)
    except Exception as e:
        logger.error(f"Erro ao decodificar multipart: {str(e)}")
        return False, 'Erro ao processar arquivo'
    
    for part in multipart_data.parts:
        if part.headers.get(b'Content-Disposition'):
            disposition = part.headers[b'Content-Disposition'].decode()
            if 'filename=' in disposition:
                file_name = disposition.split('filename=')[-1].strip().replace('"', '')
                file_content = part.content
                
                if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    logger.warning(f"Arquivo {file_name} não é uma imagem válida")
                    return False, 'O arquivo deve ser uma imagem (PNG, JPG, JPEG)'
                
                return True, (file_name, file_content)
    
    logger.warning("Nenhum arquivo encontrado no corpo da requisição")
    return False, 'Nenhum arquivo encontrado'

def execute_step_function(context, bucket_name, file_name):
    """Executa a Step Function e aguarda seu resultado"""
    try:
        # Extrai o ARN da Step Function
        aws_region = context.invoked_function_arn.split(':')[3]
        aws_account_id = context.invoked_function_arn.split(':')[4]
        arn_step_function = f'arn:aws:states:{aws_region}:{aws_account_id}:stateMachine:notas-fiscais-step-function'

        # Prepara a entrada para a Step Function
        step_function_input = {
            "file_name": file_name,
            "bucket_name": bucket_name,
        }

        # Inicia a execução da Step Function
        response = stepfunctions.start_execution(
            stateMachineArn=arn_step_function,
            input=json.dumps(step_function_input)
        )

        execution_arn = response['executionArn']
        
        # Monitora a execução
        while True:
            execution_status = stepfunctions.describe_execution(executionArn=execution_arn)
            status = execution_status['status']

            if status == 'SUCCEEDED':
                output = json.loads(execution_status['output'])
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(output)
                }
            elif status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Step Function execution failed',
                        'executionArn': execution_arn,
                        'status': status
                    })
                }
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Erro na execução da Step Function: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro ao executar Step Function'})
        }

def lambda_handler(event, context):
    """Função principal da Lambda"""
    logger.info(f"Lambda iniciada. Request ID: {context.aws_request_id}")
    
    try:
        bucket_name = os.environ.get('S3_BUCKET_NAME', 'grupo-1-notas-fiscais-s3') # Passar para variavel ambiente
        is_valid, validation_message = validate_and_extract_file(event)
        
        if not is_valid:
            logger.warning("Upload não foi bem-sucedido - validação falhou")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': validation_message})
            }
        
        file_name, file_content = validation_message
        upload_response = upload_to_s3(bucket_name, file_name, file_content)
        
        if upload_response['statusCode'] != 200:
            return upload_response
        
        logger.info("Upload bem sucedido, iniciando Step Function")
        return execute_step_function(context, bucket_name, file_name)
        
    except NoCredentialsError:
        logger.error("Credenciais da AWS não encontradas")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Credenciais da AWS não encontradas'})
        }
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno no servidor'})
        }