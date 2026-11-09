from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required

from controllers.utils import corpo_json, usuario_atual_id
from services.arquivo.create_arquivo_service import execute as enviar
from services.arquivo.create_link_service import execute as criar_link
from services.arquivo.delete_arquivo_service import execute as excluir
from services.arquivo.get_arquivo_service import execute as obter_para_download
from services.arquivo.list_arquivo_service import execute as listar
from services.arquivo.reler_arquivo_service import execute as reler_conteudo
from services.arquivo.update_arquivo_service import execute as atualizar
from services.erros import ErroServico

arquivo_bp = Blueprint("arquivo", __name__)


# Pasta onde os arquivos são guardados
def _pasta_uploads():
    return current_app.config["UPLOAD_FOLDER"]


# Upload de arquivos
@arquivo_bp.route("/repositorios/<int:repositorio_id>/arquivos", methods=["POST"])
@jwt_required()
def upload(repositorio_id):
    texto_pasta = (request.form.get("pasta_id") or "").strip()

    try:
        pasta_id = int(texto_pasta) if texto_pasta else None
    except ValueError:
        raise ErroServico("Pasta inválida.")

    enviados, erros = enviar(
        usuario_atual_id(),
        repositorio_id,
        request.files.getlist("arquivos"),
        _pasta_uploads(),
        pasta_id
    )

    resposta = {
        "enviados": [a.to_dict() for a in enviados],
        "erros": erros
    }

    if not enviados:
        resposta["erro"] = "Nenhum arquivo foi aceito."
        return jsonify(resposta), 400

    return jsonify(resposta), 201


# Adicionar link
@arquivo_bp.route("/repositorios/<int:repositorio_id>/links", methods=["POST"])
@jwt_required()
def adicionar_link(repositorio_id):
    dados = corpo_json()

    link = criar_link(
        usuario_atual_id(),
        repositorio_id,
        dados.get("url"),
        dados.get("titulo"),
        dados.get("pasta_id"),
        _pasta_uploads()
    )

    return jsonify(link.to_dict()), 201


# Listar arquivos (com filtros)
@arquivo_bp.route("/repositorios/<int:repositorio_id>/arquivos", methods=["GET"])
@jwt_required()
def listar_arquivos(repositorio_id):
    # Filtros opcionais na URL: ?q=nome&categoria=3&pasta=raiz&tipo=link&status=extraido
    filtros = {
        "q": request.args.get("q"),
        "categoria": request.args.get("categoria"),
        "pasta": request.args.get("pasta"),
        "tipo": request.args.get("tipo"),
        "status": request.args.get("status"),
    }

    return jsonify(listar(usuario_atual_id(), repositorio_id, filtros)), 200


# Baixar arquivo
@arquivo_bp.route("/arquivos/<int:arquivo_id>/download", methods=["GET"])
@jwt_required()
def baixar(arquivo_id):
    arquivo, pasta = obter_para_download(usuario_atual_id(), arquivo_id, _pasta_uploads())

    return send_from_directory(
        pasta,
        arquivo.nome_armazenado,
        as_attachment=True,
        download_name=arquivo.nome
    )


# Editar arquivo (nome, categoria, pasta)
@arquivo_bp.route("/arquivos/<int:arquivo_id>", methods=["PATCH"])
@jwt_required()
def editar(arquivo_id):
    dados = corpo_json()

    arquivo = atualizar(usuario_atual_id(), arquivo_id, dados)

    return jsonify(arquivo.to_dict()), 200


# Ler o conteúdo de novo
@arquivo_bp.route("/arquivos/<int:arquivo_id>/extrair", methods=["POST"])
@jwt_required()
def reler(arquivo_id):
    arquivo = reler_conteudo(usuario_atual_id(), arquivo_id, _pasta_uploads())

    return jsonify(arquivo.to_dict()), 200


# Excluir arquivo
@arquivo_bp.route("/arquivos/<int:arquivo_id>", methods=["DELETE"])
@jwt_required()
def remover(arquivo_id):
    excluir(usuario_atual_id(), arquivo_id, _pasta_uploads())

    return jsonify({"mensagem": "Removido."}), 200
