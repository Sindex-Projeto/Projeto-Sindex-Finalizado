from database import db, agora, para_iso


# Tabela de pastas
class Pasta(db.Model):
    __tablename__ = "pastas"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)

    # Pasta de dentro da qual esta sai (vazio = raiz)
    pasta_pai_id = db.Column(db.Integer, db.ForeignKey("pastas.id"))

    repositorio_id = db.Column(
        db.Integer, db.ForeignKey("repositorios.id"), nullable=False, index=True
    )
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    # Dados enviados ao front
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "pasta_pai_id": self.pasta_pai_id,
            "repositorio_id": self.repositorio_id,
            "criado_em": para_iso(self.criado_em),
        }


# Consultas
def buscar_por_id(id):
    return db.session.get(Pasta, id)


def listar_do_repositorio(repositorio_id):
    consulta = (
        db.select(Pasta)
        .where(Pasta.repositorio_id == repositorio_id)
        .order_by(Pasta.nome)
    )
    return db.session.execute(consulta).scalars().all()
