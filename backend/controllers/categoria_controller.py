from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from controllers.utils import corpo_json, usuario_atual_id
from services.categoria.create_categoria_service import execute as criar
from services.categoria.delete_categoria_service import execute as excluir
from services.categoria.list_categoria_service import execute as listar

categoria_bp = Blueprint("categoria", __name__)


# Listar categorias
@categoria_bp.route("/repositorios/<int:repositorio_id>/categorias", methods=["GET"])
@jwt_required()
def listar_categorias(repositorio_id):
    lista = [c.to_dict() for c in listar(usuario_atual_id(), repositorio_id)]

    return jsonify(lista), 200


# Criar categoria
@categoria_bp.route("/repositorios/<int:repositorio_id>/categorias", methods=["POST"])
@jwt_required()
def cadastrar(repositorio_id):
    dados = corpo_json()

    categoria = criar(
        usuario_atual_id(),
        repositorio_id,
        dados.get("nome"),
        dados.get("descricao")
    )

    return jsonify(categoria.to_dict()), 201


# Apagar categoria
@categoria_bp.route("/categorias/<int:categoria_id>", methods=["DELETE"])
@jwt_required()
def remover(categoria_id):
    excluir(usuario_atual_id(), categoria_id)

    return jsonify({"mensagem": "Categoria removida."}), 200
