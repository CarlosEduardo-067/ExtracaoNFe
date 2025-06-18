import json
import re
import logging
from groq import Groq

logger = logging.getLogger()

def formatar_cnpj_cpf(valor):
    if len(valor) == 14:
        return f"{valor[:2]}.{valor[2:5]}.{valor[5:8]}/{valor[8:12]}-{valor[12:]}"
    elif len(valor) == 11:
        return f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"
    return valor

# Valida o formato da nota
def validar_nota_fiscal(dados, texto):
    logger.info(f"ℹ️ Validando os dados gerados pela LLM.")

    # Define todos os valores como string
    try:
        logger.info(f"ℹ️ Validando formato do jason e reformatando campos como string.")
        for chave in ["nome_emissor", "CNPJ_emissor", "endereco_emissor", "CNPJ_CPF_consumidor", "data_emissao", "numero_nota_fiscal", "serie_nota_fiscal", "valor_total", "forma_pgto"]:
            if dados[chave] is not None and not isinstance(dados[chave], str):
                dados[chave] = str(dados[chave])
    except:
        return 0

    # Captura e mantém valores mais precisos do texto original feito com NLTK
    logger.info(f"ℹ️ Capturando dados mais precisos gerados pelo NLTK.")
    linhas = texto.split('\n')
    for linha in linhas:
        if "CNPJ do Emissor" in linha:
            padrao_cnpj = r'(\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{14}\b)'
            resultado_cnpj = re.search(padrao_cnpj, linha)
            
            if resultado_cnpj:
                cnpj = resultado_cnpj.group(1)
                # Remover os caracteres especiais, mantendo apenas os números
                cnpj = re.sub(r'\D', '', cnpj)
                dados["CNPJ_emissor"] = cnpj
        
        if "CNPJ/CPF do Consumidor" in linha:
            padrao_cnpj_cpf = r'(\b\d{11}\b|\b\d{14}\b|\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{3}\.\d{3}\.\d{3}-\d{2}\b)'
            resultado_cnpj_cpf = re.search(padrao_cnpj_cpf, linha)
            
            if resultado_cnpj_cpf:
                cnpj_cpf = resultado_cnpj_cpf.group(1)
                cnpj_cpf = re.sub(r'\D', '', cnpj_cpf)
                dados["CNPJ_CPF_consumidor"] = cnpj_cpf

        if "Número da Nota Fiscal" in linha:
            padrao_num = r'(\b\d{6}|\d{9}\b)'
            resultado_num = re.search(padrao_num, linha)
            
            if resultado_num:
                dados["numero_nota_fiscal"] = resultado_num.group(1)

        if "Série da Nota Fiscal" in linha:
            padrao_serie = r'(\b\d{3}\b)'
            resultado_serie = re.search(padrao_serie, linha)
            
            if resultado_serie:
                dados["serie_nota_fiscal"] = resultado_serie.group(1)

        if "Valor Total" in linha:
            padrao_total = r'(\b\d+([,.]\d{2})?\b)'
            resultado_total = re.search(padrao_total, linha)
            
            if resultado_total:
                dados["valor_total"] = resultado_total.group(1)

    # Verifica a forma de pagamento
    if dados["forma_pgto"] not in {"dinheiropix", "outros", None}:
        logger.info(f"❌ Forma de pagamento inválida.")
        return 0
    
    # Verifica o numero 
    if dados["numero_nota_fiscal"] is not None and not re.fullmatch(r"\d{6}|\d{9}", dados["numero_nota_fiscal"]):
        logger.info(f"❌ Número da nota fiscal inválida.")
        return 0
    
    # Verifica a serie
    if dados["serie_nota_fiscal"] is not None and not re.fullmatch(r"\d{3}", dados["serie_nota_fiscal"]):
        logger.info(f"❌ Série da nota fiscal inválida.")
        return 0
    
    # Verifica o valor total, tira zeros a esquerda e corrige , para .
    if dados["valor_total"] is not None:
        if not re.fullmatch(r"\d+([,.]\d{2})?", dados["valor_total"]):
            logger.info(f"❌ Valor total inválido.")
            return 0
        dados["valor_total"] = re.sub(r'^0+(\d+)', r'\1', dados["valor_total"])
        dados["valor_total"] = dados["valor_total"].replace(",", ".")
        if not dados["valor_total"].endswith('.00'):
            dados["valor_total"] += '.00'
    
    # Verifica o CNPJ/CPF do Consumidor e formata se necessário
    if dados["CNPJ_CPF_consumidor"] is not None:
        logger.info(f"❌ CPF/CNPJ do consumidor inválido.")
        if re.fullmatch(r"\d{11}|\d{14}", dados["CNPJ_CPF_consumidor"]):
            dados["CNPJ_CPF_consumidor"] = formatar_cnpj_cpf(dados["CNPJ_CPF_consumidor"])
        elif not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", dados["CNPJ_CPF_consumidor"]):
            return 0
    
    # Verifica o CNPJ do Emissor e formata se necessário
    if dados["CNPJ_emissor"] is not None:
        if re.fullmatch(r"\d{14}", dados["CNPJ_emissor"]):
            dados["CNPJ_emissor"] = formatar_cnpj_cpf(dados["CNPJ_emissor"])
        elif not re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", dados["CNPJ_CPF_consumidor"]):
            logger.info(f"❌ CNPJ do emissor inválido.")
            return 0
        
    if dados["data_emissao"] is not None and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados["data_emissao"]):
        logger.info(f"❌ Data de emissão inválida.")
        return 0
    
    logger.info(f"✅ Validação bem sucedida.")
    return 1

# Processamento dos dados e refinamento com a LLM
def processar_nota_com_llm(texto):
    GROQ_API_KEY = "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"

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f'''
Texto da nota fiscal:

{texto}'''
    
    # Faz a chamada para a API da Groq e define a prompt
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": """
Extraia os seguintes dados de uma nota fiscal e retorne em formato JSON:
Nome do emissor, CNPJ do emissor, Endereço do emissor, CNPJ ou CPF do consumidor,
Data de emissão, Número da nota fiscal, Valor total e Forma de pagamento.
                   
Esta nota foi extraida com uma inteligencia artificial e pode conter erros, seu trabalho também é identificar esses erros
e descarta-los definindo os campos como null para estes casos.
                   
Não escreva a forma de pagamento!! Escreva seguindo o padrão:
Para Dinheiro ou PIX insira "dinheiropix". Para Cartão de Crédito, Boleto ou outros escreva "outros".
                   
Caso algum campo não seja encontrado, coloque como null. Não invente valores não especificados no texto.
Fique atento ao identificar o nome do emissor (as vezes ele pode estar em quebras de linha).
Verifique se o CNPJ ou CPF é realmente válido, caso contrário descarte e defina como null.
                   
Número da Nota Fiscal:
O número pode ter 6 ou 9 dígitos. Valores diferentes disso devem ser definidos como null.

Número de Série:
Sempre será um número de 3 dígitos. Valores diferentes disso devem ser definidos como null.
                   
SE A SERIE NÃO TIVER EXATAMENTE 3 DÍGITOS DESCARTE E DEFINA COMO NULL!!!
NÃO INVENTE VALORES!! SE ELES NÃO BATEM COM A DEFINIÇÃO DEFINA NULL!!
                   
Se a data estiver em padrão americano ajuste e se for algum valor que não faça sentido como data, defina null.

Siga o Formato de Saída JSON desejado:

{
"nome_emissor": "<nome-fornecedor>",
"CNPJ_emissor": "00.000.000/0000-00",
"endereco_emissor": "<endereco-fornecedor>",
"CNPJ_CPF_consumidor": "000.000.000-00",
"data_emissao": "00/00/0000",
"numero_nota_fiscal": "123456",
"serie_nota_fiscal": "123",
"valor_total": "0000.00",
"forma_pgto": "<dinheiropix/outros>"
}
                                      
Não escreva nada além da saída em Json. Sem explicações ou textos adicionais. Não use { } no texto de saída.
                   """},
                  {"role": "user", "content": prompt}],
        max_tokens=512
    )

    # Pega a resposta gerada pelo modelo
    resultado = response.choices[0].message.content

    # Para evitar casos onde a LLM esqueceu os parênteses
    resultado = resultado.replace("{","")
    resultado = resultado.replace("}","")
    resultado = "{" + resultado + "\n}"

    # Tenta transformar em Json se não for possível descarta a alteração da LLM
    try:
        dados_json = json.loads(resultado)
        logger.info(f"ℹ️ Tentativa da LLM:\n{resultado}")
        if not validar_nota_fiscal(dados_json, texto):
            logger.info(f"🔄 LLM iniciando nova tentativa.")
            return processar_nota_com_llm(texto)
    except json.JSONDecodeError:
        logger.info(f"❌ Erro ao formatar json.")
        logger.info(f"🔄 LLM iniciando nova tentativa.")
        return processar_nota_com_llm(texto)

    return dados_json

def lambda_handler(event, context):
    logger.info(f"ℹ️ Importando dados da Lambda NLTK.")
    file_name = event['file_name']
    bucket_name = event['bucket_name']
    nota_texto = event['important_data']
    logger.info(f"✅ Dados importados:\n{nota_texto}")

    resultado_json = processar_nota_com_llm(nota_texto)
    logger.info(f"✅ JSON FINAL:\n{resultado_json}")
    # Retorna o Json após o processo completo da LLM
    return {
        "result_json": resultado_json,
        "file_name": file_name,
        "bucket_name": bucket_name
    }
