import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("textract", region_name="us-east-1")

def process_document(bucket_name, object_name):
    try:
        logger.info(f"Processando o documento {object_name} no bucket {bucket_name}")
        # Chama o Textract diretamente para processar o documento no S3
        response = client.analyze_document(
            Document={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_name
                }
            },
            FeatureTypes=['FORMS', 'TABLES']
        )
        logger.info(f"Documento processado com sucesso: {object_name}")
        # Retorna a resposta completa do Textract
        return response

    except Exception as e:
        logger.info(f"Erro ao processar o documento no S3: {e}")
        return None

def extract_important_data(textract_response):
    #Filtra e exibe apenas as informações importantes extraídas de uma nota fiscal.
    logger.info("Extraindo dados importantes do documento processado")
    if not textract_response:
        print("Nenhuma resposta do Textract foi retornada.")
        return

    important_data = []

    for block in textract_response.get("Blocks", []):
        if block.get("BlockType") == "LINE" and "Text" in block:
            # Extrai apenas o texto relevante
            important_data.append(block["Text"])

    return important_data

def lambda_handler(event, context):
    
    # Processa o documento e obtém a resposta bruta do Textract
    bucket_name = event['bucket_name']
    file_name = event['file_name']

    logger.info("Iniciando o processamento do evento")
    
    response = process_document(bucket_name, file_name)

    if not response:
        return {
            'statusCode': 500,
            'body': json.dumps('Falha ao processar o documento com o Textract')
        }

    # Extrai apenas as informações importantes
    important_data = extract_important_data(response)

    string_important_data = "\n".join(important_data)

    # Retorna as informações extraídas
    return {
        'important_data': string_important_data,
        'file_name' : file_name,
        'bucket_name': bucket_name
    }