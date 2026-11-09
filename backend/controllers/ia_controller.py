from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from controllers.utils import usuario_atual_id
from services.ia.aplicar_sugestao_service import execute as aplicar
from services.ia.busca_semantica_service import execute as buscar_por_significado
from services.ia.ignorar_sugestao_service import execute as ignorar
from services.ia.sugerir_service import execute as sugerir

ia_bp = Blueprint("ia", __name__)


# Pedir sugestão de organização
@ia_bp.route("/arquivos/<int:arquivo_id>/sugestao", methods=["POST"])
@jwt_required()
def pedir_sugestao(arquivo_id):
    return jsonify(sugerir(usuario_atual_id(), arquivo_id)), 200


# Aplicar a sugestão
@ia_bp.route("/arquivos/<int:arquivo_id>/sugestao/aplicar", methods=["POST"])
@jwt_required()
def aplicar_sugestao(arquivo_id):
    return jsonify(aplicar(usuario_atual_id(), arquivo_id)), 200


# Ignorar a sugestão
@ia_bp.route("/arquivos/<int:arquivo_id>/sugestao", methods=["DELETE"])
@jwt_required()
def ignorar_sugestao(arquivo_id):
    ignorar(usuario_atual_id(), arquivo_id)
    return jsonify({"mensagem": "Sugestão ignorada."}), 200


# Busca por significado
@ia_bp.route("/repositorios/<int:repositorio_id>/busca-semantica", methods=["GET"])
@jwt_required()
def busca_semantica(repositorio_id):
    resultado = buscar_por_significado(usuario_atual_id(), repositorio_id, request.args.get("q"))
    return jsonify(resultado), 200
