from flask import request
from flask_jwt_extended import get_jwt_identity

from services.erros import ErroServico


# Lê o JSON enviado pelo front
def corpo_json():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        raise ErroServico("Envie os dados em formato JSON.")

    return dados


# Id do usuário logado
def usuario_atual_id():
    return int(get_jwt_identity())
