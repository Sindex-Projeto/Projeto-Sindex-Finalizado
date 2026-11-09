from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from controllers.utils import corpo_json, usuario_atual_id
from services.usuario.config_usuario_service import execute as atualizar_config
from services.usuario.create_usuario_service import execute as criar
from services.usuario.get_usuario_service import execute as obter
from services.usuario.login_usuario_service import execute as login_usuario

usuario_bp = Blueprint("usuario", __name__)


# Cadastro
@usuario_bp.route("/usuarios", methods=["POST"])
def cadastrar():
    dados = corpo_json()

    usuario = criar(dados.get("nome"), dados.get("email"), dados.get("senha"))

    return jsonify({
        "mensagem": "Usuário cadastrado com sucesso!",
        "usuario": usuario.to_dict()
    }), 201


# Login
@usuario_bp.route("/usuarios/login", methods=["POST"])
def login():
    dados = corpo_json()

    resultado = login_usuario(
        dados.get("email"),
        dados.get("senha"),
        dados.get("metodo"),
        request.remote_addr or "desconhecido"
    )

    return jsonify(resultado), 200


# Dados do usuário logado
@usuario_bp.route("/usuarios/me", methods=["GET"])
@jwt_required()
def meus_dados():
    return jsonify(obter(usuario_atual_id()).to_dict()), 200


# Configurações (IA, tema, idioma)
@usuario_bp.route("/usuarios/me/config", methods=["PATCH"])
@jwt_required()
def alterar_config():
    usuario = atualizar_config(usuario_atual_id(), corpo_json())
    return jsonify(usuario.config()), 200
