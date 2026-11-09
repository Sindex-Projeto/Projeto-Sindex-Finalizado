import logging
import os

from database import db
from model import arquivo as arquivo_model
from services.extracao.arquivos import extrair
from services.extracao.erros import ErroExtracao, TipoSemSuporte
from services.extracao.links import extrair_de_link

registro = logging.getLogger(__name__)


# Lê o conteúdo do item e guarda o resultado (texto, situação e motivo)
def processar(arquivo, pasta_base, usar_titulo_da_pagina=False):
    titulo_da_pagina = ""
    texto = None
    status = arquivo_model.STATUS_EXTRAIDO
    observacao = None

    try:
        if arquivo.tipo == "link":
            titulo_da_pagina, texto = extrair_de_link(arquivo.url)
        else:
            caminho = os.path.join(pasta_base, str(arquivo.repositorio_id), arquivo.nome_armazenado)
            texto = extrair(caminho, arquivo.extensao)

        if not texto or not texto.strip():
            status = arquivo_model.STATUS_SEM_TEXTO
            observacao = "Nenhum texto encontrado (pode ser um documento escaneado, só com imagens)."
            texto = None
    # Resultados possíveis: sem texto, falhou ou erro inesperado
    except TipoSemSuporte as erro:
        status = arquivo_model.STATUS_SEM_TEXTO
        observacao = str(erro)
    except ErroExtracao as erro:
        status = arquivo_model.STATUS_FALHOU
        observacao = str(erro)
    except Exception:
        registro.exception("Erro inesperado ao ler o item %s", arquivo.id)
        status = arquivo_model.STATUS_FALHOU
        observacao = "Erro inesperado ao ler o conteúdo."

    arquivo.texto_extraido = texto
    arquivo.status = status
    arquivo.observacao = observacao[:255] if observacao else None

    # Link sem título digitado: usa o título da página
    if usar_titulo_da_pagina and titulo_da_pagina and status == arquivo_model.STATUS_EXTRAIDO:
        arquivo.nome = titulo_da_pagina[:255]

    db.session.commit()
    return arquivo
