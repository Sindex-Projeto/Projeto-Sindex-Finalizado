from urllib.parse import urlparse

from database import db
from model.arquivo import Arquivo
from services.erros import ErroServico
from services.extracao.executar import processar
from services.pasta.validar_pasta import validar_destino
from services.permissoes import exigir_papel


# Adicionar link
def execute(usuario_id, repositorio_id, url, titulo=None, pasta_id=None, pasta_base=""):
    exigir_papel(usuario_id, repositorio_id, "editor")
    pasta_id = validar_destino(pasta_id, repositorio_id)

    # Valida o endereço
    if not isinstance(url, str) or not url.strip():
        raise ErroServico("Informe o endereço do link.")

    url = url.strip()

    if len(url) > 2048:
        raise ErroServico("O link é grande demais.")

    partes = urlparse(url)

    # Só aceita http e https
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ErroServico("Informe um link válido, começando com http:// ou https://.")

    if titulo is not None and not isinstance(titulo, str):
        raise ErroServico("Título inválido.")

    # Nome do link: o título digitado ou o endereço
    titulo_informado = bool((titulo or "").strip())
    nome = (titulo or "").strip() or (partes.netloc + partes.path)

    # Registra no banco
    link = Arquivo(
        tipo="link",
        nome=nome[:255],
        url=url,
        repositorio_id=repositorio_id,
        usuario_id=usuario_id,
        pasta_id=pasta_id,
    )

    db.session.add(link)
    db.session.commit()

    # Lê o texto da página
    processar(link, pasta_base, usar_titulo_da_pagina=not titulo_informado)

    return link
