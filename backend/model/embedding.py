from database import db, agora


# Tabela com o vetor de significado de cada arquivo (busca por significado)
class EmbeddingArquivo(db.Model):
    __tablename__ = "embeddings_arquivo"

    arquivo_id = db.Column(
        db.Integer, db.ForeignKey("arquivos.id", ondelete="CASCADE"), primary_key=True
    )
    modelo = db.Column(db.String(100), nullable=False)
    vetor = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)


# Consultas
def buscar(arquivo_id):
    return db.session.get(EmbeddingArquivo, arquivo_id)


# Guarda (ou troca) o vetor de um arquivo
def salvar(arquivo_id, modelo, vetor_texto):
    existente = buscar(arquivo_id)

    if existente:
        existente.modelo = modelo
        existente.vetor = vetor_texto
        existente.criado_em = agora()
    else:
        db.session.add(EmbeddingArquivo(arquivo_id=arquivo_id, modelo=modelo, vetor=vetor_texto))

    db.session.commit()
