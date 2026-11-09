from sqlalchemy import UniqueConstraint

from database import db, agora, para_iso
from model.usuario import Usuario

# Tipos de repositório e papéis (maior número = mais permissão)
TIPOS = ("pessoal", "corporativo")

PAPEIS = {"leitor": 1, "editor": 2, "dono": 3}


# Tabela de repositórios
class Repositorio(db.Model):
    __tablename__ = "repositorios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, default="pessoal")
    dono_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    def to_dict(self, papel=None):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "criado_em": para_iso(self.criado_em),
        }
        if papel:
            dados["papel"] = papel
        return dados


# Tabela de membros (quem participa de cada repositório e com qual papel)
class MembroRepositorio(db.Model):
    __tablename__ = "membros_repositorio"
    __table_args__ = (UniqueConstraint("usuario_id", "repositorio_id"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    repositorio_id = db.Column(
        db.Integer, db.ForeignKey("repositorios.id"), nullable=False, index=True
    )
    papel = db.Column(db.String(20), nullable=False, default="leitor")


# Consultas
def buscar_por_id(id):
    return db.session.get(Repositorio, id)


# Cria o repositório e já coloca o dono como membro
def novo(nome, tipo, dono_id):
    repositorio = Repositorio(nome=nome, tipo=tipo, dono_id=dono_id)
    db.session.add(repositorio)
    db.session.flush()

    db.session.add(
        MembroRepositorio(
            usuario_id=dono_id, repositorio_id=repositorio.id, papel="dono"
        )
    )
    db.session.flush()
    return repositorio


# Repositórios de que o usuário participa
def listar_do_usuario(usuario_id, tipo=None):
    consulta = (
        db.select(Repositorio, MembroRepositorio.papel)
        .join(MembroRepositorio, MembroRepositorio.repositorio_id == Repositorio.id)
        .where(MembroRepositorio.usuario_id == usuario_id)
    )
    if tipo:
        consulta = consulta.where(Repositorio.tipo == tipo)
    consulta = consulta.order_by(Repositorio.id)
    return db.session.execute(consulta).all()


def buscar_membro(usuario_id, repositorio_id):
    consulta = db.select(MembroRepositorio).where(
        MembroRepositorio.usuario_id == usuario_id,
        MembroRepositorio.repositorio_id == repositorio_id,
    )
    return db.session.execute(consulta).scalar_one_or_none()


def listar_membros(repositorio_id):
    consulta = (
        db.select(Usuario, MembroRepositorio.papel)
        .join(MembroRepositorio, MembroRepositorio.usuario_id == Usuario.id)
        .where(MembroRepositorio.repositorio_id == repositorio_id)
        .order_by(MembroRepositorio.id)
    )
    return db.session.execute(consulta).all()


# Adiciona o membro ou muda o papel dele
def definir_membro(usuario_id, repositorio_id, papel):
    membro = buscar_membro(usuario_id, repositorio_id)
    if membro:
        membro.papel = papel
    else:
        membro = MembroRepositorio(
            usuario_id=usuario_id, repositorio_id=repositorio_id, papel=papel
        )
        db.session.add(membro)
    db.session.flush()
    return membro
