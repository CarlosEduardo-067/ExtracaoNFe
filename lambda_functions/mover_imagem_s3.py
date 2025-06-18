import boto3
import logging

logger = logging.getLogger()

s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Extrai os dados da entrada
        logger.info(f"ℹ️ Extraindo dados de entrada.")
        result_json = event["result_json"]

        file_name = event["file_name"]
        bucket_name = event["bucket_name"]

        forma_pgto = result_json["forma_pgto"]

        # Define a pasta de destino com base na forma de pagamento
        destino_key = f"{forma_pgto}/{file_name}"

        if forma_pgto == "dinheiropix":
           destino_key = f"dinheiro/{file_name}"

        # Define a pasta de destino com base na forma de pagamento
        logger.info(f"ℹ️ Definindo destino como {destino_key}")

        # Copia o arquivo para a pasta correspondente
        logger.info(f"ℹ️ Copiando o arquivo para a pasta correspondente.")
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': file_name},
            Key=destino_key
        )

        # Remove o arquivo da pasta raiz
        logger.info(f"ℹ️ Deletando o arquivo da pasta raiz.")
        s3.delete_object(
            Bucket=bucket_name,
            Key=file_name
        )

        # Retorna os dados para a próxima etapa
        logger.info(f"ℹ️ Deletando o arquivo da pasta raiz.")
        return result_json

    except Exception as e:
        logger.info(f"❌ Erro de exceção...")
        return {
            "error": str(e)  # Retorna um erro caso ocorra uma exceção
        }