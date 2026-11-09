from database import db, agora, para_iso


# Tabela de sugestões da IA (uma por arquivo)
class SugestaoIA(db.Model):
    __tablename__ = "sugestoes_ia"

    id = db.Column(db.Integer, primary_key=True)
    arquivo_id = db.Column(
        db.Integer,
        db.ForeignKey("arquivos.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Nome da categoria e caminho da pasta ("A / B"), podem ser novos
    categoria = db.Column(db.String(100))
    pasta = db.Column(db.String(900))
    motivo = db.Column(db.String(240))
    modelo = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    def to_dict(self):
        return {
            "arquivo_id": self.arquivo_id,
            "categoria": self.categoria,
            "pasta": self.pasta,
            "motivo": self.motivo,
            "criado_em": para_iso(self.criado_em),
        }


# Consultas
def buscar_do_arquivo(arquivo_id):
    consulta = db.select(SugestaoIA).where(SugestaoIA.arquivo_id == arquivo_id)
    return db.session.execute(consulta).scalar_one_or_none()
