# settings.py

# Configurações globais
AWS_ACCOUNT_ID = ''
REGION = 'us-east-1'
BUCKET_REGION = REGION
PYTHON_VERSION = 'python3.12'

# Configurações de credenciais temporárias
AWS_CREDENTIALS = {
    'aws_access_key_id': '',
    'aws_secret_access_key': '',
    'aws_session_token': ''
}

# Nomes dos recursos
BUCKET_NAME = ''

LAMBDA_NAMES = {
    'integracao': 'integracao_api',
    'textract': 'textract_function',
    'regex': 'regex_nota_fiscal',
    'llm': 'llm_finetune',
    'mover_imagem': 'mover-imagem-s3',
}

# Mapeamento de Layers para cada Lambda
LAMBDA_LAYERS = {
    'integracao': ['RequestToolbelt'],
    'textract': [],
    'regex': ['NLTK'],
    'llm': ['GROQ'],
    'mover_imagem': [],
}

# Mapeamento dos arquivos Lambda
LAMBDA_FILES = {
    'integracao': 'integracao_api.py',
    'textract': 'textract_function.py',
    'regex': 'regex_nota_fiscal.py',
    'llm': 'llm_finetune.py',
    'mover_imagem': 'mover_imagem_s3.py',
}

# Mapeamento de qual Lambda usa qual Role
LAMBDA_ROLES = {
    'integracao': 'RoleS3Step',
    'textract': 'RoleS3Textract',
    'regex': 'RoleS3Textract',
    'llm': 'RoleDefault',
    'mover_imagem': 'RoleS3',
}

STEP_FUNCTION_NAME = 'notas-fiscais-step-function'
API_NAME = 'NotasFiscaisAPI'

# Configuração dos Layers
LAYERS_CONFIG = {
    'RequestToolbelt': {
        'description': 'Layer contendo o Request Toolbelt para chamadas HTTP avançadas',
        'zip_file': 'request_toolbelt.zip',
        'compatible_runtimes': [PYTHON_VERSION],
        'license_info': 'Apache-2.0'
    },
    'NLTK': {
        'description': 'Layer contendo o NLTK para processamento de linguagem natural',
        'zip_file': 'nltk.zip',
        'compatible_runtimes': [PYTHON_VERSION],
        'license_info': 'Apache-2.0'
    },
    'GROQ': {
        'description': 'Layer contendo o GROQQ para processamento de linguagem natural',
        'zip_file': 'groq.zip',
        'compatible_runtimes': [PYTHON_VERSION],
        'license_info': 'Apache-2.0'
    },
}