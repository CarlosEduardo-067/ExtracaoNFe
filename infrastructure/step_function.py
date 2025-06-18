import json
from botocore.exceptions import ClientError
from config.settings import STEP_FUNCTION_NAME, REGION, AWS_ACCOUNT_ID

def create_step_function(stepfunctions_client, stepfunctions_role_arn, lambda_arns):
    definition = {
        "Comment": "Step Function para processamento de notas fiscais",
        "StartAt": "Textract",
        "States": {
            "Textract": {
                "Type": "Task",
                "Resource": lambda_arns['textract'],
                "Next": "REGEX"
            },
            "REGEX": {
                "Type": "Task",
                "Resource": lambda_arns['regex'],
                "Next": "LLM"
            },
            "LLM": {
                "Type": "Task",
                "Resource": lambda_arns['llm'],
                "Next": "MoverIMG"
            },
            "MoverIMG": {
                "Type": "Task",
                "Resource": lambda_arns['mover_imagem'],
                "End": True
            },
        }
    }

    try:
        # Tenta criar nova Step Function
        response = stepfunctions_client.create_state_machine(
            name=STEP_FUNCTION_NAME,
            definition=json.dumps(definition),
            roleArn=stepfunctions_role_arn,
            type='STANDARD'
        )
        print(f"✅ Step Function '{STEP_FUNCTION_NAME}' criada com sucesso.")
        return response['stateMachineArn']

    except stepfunctions_client.exceptions.StateMachineAlreadyExists:
        # Se já existir, atualiza a definição
        existing_arn = f"arn:aws:states:{REGION}:{AWS_ACCOUNT_ID}:stateMachine:{STEP_FUNCTION_NAME}"
        
        response = stepfunctions_client.update_state_machine(
            stateMachineArn=existing_arn,
            definition=json.dumps(definition),
            roleArn=stepfunctions_role_arn
        )
        print(f"🔄 Step Function existente '{STEP_FUNCTION_NAME}' foi atualizada.")
        return existing_arn

    except Exception as e:
        print(f"❌ Erro ao processar Step Function: {e}")
        raise