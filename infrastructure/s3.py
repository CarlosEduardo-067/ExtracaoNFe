from botocore.exceptions import ClientError
from config.settings import BUCKET_NAME, REGION

def create_s3_bucket(s3_client, BUCKET_NAME, REGION):
    try:
        # Tenta criar o bucket (com tratamento especial para us-east-1)
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print(f"✅ Bucket {BUCKET_NAME} criado com sucesso.")

    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists':
            print(f"⚠️ Bucket {BUCKET_NAME} já existe. Continuando...")
        else:
            print(f"❌ Erro ao criar bucket: {e}")
            raise  # Só relança erros que não são "BucketAlreadyExists"

    # Cria as pastas independentemente se o bucket é novo ou existente
    try:
        s3_client.put_object(Bucket=BUCKET_NAME, Key='dinheiro/')
        s3_client.put_object(Bucket=BUCKET_NAME, Key='outros/')
        print("✅ Pastas 'dinheiro' e 'outros' criadas/verificadas")
    except ClientError as e:
        print(f"❌ Erro ao criar pastas: {e}")
        raise