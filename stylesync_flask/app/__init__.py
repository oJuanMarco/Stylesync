from flask import Flask
from pymongo import MongoClient

db=None

def create_app():
    app = Flask(__name__)
    # pega os atributos da classe Config no arquivo config.py e adota como configuração da app
    app.config.from_object('config.Config')
    #variavel de escopo global
    global db
    
    try:
        # abre uma conexão com o MongoDB, usando a URI de conexão que veio lá do config.Config
        client = MongoClient(app.config['MONGO_URI'])
        # método que olha pra dentro da própria URI de conexão e extrai qual banco foi especificado ali.
        db = client.get_default_database()
    except Exception as e:
        print(f'Erro ao realizar a conexão com db: {e}')
        
    from .routes.main import main_bp
    app.register_blueprint(main_bp)
    
    return app