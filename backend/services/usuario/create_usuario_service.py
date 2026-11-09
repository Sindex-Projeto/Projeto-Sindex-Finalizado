import re

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from database import db
from model import repositorio as repositorio_model
from model import usuario as usuario_model
from services.erros import ErroServico

# Formato aceito para e-mail
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# Cadastro de usuário
def execute(nome, email, senha):
    if not all(isinstance(valor, str) for valor in (nome, email, senha)):
        raise ErroServico("Preencha todos os campos.")

    # Valida os campos
    nome = nome.strip()
    email = email.strip().lower()

    if not nome or not email or not senha:
        raise ErroServico("Preencha todos os campos.")

    if len(nome) > 100:
        raise ErroServico("O nome pode ter no máximo 100 caracteres.")

    if len(email) > 120 or not EMAIL_REGEX.match(email):
        raise ErroServico("E-mail inválido.")

    if len(senha) < 8:
        raise ErroServico("A senha deve ter pelo menos 8 caracteres.")

    if len(senha) > 128:
        raise ErroServico("A senha pode ter no máximo 128 caracteres.")

    if usuario_model.buscar_por_email(email):
        raise ErroServico("E-mail já cadastrado.", 409)

    # Salva com a senha criptografada e cria o repositório pessoal
    try:
        novo = usuario_model.criar(nome, email, generate_password_hash(senha))
        repositorio_model.novo("Meu repositório", "pessoal", novo.id)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ErroServico("E-mail já cadastrado.", 409)

    return novo
