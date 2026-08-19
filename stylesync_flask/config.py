# configuração para consumo de db mongodb, estabeler conexão (no init)

import os 
from dotenv import load_dotenv
# dotenv é uma biblioteca externa (não nativa) que permite ler um arquivo especial chamado .env —
# um arquivo de texto simples que guarda pares CHAVE=valor, geralmente informações sensíveis tipo
# senhas, tokens, strings de conexão.
load_dotenv()
# Executa a leitura do arquivo .env (que deve estar na raiz do projeto) 
# e carrega todas aquelas variáveis pra dentro do ambiente do sistema operacional,

class Config:
    MONGO_URI = os.getenv('MONGO_URI')
    # Dentro dela, os.getenv('MONGO_URI') busca o valor da variável de ambiente chamada MONGO_URI
    # e guarda esse valor como um atributo de classe.
    SECRET_KEY = os.getenv('SECRET_KEY')