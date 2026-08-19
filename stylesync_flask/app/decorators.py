# dependencia de tokenização do JWT na parte do login
from functools import wraps
# wraps é fundamental para criação de decorators bem comportados, 
# copiando os metadados da função original (como nome, docstring) para a função decorada
# Dessa forma as rotas rotas protegidas podem ser de distintas funções decorated
from flask import request, jsonify,current_app
# current_app é um proxy que aponta para a instancia da app flask tratada na request atual
import jwt

# criação da chave secreta para utilização do token jwt por meio do ".env"

# função responsável por ser o decorator
# decorator : unção especial que modifica 
# ou estende o comportamento de outra função (f) ou método sem alterar o código original
def token_required(f):
    @wraps(f)
    # função que substitui a original, com argumentos que capturam argumentos originais
    def decorated(*args,**kwargs):

        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'message':'Token malformado'})
        if not token:
            return jsonify({'message':'Token não encontrado'})

        try:
            data = jwt.decode(token, 
                              current_app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message':'Token expirado'}),401
        except jwt.InvalidTokenError:
            return jsonify({'message':'Token inválido'}),401

        return f(data,*args,**kwargs)

    return decorated