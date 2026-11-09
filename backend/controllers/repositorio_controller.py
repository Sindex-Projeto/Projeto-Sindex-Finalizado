from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from controllers.utils import corpo_json, usuario_atual_id
from services.repositorio.add_membro_service import execute as adicionar_membro
from services.repositorio.create_repositorio_service import execute as criar
from services.repositorio.list_membros_service import execute as listar_membros
from services.repositorio.list_repositorio_service import execute as listar
from services.repositorio.remove_membro_service import execute as remover_membro

repositorio_bp = Blueprint("repositorio", __name__)


# Listar repositórios
@repositorio_bp.route("/repositorios", methods=["GET"])
@jwt_required()
def listar_repositorios():
    tipo = request.args.get("tipo")

    return jsonify(listar(usuario_atual_id(), tipo)), 200


# Criar repositório
@repositorio_bp.route("/repositorios", methods=["POST"])
@jwt_required()
def cadastrar():
    dados = corpo_json()

    return jsonify(criar(usuario_atual_id(), dados.get("nome"))), 201


# Membros: listar
@repositorio_bp.route("/repositorios/<int:repositorio_id>/membros", methods=["GET"])
@jwt_required()
def listar_dos_membros(repositorio_id):
    return jsonify(listar_membros(usuario_atual_id(), repositorio_id)), 200


# Membros: remover
@repositorio_bp.route(
    "/repositorios/<int:repositorio_id>/membros/<int:alvo_id>", methods=["DELETE"]
)
@jwt_required()
def tirar_membro(repositorio_id, alvo_id):
    remover_membro(usuario_atual_id(), repositorio_id, alvo_id)

    return jsonify({"mensagem": "Membro removido."}), 200


# Membros: convidar
@repositorio_bp.route("/repositorios/<int:repositorio_id>/membros", methods=["POST"])
@jwt_required()
def novo_membro(repositorio_id):
    dados = corpo_json()

    resultado = adicionar_membro(
        usuario_atual_id(),
        repositorio_id,
        dados.get("email"),
        dados.get("papel")
    )

    return jsonify(resultado), 200
