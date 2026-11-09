import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import RequestEntityTooLarge

from database import db
from routes.routes import registrar_rotas
from services.erros import ErroServico

from model import arquivo, categoria, embedding, pasta, repositorio, sugestao, usuario

# Configuração do app
load_dotenv()

app = Flask(__name__)

# Quais sites podem usar a API (CORS)
origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
CORS(app, origins=origens or "*")


# Banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///sindex.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Pasta e tamanho máximo dos uploads
app.config["UPLOAD_FOLDER"] = os.path.abspath(
    os.getenv("UPLOAD_FOLDER") or os.path.join(app.root_path, "uploads")
)

app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

# Chave do login (JWT)
chave_jwt = os.getenv("JWT_SECRET_KEY")

if not chave_jwt:
    chave_jwt = secrets.token_hex(32)
    print("AVISO: defina JWT_SECRET_KEY no arquivo .env (veja .env.example).")

app.config["JWT_SECRET_KEY"] = chave_jwt
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)


# Inicia banco e login
db.init_app(app)
jwt = JWTManager(app)


# Erros devolvidos como JSON
@app.errorhandler(ErroServico)
def tratar_erro_servico(erro):
    return jsonify({"erro": erro.mensagem}), erro.status


@app.errorhandler(RequestEntityTooLarge)
def tratar_arquivo_grande(_erro):
    limite = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
    return jsonify({"erro": f"O envio passou do limite de {limite} MB."}), 413


@jwt.unauthorized_loader
def token_ausente(_motivo):
    return jsonify({"erro": "Faça login para continuar."}), 401


@jwt.invalid_token_loader
def token_invalido(_motivo):
    return jsonify({"erro": "Sessão inválida. Entre novamente."}), 401


@jwt.expired_token_loader
def token_expirado(_cabecalho, _dados):
    return jsonify({"erro": "Sessão expirada. Entre novamente."}), 401


# Rotas da API
registrar_rotas(app)


@app.route("/")
def inicio():
    return jsonify({"mensagem": "API Sindex funcionando!"})


# Cria as tabelas do banco
with app.app_context():
    db.create_all()


# Inicia o servidor
if __name__ == "__main__":
    app.run(debug=True, port=5000)
