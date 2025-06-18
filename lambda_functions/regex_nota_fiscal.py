import re
import json
import logging

logger = logging.getLogger()

# Padrões de regex para extração de dados
REGEX_PATTERNS = {
    "NOME_EMISSOR": r"([\w\s]+) LTDA",
    "CNPJ": r"\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
    "ENDERECO_EMISSOR": r"(AVENIDA|RUA|TRAVESSA|ALAMEDA|AV|RODOVIA)\s+[\w\s,-]+CEP\s+\d{5}-\d{3}",
    "CPF": r"\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2}",
    "DATA": r"\d{2}/\d{2}/\d{4}",
    "NUMERO_NF": r"\b(\d{6}|\d{9})\b",
    "SERIE_NF": r"SAT No\.?\s*0*(\d{3})\b",
    "VALOR": r"TOTAL R\$ :\s*([\d,.]+)",
    "FORMA_PGTO": r"\b(Pix|Dinheiro|Cartão|Crédito|Débito)\b"}

# Extrai um campo usando regex e retorna o primeiro valor encontrado ou um valor default.
def extract_field(pattern, text, default="<none>"):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else default

# Processa o texto da nota fiscal e extrai os dados na ordem correta.
def processar_nota(text):
    logger.info("🔄 Iniciando processamento da nota fiscal.")
    
    forma_pgto = extract_field(REGEX_PATTERNS["FORMA_PGTO"], text, "Outros")
    forma_pgto = "dinheiroPix" if forma_pgto.lower() in ["pix", "dinheiro"] else "outros"

    structured_data = {
        "Nome do Emissor": extract_field(REGEX_PATTERNS["NOME_EMISSOR"], text),
        "CNPJ do Emissor": extract_field(REGEX_PATTERNS["CNPJ"], text),
        "Endereço do Emissor": extract_field(REGEX_PATTERNS["ENDERECO_EMISSOR"], text),
        "CNPJ/CPF do Consumidor": extract_field(REGEX_PATTERNS["CPF"], text),
        "Data de Emissão": extract_field(REGEX_PATTERNS["DATA"], text),
        "Número da Nota Fiscal": extract_field(REGEX_PATTERNS["NUMERO_NF"], text),
        "Série da Nota Fiscal": extract_field(REGEX_PATTERNS["SERIE_NF"], text),
        "Valor Total": extract_field(REGEX_PATTERNS["VALOR"], text),
        "Forma de Pagamento": forma_pgto
    }
    logger.info(f"✅ Dados extraídos com sucesso: {structured_data}")
    return structured_data


# Função principal executada pela AWS Lambda. Recebe o evento com os dados da nota fiscal,
# processa as informações extraindo os campos relevantes e retorna os dados formatados.
def lambda_handler(event, context):
    logger.info("🔄 Recebendo evento Lambda.")
    data = event["important_data"]
    
    logger.info("🔄 Extraindo dados da nota fiscal.")
    dados_extraidos = processar_nota(data)

    important_data = "\n".join([f"{chave}: {valor}" for chave, valor in dados_extraidos.items()])

    logger.info("✅ Extração concluída com sucesso.")
    return{
        "statusCode": 200,
        "important_data": important_data,
        "file_name": event["file_name"],
        "bucket_name": event["bucket_name"],
    }