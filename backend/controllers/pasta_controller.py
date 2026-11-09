from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from controllers.utils import corpo_json, usuario_atual_id
from services.pasta.create_pasta_service import execute as criar
from services.pasta.delete_pasta_service import execute as excluir
from services.pasta.list_pasta_service import execute as listar
from services.pasta.update_pasta_service import execute as atualizar

pasta_bp = Blueprint("pasta", __name__)


# Listar pastas
@pasta_bp.route("/repositorios/<int:repositorio_id>/pastas", methods=["GET"])
@jwt_required()
def listar_pastas(repositorio_id):
    lista = [p.to_dict() for p in listar(usuario_atual_id(), repositorio_id)]

    return jsonify(lista), 200


# Criar pasta
@pasta_bp.route("/repositorios/<int:repositorio_id>/pastas", methods=["POST"])
@jwt_required()
def cadastrar(repositorio_id):
    dados = corpo_json()

    pasta = criar(
        usuario_atual_id(),
        repositorio_id,
        dados.get("nome"),
        dados.get("pasta_pai_id")
    )

    return jsonify(pasta.to_dict()), 201


# Renomear ou mover pasta
@pasta_bp.route("/pastas/<int:pasta_id>", methods=["PATCH"])
@jwt_required()
def editar(pasta_id):
    dados = corpo_json()

    return jsonify(atualizar(usuario_atual_id(), pasta_id, dados).to_dict()), 200


# Apagar pasta
@pasta_bp.route("/pastas/<int:pasta_id>", methods=["DELETE"])
@jwt_required()
def remover(pasta_id):
    excluir(usuario_atual_id(), pasta_id)

    return jsonify({"mensagem": "Pasta removida. O conteúdo dela subiu um nível."}), 200
