from flask import Blueprint, jsonify,request,current_app
from app.models.user import LoginPayload
from pydantic import ValidationError
from app import db
from bson import ObjectId
from app.models.products import *
from app.models.sale import Sale
from app.decorators import token_required
from datetime import datetime,timedelta,timezone
import jwt
import csv
import os
import io


# jsonify converte o dicionario em um JSON legivel para o app
# o BP guarda as rotas para serem exibidas ao botar o server pra rodar no register_blueprint no __init__
# request para pegar as informações enviadas no body via requisição na rota LoginPayload
# pasta models contém a classe de usuario pro login
# objectid converte a strig em id do Mongo

main_bp = Blueprint('main_bp',__name__)

# O sistema deve permitir que um usuário se autentique para obter um token (JWT)
@main_bp.route('/login', methods=['POST'])
def login():
    # primeiro pega a informação enviada e valida, se tiver algum erro de tipagem ou algo do genero, o devolve
    try:
        # pega a info e converte em JSON
        raw_data = request.get_json()
        # desacopla dicionario para servir de argumento nos atributos
        user_data = LoginPayload(**raw_data)

    except ValidationError as e:
        return jsonify({'message':e.errors()}), 400
    except Exception:
        return jsonify({'message':'Corpo da requisição inválido ou não é JSON'}), 500

    # se tiver os dados no formato correto, os validam pra saber se batem com um usuario (admin)
    if user_data.username == 'admin' and user_data.password == '123':
        # criação do token JWT
        token = jwt.encode(
            {
                "user_id":user_data.username,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'access_token':token}),200

    return jsonify({'message':'Credenciais inválidas!'}),401
    
    # envia a mensagem e informa qual o tipo que será exibido na resposta por meio do model_dump
    return jsonify({'message':f'Realiar login do usuário {user_data.model_dump_json()}'})

# O sistema deve permitir listagem de todos os produtos
@main_bp.route('/products',methods = ['GET'])
def get_products():
    # busca todos os documentos dentro dos products
    products_cursor = db.products.find({})
    # transforma o cursor usando o alias e exclui qualquer valor vazio, tranformando em objeto JSON
    products_list = [ProductDBModel(**product).model_dump(by_alias=True,exclude_none=True) for product in products_cursor]
        
    return jsonify(products_list)

# O sistema deve permitir a criação de um novo produto
# utilizar validação do decorator em endpoint pois só quem está logado pode realizar a ação
@main_bp.route('/products',methods=['POST'])
@token_required
def create_product(token):
    try:
        product = Product(**request.get_json())
    except ValidationError as e:
        return jsonify({'error':e.errors()})

    result = db.products.insert_one(product.model_dump())

    return jsonify({'message':'Esta é a rota de criação dos produtos',
                   "id":str(result.inserted_id) }),201


# O sistema deve permitir a visualização dos detalhes de um unico produto
@main_bp.route('/product/<string:product_id>',methods=['GET'])
def get_product_by_id(product_id):
    try:
        oid = ObjectId(product_id)
    except Exception as e:
        return jsonify({'message':f'Erro ao transformar o {product_id} em ObjectId:{e}'})
    
    product = db.products.find_one({'_id':oid})
    if product:
        product_model = ProductDBModel(**product).model_dump(by_alias=True,exclude_none=True)
        return jsonify(product_model)
    else:
        return jsonify({'error':f'Produto com o id: {product_id} - Não encontrado'})

# O sistema deve permitir a atualização de um unico produto existente
@main_bp.route('/product/<string:product_id>',methods=['PUT'])
@token_required
def update_product(token, product_id):
    try:
        oid = ObjectId(product_id)
        update_data = UpdateProduct(**request.get_json())
    except ValidationError as e:
        return jsonify({'error':e.errors()})

    update_result = db.products.update_one(
        {"_id":oid},
        {"$set":update_data.model_dump(exclude_unset=True)}
    )

    if update_result.matched_count == 0:
        return jsonify({'error':'Produto não encontrado'}),404

    updated_product = db.products.find_one({"_id":oid})
    return jsonify(ProductDBModel(**updated_product).model_dump(by_alias=True,exclude=None))

# O sistema deve permitir a deleção de um unico produto existente
@main_bp.route('/product/<string:product_id>',methods=['DELETE'])
@token_required
def delete_product(token, product_id):
    try:
        oid = ObjectId(product_id)
    except Exception:
        return jsonify({'error':'id do produto inválido'}),400

    delete_product = db.products.delete_one({"_id":oid})

    if delete_product.deleted_count == 0:
        return jsonify({'error':'Produto não foi encontrado'}),404

    return "", 204

# O sistema deve permitir a importação de vendas através de um arquivo
@main_bp.route('/sales/upload',methods=['POST'])
@token_required
def upload_sales(token):
    if 'file' not in request.files:
        return jsonify({'error':'Nenhum arquivo foi enviado'}),400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error':'Nenhum arquivo foi selecionado'}),400

    if file and file.name.endswith('.csv'):
        csv_stream = io.StringIO(file.stream.read().decode('UTF-8'),newline=None)
        # trata cada linha do csv como dicionario pra pegar as chaves do dic
        csv_reader = csv.DictReader(csv_stream)

        sales_to_insert = []
        error = []

        for row_num,row in enumerate(csv_reader,1):
            try:
                sale_data = Sale(**row)

                sales_to_insert.append(sale_data.model_dump())
            except ValidationError as e:
                error.append(f'Linha {row_num} com dados inválidos')
            except Exception as e:
                error.append(f'Linha {row_num} com erro inesperado nos dados')

        if sales_to_insert:
            try:
                db.sale.insert_many(sales_to_insert)
            except Exception as e:
                return jsonify({'error':f'{e}'})
        return jsonify({
            "message":"Upload realizado com sucesso",
            "vendas importadas":len(sales_to_insert),
            "erros encontrados":error
        }),200

    return jsonify({'message':'Esta é a rota de arquivo de vendas'})

@main_bp.route('/')
def index():
    return jsonify({'message':'Bem vindo ao StyleSync!'})
