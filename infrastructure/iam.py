import json
from botocore.exceptions import ClientError
from config.settings import AWS_ACCOUNT_ID

def create_custom_iam_policies(iam_client):
    """Cria políticas personalizadas além das políticas gerenciadas da AWS"""
    policies = {
        'TextractFullAccessPolicy': {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": "textract:*",
                "Resource": "*"
            }]
        }
    }

    for name, policy_doc in policies.items():
        try:
            iam_client.create_policy(
                PolicyName=name,
                PolicyDocument=json.dumps(policy_doc),
                Description=f'Política para acesso total ao {name.split("Policy")[0]}'
            )
            print(f"✅ Política {name} criada")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"🔄 Política {name} já existe - continuando")

def create_lambda_roles(iam_client):
    """Cria as 4 roles específicas para as Lambdas"""
    roles_config = {
        'RoleDefault': {
            'description': 'Role com acesso apenas ao CloudWatch',
            'policies': ['arn:aws:iam::aws:policy/CloudWatchFullAccess']
        },
        'RoleS3': {
            'description': 'Role com acesso ao CloudWatch e S3',
            'policies': [
                'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess'
            ]
        },
        'RoleStep': {
            'description': 'Role com acesso ao CloudWatch, S3 e StepFunctions',
            'policies': [
                'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                'arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess'
            ]
        },
        'RoleS3Textract': {
            'description': 'Role com acesso ao CloudWatch, S3 e Textract',
            'policies': [
                'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                f'arn:aws:iam::{AWS_ACCOUNT_ID}:policy/TextractFullAccessPolicy'
            ]
        },
        'RoleS3Step': {
            'description': 'Role com acesso ao CloudWatch, S3 e StepFunctions',
            'policies': [
                'arn:aws:iam::aws:policy/CloudWatchFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                'arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess'
            ]
        },
    }

    role_arns = {}
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    # Cria políticas personalizadas primeiro
    create_custom_iam_policies(iam_client)

    for role_name, config in roles_config.items():
        try:
            response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=config['description']
            )
            role_arn = response['Role']['Arn']
            print(f"✅ Role {role_name} criada")
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"🔄 Role {role_name} já existe - atualizando")
            role = iam_client.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']

        # Anexa políticas
        for policy_arn in config['policies']:
            try:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                print(f"✅ Política {policy_arn.split('/')[-1]} anexada à {role_name}")
            except ClientError as e:
                print(f"⚠️ Erro ao anexar política {policy_arn} à {role_name}: {e}")

        role_arns[role_name] = role_arn

    return role_arns

def create_stepfunctions_execution_role(iam_client):
    """Cria role específica para Step Function com acesso às Lambdas"""
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "states.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        response = iam_client.create_role(
            RoleName='StepFunctionExecutionRole',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role para execução de Step Functions com acesso às Lambdas'
        )
        role_arn = response['Role']['Arn']
        print("✅ Role Step Functions criada")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print("🔄 Role Step Functions já existe - continuando")
        role = iam_client.get_role(RoleName='StepFunctionExecutionRole')
        role_arn = role['Role']['Arn']

    # Anexa política de acesso às Lambdas
    try:
        iam_client.attach_role_policy(
            RoleName='StepFunctionExecutionRole',
            PolicyArn='arn:aws:iam::aws:policy/AWSLambda_FullAccess'
        )
        print("✅ Política AWSLambda_FullAccess anexada à Role Step Functions")
    except ClientError as e:
        print(f"⚠️ Erro ao anexar política: {e}")

    return role_arn

def create_iam_roles(iam_client):
    """Orquestra a criação de todas as roles e políticas"""
    try:
        # Cria roles para Lambdas
        lambda_roles = create_lambda_roles(iam_client)
        
        # Cria role para Step Functions
        stepfunctions_role_arn = create_stepfunctions_execution_role(iam_client)
        
        return lambda_roles, stepfunctions_role_arn
        
    except Exception as e:
        print(f"❌ Erro fatal no IAM: {e}")
        raise