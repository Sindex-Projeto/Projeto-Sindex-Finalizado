from sqlalchemy import UniqueConstraint

from database import db


# Tabela de categorias
class Categoria(db.Model):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("repositorio_id", "nome"),)

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    repositorio_id = db.Column(
        db.Integer, db.ForeignKey("repositorios.id"), nullable=False, index=True
    )

    # Dados enviados ao front
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "repositorio_id": self.repositorio_id,
        }


# Consultas
def buscar_por_id(id):
    return db.session.get(Categoria, id)


def buscar_por_nome(repositorio_id, nome):
    consulta = db.select(Categoria).where(
        Categoria.repositorio_id == repositorio_id, Categoria.nome == nome
    )
    return db.session.execute(consulta).scalar_one_or_none()


def listar_do_repositorio(repositorio_id):
    consulta = (
        db.select(Categoria)
        .where(Categoria.repositorio_id == repositorio_id)
        .order_by(Categoria.nome)
    )
    return db.session.execute(consulta).scalars().all()
