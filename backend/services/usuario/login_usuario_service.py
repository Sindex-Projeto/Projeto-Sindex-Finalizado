from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from model import repositorio as repositorio_model
from model import usuario as usuario_model
from services.erros import ErroServico
from services.usuario import limite_login

# Senha de mentira, para o tempo de resposta não revelar se o e-mail existe
HASH_FALSO = generate_password_hash("sindex-senha-falsa")


# Login
def execute(email, senha, metodo, ip="desconhecido"):
    # Valida os dados enviados
    metodo = metodo or "pessoal"

    if metodo not in repositorio_model.TIPOS:
        raise ErroServico("Método de login inválido.")

    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
        raise ErroServico("Informe e-mail e senha.")

    email = email.strip().lower()

    # Bloqueia se errou a senha muitas vezes
    espera = limite_login.segundos_de_espera(email, ip)

    if espera:
        minutos = (espera + 59) // 60
        raise ErroServico(
            f"Muitas tentativas de login. Tente novamente em {minutos} minuto(s).", 429
        )

    # Confere e-mail e senha (mesma mensagem de erro nos dois casos)
    usuario = usuario_model.buscar_por_email(email)

    hash_conferido = usuario.senha_hash if usuario else HASH_FALSO
    senha_correta = check_password_hash(hash_conferido, senha)

    if usuario is None or not senha_correta:
        limite_login.registrar_falha(email, ip)

        raise ErroServico("E-mail ou senha incorretos.", 401)

    limite_login.limpar_conta(email, ip)

    # Repositórios do modo escolhido (pessoal ou corporativo)
    repositorios = repositorio_model.listar_do_usuario(usuario.id, metodo)

    if not repositorios:
        raise ErroServico(
            "Você ainda não participa de nenhum repositório corporativo.", 403
        )

    # Devolve o token de acesso
    return {
        "token": create_access_token(identity=str(usuario.id)),
        "usuario": usuario.to_dict(),
        "metodo": metodo,
        "repositorios": [repo.to_dict(papel) for repo, papel in repositorios],
    }
