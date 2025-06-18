import time
from botocore.exceptions import ClientError
from config.settings import AWS_ACCOUNT_ID, API_NAME, LAMBDA_NAMES, REGION

def create_rest_api(apigateway_client, lambda_client, lambda_arn):
    try:
        # 1. Verifica se a API já existe
        apis = apigateway_client.get_rest_apis()['items']
        api = next((api for api in apis if api['name'] == API_NAME), None)
        
        if api:
            api_id = api['id']
            print(f"🔄 API '{API_NAME}' já existe (ID: {api_id})")
        else:
            api = apigateway_client.create_rest_api(
                name=API_NAME,
                description='API para processamento de notas fiscais',
                endpointConfiguration={'types': ['REGIONAL']},
                binaryMediaTypes=['*/*']  # Aceita qualquer tipo de mídia binária
            )
            api_id = api['id']
            print(f"✅ API '{API_NAME}' criada (ID: {api_id})")

        # 2. Configuração do recurso /invoice
        resources = apigateway_client.get_resources(restApiId=api_id)['items']
        root_id = next(res['id'] for res in resources if res['path'] == '/')
        
        resource = next(
            (res for res in resources if res.get('path') == '/invoice'),
            None
        )
        
        if resource:
            resource_id = resource['id']
            print("🔄 Recurso /invoice já existe")
        else:
            resource = apigateway_client.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='invoice'
            )
            resource_id = resource['id']
            print("✅ Recurso /invoice criado")

        # 3. Configuração do método POST
        try:
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST',
                authorizationType='NONE',
                requestParameters={
                    'method.request.header.Content-Type': True
                }
            )
            print("✅ Método POST configurado")
        except apigateway_client.exceptions.ConflictException:
            print("🔄 Método POST já existe")

        # 4. Configuração da integração como proxy
        apigateway_client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations',
            contentHandling='CONVERT_TO_BINARY'  # Converte o payload para binário
        )
        print("✅ Integração Lambda proxy configurada")

        # 5. Configuração de permissões (com ID único)
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_NAMES['integracao'],
                StatementId=f"apigateway-invoke-{int(time.time())}",
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{REGION}:{AWS_ACCOUNT_ID}:{api_id}/*/POST/invoice"
            )
            print("✅ Permissão Lambda configurada")
        except lambda_client.exceptions.ResourceConflictException:
            print("🔒 Permissão já existe - continuando")

        # 6. Atualiza a configuração binária da API se ela já existia
        if api:
            apigateway_client.update_rest_api(
                restApiId=api_id,
                patchOperations=[
                    {
                        'op': 'add',
                        'path': '/binaryMediaTypes/*~1*'
                    }
                ]
            )
            print("✅ Configuração de mídia binária atualizada para aceitar */*")

        # 7. Implantação
        deployment = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='v1',
            description=f'Deploy em {time.strftime("%Y-%m-%d %H:%M:%S")}'
        )
        print(f"✅ API implantada (Deployment ID: {deployment['id']})")

        api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/v1"
        print(f"🎉 Endpoint pronto: {api_url}/invoice")
        return api_url

    except Exception as e:
        print(f"❌ Erro fatal na API Gateway: {str(e)}")
        raise