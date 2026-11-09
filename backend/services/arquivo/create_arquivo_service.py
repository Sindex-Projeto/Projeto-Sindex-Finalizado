import os
import uuid

from database import db
from model.arquivo import Arquivo
from services.erros import ErroServico
from services.extracao.executar import processar
from services.pasta.validar_pasta import validar_destino
from services.permissoes import exigir_papel

# Tipos de arquivo aceitos no upload
EXTENSOES_PERMITIDAS = {
    "pdf", "txt", "md", "csv", "docx",
    "png", "jpg", "jpeg", "gif",
    "mp4", "mov",
}


# Nome mostrado ao usuário (sem pastas no caminho)
def _nome_de_exibicao(nome_enviado):
    nome = os.path.basename((nome_enviado or "").replace("\\", "/")).strip()
    return nome[:255]


# Upload de arquivos
def execute(usuario_id, repositorio_id, arquivos, pasta_base, pasta_id=None):
    # Só editor ou dono envia
    exigir_papel(usuario_id, repositorio_id, "editor")
    pasta_id = validar_destino(pasta_id, repositorio_id)

    arquivos = [a for a in arquivos if a and a.filename]

    if not arquivos:
        raise ErroServico("Nenhum arquivo enviado.")

    # Cada repositório tem a sua pasta no disco
    pasta = os.path.join(pasta_base, str(repositorio_id))
    os.makedirs(pasta, exist_ok=True)

    enviados = []
    erros = []

    # Valida e salva um arquivo por vez
    for arquivo_enviado in arquivos:
        nome = _nome_de_exibicao(arquivo_enviado.filename)
        extensao = nome.rsplit(".", 1)[-1].lower() if "." in nome else ""

        if extensao not in EXTENSOES_PERMITIDAS:
            erros.append({"arquivo": nome or "(sem nome)", "erro": "Tipo de arquivo não permitido."})
            continue

        # Salva no disco com nome aleatório
        nome_armazenado = f"{uuid.uuid4().hex}.{extensao}"
        caminho = os.path.join(pasta, nome_armazenado)

        arquivo_enviado.save(caminho)

        # Registra no banco (se falhar, apaga o arquivo salvo)
        try:
            registro = Arquivo(
                tipo="arquivo",
                nome=nome,
                nome_armazenado=nome_armazenado,
                extensao=extensao,
                tamanho=os.path.getsize(caminho),
                repositorio_id=repositorio_id,
                usuario_id=usuario_id,
                pasta_id=pasta_id,
            )
            db.session.add(registro)
            db.session.commit()
        except Exception:
            db.session.rollback()
            if os.path.exists(caminho):
                os.remove(caminho)
            erros.append({"arquivo": nome, "erro": "Não foi possível salvar o arquivo."})
            continue

        # Lê o texto do arquivo
        processar(registro, pasta_base)

        enviados.append(registro)

    return enviados, erros
