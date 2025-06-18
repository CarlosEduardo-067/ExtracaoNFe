# ExtracaoNFe

<img src="https://img.shields.io/badge/Status-Desenvolvimento-blue"/>

---

## Descrição

Este projeto consiste em uma API REST desenvolvida em Python para processar imagens de notas fiscais eletrônicas em formato simplificado. A API recebe a imagem via requisição POST, armazena no Amazon S3 e utiliza o Amazon Textract para extrair os dados. Os elementos da nota são refinados com NLP (Spacy ou NLTK) e uma LLM para formatação estruturada em JSON. Além disso, as notas são organizadas no S3 com base na forma de pagamento, e os logs do processo são armazenados no CloudWatch.

---

## Desenvolvimento

### Divisão de Tarefas

- API: [Leon Rabello](#leon-rabello)
- Textract: [Carlos Eduardo](#carlos-eduardo-dos-santos)
- Spacy: [Felipe Rand](#felipe-rand)
- LLMs: [Rafael Eich](#rafael-eich-fernandes)

### Etapas

1. Desenvolvimento da API para armazenar as notas na S3 e testes.
2. Testes na API para rotas e redirecionamentos das imagens na S3.
3. Implementação da Lambda de leitura da imagem com Textract.
4. Implementação da Lambda para refinamento com NLTK e Regex.
5. Implementação da Lambda da LLM para refinamento final e retorno em JSON.
6. Criação da Layer para o Ambiente AWS.
7. Ajustes do Ambiente AWS e testes finais.

---

## Dificuldades Encontradas

- Fazer o upload da imagem para a bucket S3 mantendo a integridade do arquivo.
- Compreensão e uso do NLTK.
- Como fazer a extração dos dados com o textract.

---

## Funcionalidades

- Leitura de uma nota fiscal e devolução dos dados em formato JSON.

- Classificação e armazenamento das notas na bucket S3 classificadas pelo método de pagamento em *Dinheiro* ou *Outros*.

---

## Como Utilizar o Sistema

### 1. Clone o repositório:

```bash
git clone https://github.com/CarlosEduardo-067/ExtracaoNFe.git
```

### 2. Acesse o diretório do projeto:

```bash
cd ExtracaoNFe/
```

### 3. Alterar credenciais no arquivo settings:

- **settings.py**: Abra em um editor de texto e altere as credencias.

### 4. Rodar o deploy:

```bash
python deploy.py
```

---

## Estrutura do projeto

```bash
/projeto-notaFiscal
│
├── /config                             # Configurações AWS
│    └── settings.py
│
├── /dataset                            # Notas fiscais para testes
│    └── NFs.zip
│
├── /infrastructure                     # Funções para criação da infraestrutura
│    ├── api_gateway.py
│    ├── iam.py
│    ├── lambdas.py
│    ├── layers.py
│    ├── s3.py
│    └── step_function.py
│
├── /lambda_functions                   # Funções lambdas
│    ├── integracao.py
│    ├── llm.py
│    ├── mover_imagem.py
│    ├── regex_nota_fiscal.py
│    └── textract_function.py
│
├── /layers                            # Layers para importação de bibliotecas
│    ├── groq.zip
│    ├── nltk.zip
│    └── request_toolbelt.zip               
│
├── README.md                           # Documentação do projeto
├── deploy.py                           # Script de deploy na AWS
└── .gitignore                          # Arquivos a serem ignorados no repositório Git
```

---

## Autores

### Leon Rabello

Contato: _lr.dale2001@gmail.com_

- [GitHub](https://github.com/LeonDale2001)
- [LinkedIn](https://www.linkedin.com/in/leon-rabello/)

### Carlos Eduardo dos Santos

Contato: _carloseduardodossantosvital@gmail.com_

- [GitHub](https://github.com/CarlosEduardo-067)
- [LinkedIn](https://www.linkedin.com/in/carlos-eduardo-dos-santos-vital-9335612b1/)

### Felipe Rand

Contato: _felipe.souza.pb@compasso.com.br_

- [GitHub](https://github.com/liperand)
- [LinkedIn](https://www.linkedin.com/in/felipe-rand-47312431b/)

### Rafael Eich Fernandes

Contato: _rrafael.fernandes@gmail.com_

- [GitHub](https://github.com/eichfernandes)
- [LinkedIn](https://www.linkedin.com/in/rafael-eich-fernandes-521623232)
