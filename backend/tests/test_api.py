import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

# Configuração de teste (banco em memória e uploads numa pasta temporária)
PASTA_UPLOADS = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_FOLDER"] = PASTA_UPLOADS
os.environ["JWT_SECRET_KEY"] = "chave-de-teste-bem-longa-0123456789-0123456789"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports do projeto (depois da configuração acima)
from app import app
from database import db
from model.arquivo import Arquivo
from model.sugestao import SugestaoIA
from model.usuario import Usuario
from services.erros import ErroServico
from services.extracao.links import ErroLink
from services.usuario import limite_login

SENHA = "senha-forte-123"


# Base dos testes: banco limpo a cada teste e funções de apoio
class ApiTestCase(unittest.TestCase):
    def setUp(self):
        limite_login.reiniciar()

        leitor_falso = mock.patch(
            "services.extracao.executar.extrair_de_link",
            return_value=("Página de teste", "conteúdo da página"),
        )
        self.leitor_de_links = leitor_falso.start()
        self.addCleanup(leitor_falso.stop)

        shutil.rmtree(PASTA_UPLOADS, ignore_errors=True)
        os.makedirs(PASTA_UPLOADS, exist_ok=True)

        with app.app_context():
            db.drop_all()
            db.create_all()
        self.c = app.test_client()


    # Funções de apoio
    def cadastrar(self, email, nome="Teste", senha=SENHA):
        return self.c.post("/api/usuarios", json={"nome": nome, "email": email, "senha": senha})

    def entrar(self, email, metodo="pessoal", senha=SENHA):
        return self.c.post("/api/usuarios/login", json={"email": email, "senha": senha, "metodo": metodo})

    def criar_usuario_logado(self, email):
        self.assertEqual(self.cadastrar(email).status_code, 201)
        dados = self.entrar(email).get_json()
        cabecalhos = {"Authorization": f"Bearer {dados['token']}"}
        return cabecalhos, dados["repositorios"][0]["id"]

    def enviar(self, cabecalhos, repo_id, arquivos, pasta_id=None):
        dados = {"arquivos": arquivos}
        if pasta_id is not None:
            dados["pasta_id"] = str(pasta_id)

        return self.c.post(
            f"/api/repositorios/{repo_id}/arquivos",
            data=dados,
            headers=cabecalhos,
            content_type="multipart/form-data",
        )

    def nova_pasta(self, cabecalhos, repo_id, nome, pai=None):
        return self.c.post(
            f"/api/repositorios/{repo_id}/pastas",
            json={"nome": nome, "pasta_pai_id": pai},
            headers=cabecalhos,
        )

    def banco(self, arquivo_id):
        with app.app_context():
            a = db.session.get(Arquivo, arquivo_id)
            return {"status": a.status, "observacao": a.observacao, "texto": a.texto_extraido, "nome": a.nome}


# Cadastro e login
class TestUsuarios(ApiTestCase):
    def test_cadastro_cria_usuario_e_repositorio_pessoal(self):
        resposta = self.cadastrar("ana@exemplo.com")
        self.assertEqual(resposta.status_code, 201)

        dados = self.entrar("ana@exemplo.com").get_json()
        self.assertEqual(len(dados["repositorios"]), 1)
        self.assertEqual(dados["repositorios"][0]["tipo"], "pessoal")
        self.assertEqual(dados["repositorios"][0]["papel"], "dono")

    def test_senha_nao_e_guardada_em_texto_puro(self):
        self.cadastrar("ana@exemplo.com")

        with app.app_context():
            usuario = db.session.execute(db.select(Usuario)).scalar_one()
            self.assertNotEqual(usuario.senha_hash, SENHA)
            self.assertNotIn(SENHA, usuario.senha_hash)

    def test_email_repetido_da_409(self):
        self.cadastrar("ana@exemplo.com")
        self.assertEqual(self.cadastrar("ANA@exemplo.com").status_code, 409)

    def test_validacoes_do_cadastro(self):
        self.assertEqual(self.cadastrar("sem-arroba").status_code, 400)
        self.assertEqual(self.cadastrar("a@b.com", senha="curta").status_code, 400)
        self.assertEqual(self.cadastrar("a@b.com", nome="  ").status_code, 400)

    def test_login_com_senha_errada_da_401(self):
        self.cadastrar("ana@exemplo.com")
        self.assertEqual(self.entrar("ana@exemplo.com", senha="errada-errada").status_code, 401)
        self.assertEqual(self.entrar("naoexiste@exemplo.com").status_code, 401)

    def test_limite_de_tentativas_de_login(self):
        self.cadastrar("ana@exemplo.com")

        for _ in range(limite_login.MAX_FALHAS_POR_CONTA):
            self.assertEqual(self.entrar("ana@exemplo.com", senha="errada-errada").status_code, 401)

        bloqueado = self.entrar("ana@exemplo.com")
        self.assertEqual(bloqueado.status_code, 429)
        self.assertIn("Muitas tentativas", bloqueado.get_json()["erro"])

        self.cadastrar("bia@exemplo.com")
        self.assertEqual(self.entrar("bia@exemplo.com").status_code, 200)

    def test_login_certo_zera_a_contagem_de_falhas(self):
        self.cadastrar("ana@exemplo.com")

        for _ in range(limite_login.MAX_FALHAS_POR_CONTA - 1):
            self.entrar("ana@exemplo.com", senha="errada-errada")

        self.assertEqual(self.entrar("ana@exemplo.com").status_code, 200)

        for _ in range(limite_login.MAX_FALHAS_POR_CONTA - 1):
            self.assertEqual(self.entrar("ana@exemplo.com", senha="errada-errada").status_code, 401)

    def test_login_corporativo_sem_repositorio_da_403(self):
        self.cadastrar("ana@exemplo.com")
        self.assertEqual(self.entrar("ana@exemplo.com", metodo="corporativo").status_code, 403)

    def test_rotas_protegidas_exigem_token(self):
        self.assertEqual(self.c.get("/api/repositorios").status_code, 401)
        self.assertEqual(self.c.get("/api/usuarios/me").status_code, 401)
        self.assertEqual(self.c.delete("/api/arquivos/1").status_code, 401)


# Configurações (IA, tema, idioma)
class TestConfiguracoes(ApiTestCase):
    def test_padrao_e_alteracao_persistem(self):
        cab, _ = self.criar_usuario_logado("ana@exemplo.com")

        padrao = self.c.get("/api/usuarios/me", headers=cab).get_json()["config"]
        self.assertEqual(padrao, {"ia_ativa": True, "tema": "escuro", "idioma": "pt-BR"})

        resposta = self.c.patch("/api/usuarios/me/config", headers=cab,
                                json={"ia_ativa": False, "tema": "claro", "idioma": "en"})
        self.assertEqual(resposta.status_code, 200)

        salvo = self.c.get("/api/usuarios/me", headers=cab).get_json()["config"]
        self.assertEqual(salvo, {"ia_ativa": False, "tema": "claro", "idioma": "en"})

        dados = self.entrar("ana@exemplo.com").get_json()
        self.assertEqual(dados["usuario"]["config"]["tema"], "claro")

    def test_envio_parcial_muda_so_o_que_veio(self):
        cab, _ = self.criar_usuario_logado("ana@exemplo.com")
        self.c.patch("/api/usuarios/me/config", headers=cab, json={"tema": "claro"})
        config = self.c.get("/api/usuarios/me", headers=cab).get_json()["config"]
        self.assertEqual(config, {"ia_ativa": True, "tema": "claro", "idioma": "pt-BR"})

    def test_valores_invalidos_sao_recusados(self):
        cab, _ = self.criar_usuario_logado("ana@exemplo.com")
        for corpo in ({"tema": "roxo"}, {"idioma": "fr"}, {"ia_ativa": "sim"}, {"ia_ativa": 1}):
            resposta = self.c.patch("/api/usuarios/me/config", headers=cab, json=corpo)
            self.assertEqual(resposta.status_code, 400, corpo)

    def test_exige_login_e_cada_um_tem_a_sua(self):
        self.assertEqual(self.c.patch("/api/usuarios/me/config", json={"tema": "claro"}).status_code, 401)

        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")
        self.c.patch("/api/usuarios/me/config", headers=cab_ana, json={"tema": "claro"})
        self.assertEqual(self.c.get("/api/usuarios/me", headers=cab_bia).get_json()["config"]["tema"], "escuro")


# Upload, download e exclusão de arquivos e links
class TestArquivos(ApiTestCase):
    def test_upload_listagem_download_e_exclusao(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [(io.BytesIO(b"conteudo da nota"), "nota.txt")])
        self.assertEqual(resposta.status_code, 201)
        arquivo = resposta.get_json()["enviados"][0]
        self.assertEqual(arquivo["nome"], "nota.txt")
        self.assertEqual(arquivo["tamanho"], len(b"conteudo da nota"))
        self.assertEqual(arquivo["status"], "extraido")

        lista = self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json()
        self.assertEqual([a["id"] for a in lista], [arquivo["id"]])

        baixado = self.c.get(f"/api/arquivos/{arquivo['id']}/download", headers=cab)
        self.assertEqual(baixado.status_code, 200)
        self.assertEqual(baixado.data, b"conteudo da nota")
        baixado.close()

        pasta = os.path.join(PASTA_UPLOADS, str(repo))
        self.assertEqual(len(os.listdir(pasta)), 1)

        self.assertEqual(self.c.delete(f"/api/arquivos/{arquivo['id']}", headers=cab).status_code, 200)
        self.assertEqual(os.listdir(pasta), [])
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json(), [])

    def test_tipo_nao_permitido_e_rejeitado(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [(io.BytesIO(b"MZ"), "virus.exe")])
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erros"][0]["arquivo"], "virus.exe")

    def test_envio_misto_aceita_so_os_validos(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [
            (io.BytesIO(b"ok"), "a.txt"),
            (io.BytesIO(b"no"), "b.exe"),
        ])
        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(len(corpo["enviados"]), 1)
        self.assertEqual(len(corpo["erros"]), 1)

    def test_nome_com_caminho_nao_escapa_da_pasta(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [(io.BytesIO(b"x"), "../../fora.txt")])
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["enviados"][0]["nome"], "fora.txt")

        pasta = os.path.join(PASTA_UPLOADS, str(repo))
        self.assertEqual(len(os.listdir(pasta)), 1)
        self.assertFalse(os.path.exists(os.path.join(PASTA_UPLOADS, "..", "fora.txt")))

    def test_usuario_nao_ve_repositorio_de_outro(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        enviado = self.enviar(cab_ana, repo_ana, [(io.BytesIO(b"segredo"), "s.txt")]).get_json()["enviados"][0]

        self.assertEqual(self.c.get(f"/api/repositorios/{repo_ana}/arquivos", headers=cab_bia).status_code, 404)
        self.assertEqual(self.enviar(cab_bia, repo_ana, [(io.BytesIO(b"x"), "x.txt")]).status_code, 404)
        self.assertEqual(self.c.get(f"/api/arquivos/{enviado['id']}/download", headers=cab_bia).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/arquivos/{enviado['id']}", headers=cab_bia).status_code, 404)

    def test_links(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        url = f"/api/repositorios/{repo}/links"

        self.assertEqual(self.c.post(url, json={"url": "javascript:alert(1)"}, headers=cab).status_code, 400)
        self.assertEqual(self.c.post(url, json={"url": "nao é link"}, headers=cab).status_code, 400)

        ok = self.c.post(url, json={"url": "https://exemplo.com/artigo", "titulo": "Artigo"}, headers=cab)
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(ok.get_json()["tipo"], "link")
        self.assertEqual(ok.get_json()["nome"], "Artigo")

        baixar = self.c.get(f"/api/arquivos/{ok.get_json()['id']}/download", headers=cab)
        self.assertEqual(baixar.status_code, 400)


# Categorias
class TestCategorias(ApiTestCase):
    def test_criar_mover_e_apagar_categoria(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar(cab, repo, [(io.BytesIO(b"x"), "a.txt")]).get_json()["enviados"][0]

        cat = self.c.post(f"/api/repositorios/{repo}/categorias", json={"nome": "Ciências"}, headers=cab)
        self.assertEqual(cat.status_code, 201)
        cat_id = cat.get_json()["id"]

        repetida = self.c.post(f"/api/repositorios/{repo}/categorias", json={"nome": "Ciências"}, headers=cab)
        self.assertEqual(repetida.status_code, 409)

        movido = self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"categoria_id": cat_id}, headers=cab)
        self.assertEqual(movido.get_json()["categoria_id"], cat_id)

        self.assertEqual(self.c.delete(f"/api/categorias/{cat_id}", headers=cab).status_code, 200)

        lista = self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json()
        self.assertEqual(len(lista), 1)
        self.assertIsNone(lista[0]["categoria_id"])

    def test_nao_move_para_categoria_de_outro_repositorio(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, repo_bia = self.criar_usuario_logado("bia@exemplo.com")

        cat_bia = self.c.post(f"/api/repositorios/{repo_bia}/categorias", json={"nome": "Dela"}, headers=cab_bia).get_json()
        arquivo = self.enviar(cab_ana, repo_ana, [(io.BytesIO(b"x"), "a.txt")]).get_json()["enviados"][0]

        resposta = self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"categoria_id": cat_bia["id"]}, headers=cab_ana)
        self.assertEqual(resposta.status_code, 400)


# Repositórios corporativos, membros e papéis
class TestRepositoriosCorporativos(ApiTestCase):
    def test_papeis_no_repositorio_corporativo(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        empresa = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana)
        self.assertEqual(empresa.status_code, 201)
        repo = empresa.get_json()["id"]
        self.assertEqual(empresa.get_json()["tipo"], "corporativo")

        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab_bia).status_code, 404)

        convite_bia = self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "ana@exemplo.com", "papel": "leitor"}, headers=cab_bia)
        self.assertEqual(convite_bia.status_code, 404)

        convite = self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "leitor"}, headers=cab_ana)
        self.assertEqual(convite.status_code, 200)

        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab_bia).status_code, 200)
        self.assertEqual(self.enviar(cab_bia, repo, [(io.BytesIO(b"x"), "a.txt")]).status_code, 403)

        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "editor"}, headers=cab_ana)
        self.assertEqual(self.enviar(cab_bia, repo, [(io.BytesIO(b"x"), "a.txt")]).status_code, 201)

        login = self.entrar("bia@exemplo.com", metodo="corporativo")
        self.assertEqual(login.status_code, 200)
        self.assertEqual([r["nome"] for r in login.get_json()["repositorios"]], ["Empresa"])
        self.assertEqual(login.get_json()["repositorios"][0]["papel"], "editor")

    def test_listar_e_remover_membros(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        repo = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana).get_json()["id"]
        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "editor"}, headers=cab_ana)

        membros = self.c.get(f"/api/repositorios/{repo}/membros", headers=cab_bia)
        self.assertEqual(membros.status_code, 200)
        self.assertEqual([(m["email"], m["papel"]) for m in membros.get_json()],
                         [("ana@exemplo.com", "dono"), ("bia@exemplo.com", "editor")])
        self.assertNotIn("senha_hash", membros.get_json()[0])

        bia_id = membros.get_json()[1]["usuario_id"]
        ana_id = membros.get_json()[0]["usuario_id"]

        self.assertEqual(self.c.delete(f"/api/repositorios/{repo}/membros/{ana_id}", headers=cab_bia).status_code, 403)
        self.assertEqual(self.c.delete(f"/api/repositorios/{repo}/membros/{ana_id}", headers=cab_ana).status_code, 400)

        self.assertEqual(self.c.delete(f"/api/repositorios/{repo}/membros/{bia_id}", headers=cab_ana).status_code, 200)
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab_bia).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/repositorios/{repo}/membros/{bia_id}", headers=cab_ana).status_code, 404)

    def test_repositorio_pessoal_nao_aceita_membros(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        self.cadastrar("bia@exemplo.com")

        resposta = self.c.post(f"/api/repositorios/{repo_ana}/membros", json={"email": "bia@exemplo.com", "papel": "editor"}, headers=cab_ana)
        self.assertEqual(resposta.status_code, 400)


# Pastas
class TestPastas(ApiTestCase):
    def test_criar_listar_e_nomes_repetidos(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        ciencias = self.nova_pasta(cab, repo, "Ciências")
        self.assertEqual(ciencias.status_code, 201)
        cid = ciencias.get_json()["id"]
        self.assertIsNone(ciencias.get_json()["pasta_pai_id"])

        fisica = self.nova_pasta(cab, repo, "Física", pai=cid)
        self.assertEqual(fisica.status_code, 201)
        self.assertEqual(fisica.get_json()["pasta_pai_id"], cid)

        self.assertEqual(self.nova_pasta(cab, repo, "ciências").status_code, 409)
        self.assertEqual(self.nova_pasta(cab, repo, "Física").status_code, 201)

        lista = self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json()
        self.assertEqual(len(lista), 3)

    def test_validacoes_do_nome(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        self.assertEqual(self.nova_pasta(cab, repo, "  ").status_code, 400)
        self.assertEqual(self.nova_pasta(cab, repo, "a/b").status_code, 400)
        self.assertEqual(self.nova_pasta(cab, repo, "x" * 101).status_code, 400)

    def test_pasta_pai_de_outro_repositorio_e_recusada(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, repo_bia = self.criar_usuario_logado("bia@exemplo.com")

        da_bia = self.nova_pasta(cab_bia, repo_bia, "Dela").get_json()["id"]

        self.assertEqual(self.nova_pasta(cab_ana, repo_ana, "Minha", pai=da_bia).status_code, 400)

    def test_permissoes_nas_pastas(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        repo = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana).get_json()["id"]
        pasta = self.nova_pasta(cab_ana, repo, "Geral").get_json()["id"]

        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab_bia).status_code, 404)
        self.assertEqual(self.nova_pasta(cab_bia, repo, "X").status_code, 404)

        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "leitor"}, headers=cab_ana)
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab_bia).status_code, 200)
        self.assertEqual(self.nova_pasta(cab_bia, repo, "X").status_code, 403)
        self.assertEqual(self.c.patch(f"/api/pastas/{pasta}", json={"nome": "Y"}, headers=cab_bia).status_code, 403)
        self.assertEqual(self.c.delete(f"/api/pastas/{pasta}", headers=cab_bia).status_code, 403)

    def test_renomear_e_mover_sem_criar_ciclo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        a = self.nova_pasta(cab, repo, "A").get_json()["id"]
        b = self.nova_pasta(cab, repo, "B", pai=a).get_json()["id"]
        c = self.nova_pasta(cab, repo, "C", pai=b).get_json()["id"]

        renomeada = self.c.patch(f"/api/pastas/{a}", json={"nome": "Nova A"}, headers=cab)
        self.assertEqual(renomeada.get_json()["nome"], "Nova A")

        self.assertEqual(self.c.patch(f"/api/pastas/{a}", json={"pasta_pai_id": a}, headers=cab).status_code, 400)
        self.assertEqual(self.c.patch(f"/api/pastas/{a}", json={"pasta_pai_id": c}, headers=cab).status_code, 400)

        movida = self.c.patch(f"/api/pastas/{c}", json={"pasta_pai_id": None}, headers=cab)
        self.assertEqual(movida.status_code, 200)
        self.assertIsNone(movida.get_json()["pasta_pai_id"])

    def test_limite_de_niveis(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        pai = None

        for i in range(8):
            resposta = self.nova_pasta(cab, repo, f"nivel{i}", pai=pai)
            self.assertEqual(resposta.status_code, 201)
            pai = resposta.get_json()["id"]

        self.assertEqual(self.nova_pasta(cab, repo, "nivel8", pai=pai).status_code, 400)

    def test_upload_para_uma_pasta_e_mover_arquivo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        pasta = self.nova_pasta(cab, repo, "Aulas").get_json()["id"]
        outra = self.nova_pasta(cab, repo, "Provas").get_json()["id"]

        arquivo = self.enviar(cab, repo, [(io.BytesIO(b"x"), "a.txt")], pasta_id=pasta).get_json()["enviados"][0]
        self.assertEqual(arquivo["pasta_id"], pasta)

        na_raiz = self.enviar(cab, repo, [(io.BytesIO(b"y"), "b.txt")]).get_json()["enviados"][0]
        self.assertIsNone(na_raiz["pasta_id"])

        movido = self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"pasta_id": outra}, headers=cab)
        self.assertEqual(movido.get_json()["pasta_id"], outra)
        raiz = self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"pasta_id": None}, headers=cab)
        self.assertIsNone(raiz.get_json()["pasta_id"])

        link = self.c.post(f"/api/repositorios/{repo}/links", json={"url": "https://exemplo.com", "pasta_id": pasta}, headers=cab)
        self.assertEqual(link.get_json()["pasta_id"], pasta)

    def test_pasta_de_outro_repositorio_no_upload_e_na_edicao(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, repo_bia = self.criar_usuario_logado("bia@exemplo.com")
        da_bia = self.nova_pasta(cab_bia, repo_bia, "Dela").get_json()["id"]

        self.assertEqual(self.enviar(cab_ana, repo_ana, [(io.BytesIO(b"x"), "a.txt")], pasta_id=da_bia).status_code, 400)

        arquivo = self.enviar(cab_ana, repo_ana, [(io.BytesIO(b"x"), "a.txt")]).get_json()["enviados"][0]
        self.assertEqual(self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"pasta_id": da_bia}, headers=cab_ana).status_code, 400)
        self.assertEqual(self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"pasta_id": "abc"}, headers=cab_ana).status_code, 400)

    def test_apagar_pasta_sobe_o_conteudo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        a = self.nova_pasta(cab, repo, "A").get_json()["id"]
        b = self.nova_pasta(cab, repo, "B", pai=a).get_json()["id"]
        self.nova_pasta(cab, repo, "B")
        arquivo = self.enviar(cab, repo, [(io.BytesIO(b"x"), "a.txt")], pasta_id=a).get_json()["enviados"][0]
        no_b = self.enviar(cab, repo, [(io.BytesIO(b"y"), "b.txt")], pasta_id=b).get_json()["enviados"][0]

        self.assertEqual(self.c.delete(f"/api/pastas/{a}", headers=cab).status_code, 200)

        pastas = {p["id"]: p for p in self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json()}
        self.assertNotIn(a, pastas)
        self.assertIsNone(pastas[b]["pasta_pai_id"])
        self.assertEqual(pastas[b]["nome"], "B (2)")

        arquivos = {x["id"]: x for x in self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json()}
        self.assertEqual(len(arquivos), 2)
        self.assertIsNone(arquivos[arquivo["id"]]["pasta_id"])
        self.assertEqual(arquivos[no_b["id"]]["pasta_id"], b)


# Camada Repository: filtros em SQL
class TestFiltrosSQL(ApiTestCase):
    def preparar(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        ciencias = self.c.post(f"/api/repositorios/{repo}/categorias", json={"nome": "Ciências"}, headers=cab).get_json()["id"]
        pasta = self.nova_pasta(cab, repo, "Aulas").get_json()["id"]

        ids = {}
        for nome in ["Matemática Básica.txt", "MATEMATICA avançada.txt", "100% pronto.txt", "relatorio_final.txt", "relatorioXfinal.txt"]:
            ids[nome] = self.enviar(cab, repo, [(io.BytesIO(b"texto"), nome)]).get_json()["enviados"][0]["id"]

        link = self.c.post(f"/api/repositorios/{repo}/links", json={"url": "https://exemplo.com/artigo"}, headers=cab).get_json()["id"]

        # Duas matérias em "Ciências"; uma delas e o link dentro da pasta "Aulas"
        for nome in ["Matemática Básica.txt", "MATEMATICA avançada.txt"]:
            self.c.patch(f"/api/arquivos/{ids[nome]}", json={"categoria_id": ciencias}, headers=cab)
        self.c.patch(f"/api/arquivos/{ids['MATEMATICA avançada.txt']}", json={"pasta_id": pasta}, headers=cab)
        self.c.patch(f"/api/arquivos/{link}", json={"pasta_id": pasta}, headers=cab)

        return cab, repo, ciencias, pasta, ids, link

    def listar(self, cab, repo, consulta=""):
        resposta = self.c.get(f"/api/repositorios/{repo}/arquivos{consulta}", headers=cab)
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return resposta.get_json()

    def nomes(self, lista):
        return sorted(a["nome"] for a in lista)

    def test_pesquisa_por_nome_ignora_acentos_e_maiusculas(self):
        cab, repo, *_ = self.preparar()

        achados = self.nomes(self.listar(cab, repo, "?q=matematica"))
        self.assertEqual(achados, ["MATEMATICA avançada.txt", "Matemática Básica.txt"])
        self.assertEqual(self.nomes(self.listar(cab, repo, "?q=MATEMÁTICA")), achados)
        self.assertEqual(self.listar(cab, repo, "?q=nao-existe"), [])

    def test_pesquisa_trata_curingas_e_sql_como_texto_comum(self):
        cab, repo, *_ = self.preparar()

        self.assertEqual(self.nomes(self.listar(cab, repo, "?q=100%25")), ["100% pronto.txt"])
        self.assertEqual(self.nomes(self.listar(cab, repo, "?q=relatorio_final")), ["relatorio_final.txt"])
        self.assertEqual(self.listar(cab, repo, "?q=x'%20OR%20'1'='1"), [])

    def test_filtro_por_categoria(self):
        cab, repo, ciencias, *_ = self.preparar()

        da_categoria = self.listar(cab, repo, f"?categoria={ciencias}")
        self.assertEqual(self.nomes(da_categoria), ["MATEMATICA avançada.txt", "Matemática Básica.txt"])
        self.assertEqual({a["categoria_nome"] for a in da_categoria}, {"Ciências"})

        sem_categoria = self.listar(cab, repo, "?categoria=sem")
        self.assertEqual(len(sem_categoria), 4)
        self.assertTrue(all(a["categoria_id"] is None and a["categoria_nome"] is None for a in sem_categoria))

    def test_filtros_de_pasta_tipo_e_situacao(self):
        cab, repo, _ciencias, pasta, ids, link = self.preparar()

        self.assertEqual(sorted(a["id"] for a in self.listar(cab, repo, f"?pasta={pasta}")),
                         sorted([ids["MATEMATICA avançada.txt"], link]))
        self.assertEqual(len(self.listar(cab, repo, "?pasta=raiz")), 4)

        self.assertEqual([a["id"] for a in self.listar(cab, repo, "?tipo=link")], [link])
        self.assertEqual(len(self.listar(cab, repo, "?tipo=arquivo")), 5)

        self.assertEqual(len(self.listar(cab, repo, "?status=extraido")), 6)
        self.assertEqual(self.listar(cab, repo, "?status=falhou"), [])

    def test_filtros_combinados(self):
        cab, repo, ciencias, pasta, *_ = self.preparar()

        achados = self.listar(cab, repo, f"?q=matematica&categoria={ciencias}&pasta={pasta}")
        self.assertEqual(self.nomes(achados), ["MATEMATICA avançada.txt"])
        self.assertEqual(self.listar(cab, repo, f"?q=matematica&tipo=link"), [])

    def test_resposta_tem_o_mesmo_formato_de_antes(self):
        cab, repo, *_ = self.preparar()

        primeiro = self.listar(cab, repo)[0]
        for campo in ["id", "tipo", "nome", "extensao", "tamanho", "url", "status", "observacao",
                      "repositorio_id", "usuario_id", "categoria_id", "pasta_id", "criado_em"]:
            self.assertIn(campo, primeiro)
        self.assertTrue(primeiro["criado_em"].endswith("Z") or "+" in primeiro["criado_em"])
        self.assertNotIn("texto_extraido", primeiro)

        # Mais novo primeiro
        datas = [a["criado_em"] for a in self.listar(cab, repo)]
        self.assertEqual(datas, sorted(datas, reverse=True))

    def test_parametros_invalidos_dao_400(self):
        cab, repo, *_ = self.preparar()

        for consulta in ["?categoria=abc", "?pasta=-1", "?tipo=video", "?status=xyz", "?q=" + "a" * 101]:
            resposta = self.c.get(f"/api/repositorios/{repo}/arquivos{consulta}", headers=cab)
            self.assertEqual(resposta.status_code, 400, consulta)

    def test_filtro_respeita_permissoes_e_repositorios(self):
        cab_ana, repo_ana, *_ = self.preparar()
        cab_bia, _repo_bia = self.criar_usuario_logado("bia@exemplo.com")

        self.assertEqual(self.c.get(f"/api/repositorios/{repo_ana}/arquivos?q=matematica", headers=cab_bia).status_code, 404)
        self.assertEqual(self.c.get(f"/api/repositorios/{repo_ana}/arquivos?q=matematica").status_code, 401)

        # Arquivo da Bia nunca aparece na busca da Ana
        self.enviar(cab_bia, _repo_bia, [(io.BytesIO(b"x"), "matematica da bia.txt")])
        self.assertNotIn("matematica da bia.txt", self.nomes(self.listar(cab_ana, repo_ana, "?q=matematica")))


# Leitura do texto de arquivos e links
class TestLeituraDeConteudo(ApiTestCase):
    def test_txt_tem_o_texto_lido_no_upload(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        arquivo = self.enviar(cab, repo, [(io.BytesIO("olá mundo".encode("utf-8")), "nota.txt")]).get_json()["enviados"][0]
        self.assertEqual(arquivo["status"], "extraido")
        self.assertNotIn("texto_extraido", arquivo)

        dados = self.banco(arquivo["id"])
        self.assertEqual(dados["texto"], "olá mundo")
        self.assertIsNone(dados["observacao"])

    def test_docx_tem_o_texto_lido(self):
        import docx

        documento = docx.Document()
        documento.add_paragraph("Relatório de física")
        buffer = io.BytesIO()
        documento.save(buffer)
        buffer.seek(0)

        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar(cab, repo, [(buffer, "relatorio.docx")]).get_json()["enviados"][0]

        self.assertEqual(arquivo["status"], "extraido")
        self.assertIn("Relatório de física", self.banco(arquivo["id"])["texto"])

    def test_imagem_fica_sem_texto_e_continua_no_repositorio(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [(io.BytesIO(b"\x89PNG"), "foto.png")])
        self.assertEqual(resposta.status_code, 201)

        arquivo = resposta.get_json()["enviados"][0]
        self.assertEqual(arquivo["status"], "sem_texto")
        self.assertIn("ainda não tem leitura", arquivo["observacao"])

    def test_arquivo_ilegivel_falha_mas_o_upload_vale(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        resposta = self.enviar(cab, repo, [(io.BytesIO(b"isto nao e um pdf"), "quebrado.pdf")])
        self.assertEqual(resposta.status_code, 201)

        arquivo = resposta.get_json()["enviados"][0]
        self.assertEqual(arquivo["status"], "falhou")
        self.assertIn("PDF", arquivo["observacao"])

        lista = self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json()
        self.assertEqual(len(lista), 1)

    def test_arquivo_vazio_fica_sem_texto(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")

        arquivo = self.enviar(cab, repo, [(io.BytesIO(b"   \n  "), "vazio.txt")]).get_json()["enviados"][0]
        self.assertEqual(arquivo["status"], "sem_texto")

    def test_link_usa_titulo_da_pagina_quando_nao_ha_titulo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        url = f"/api/repositorios/{repo}/links"

        sem_titulo = self.c.post(url, json={"url": "https://exemplo.com/a"}, headers=cab).get_json()
        self.assertEqual(sem_titulo["status"], "extraido")
        self.assertEqual(sem_titulo["nome"], "Página de teste")
        self.assertEqual(self.banco(sem_titulo["id"])["texto"], "conteúdo da página")

        com_titulo = self.c.post(url, json={"url": "https://exemplo.com/b", "titulo": "Meu título"}, headers=cab).get_json()
        self.assertEqual(com_titulo["nome"], "Meu título")

    def test_link_que_falha_continua_salvo_e_da_para_reler(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        self.leitor_de_links.side_effect = ErroLink("O site respondeu com erro 500.")

        resposta = self.c.post(f"/api/repositorios/{repo}/links", json={"url": "https://exemplo.com/x"}, headers=cab)
        self.assertEqual(resposta.status_code, 201)

        link = resposta.get_json()
        self.assertEqual(link["status"], "falhou")
        self.assertEqual(link["observacao"], "O site respondeu com erro 500.")

        self.leitor_de_links.side_effect = None
        reler = self.c.post(f"/api/arquivos/{link['id']}/extrair", headers=cab)
        self.assertEqual(reler.status_code, 200)
        self.assertEqual(reler.get_json()["status"], "extraido")
        self.assertIsNone(reler.get_json()["observacao"])

    def test_erro_inesperado_na_leitura_nao_derruba_o_envio(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        self.leitor_de_links.side_effect = RuntimeError("bug qualquer")

        resposta = self.c.post(f"/api/repositorios/{repo}/links", json={"url": "https://exemplo.com/x"}, headers=cab)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["status"], "falhou")

    def test_so_editor_manda_reler(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        repo = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana).get_json()["id"]
        link = self.c.post(f"/api/repositorios/{repo}/links", json={"url": "https://exemplo.com/x"}, headers=cab_ana).get_json()

        self.assertEqual(self.c.post(f"/api/arquivos/{link['id']}/extrair", headers=cab_bia).status_code, 404)

        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "leitor"}, headers=cab_ana)
        self.assertEqual(self.c.post(f"/api/arquivos/{link['id']}/extrair", headers=cab_bia).status_code, 403)


# IA: sugestões de organização e busca por significado (Gemini simulado)
class TestIA(ApiTestCase):
    def setUp(self):
        super().setUp()

        ambiente = mock.patch.dict(os.environ, {"GEMINI_API_KEY": "chave-de-teste"})
        ambiente.start()
        self.addCleanup(ambiente.stop)

        # Resposta do "Gemini" que cada teste pode trocar
        self.resposta_ia = {"categoria": "Finanças", "pasta": ["Documentos", "2024"], "motivo": "Fala de gastos"}

        json_falso = mock.patch("services.ia.gemini.gerar_json", side_effect=lambda *_: self.resposta_ia)
        self.gerar_json = json_falso.start()
        self.addCleanup(json_falso.stop)

        # Vetor simples: textos com "banana" apontam para um lado, o resto para o outro
        vetor_falso = mock.patch(
            "services.ia.gemini.gerar_embedding",
            side_effect=lambda texto, tarefa: [1.0, 0.0] if "banana" in texto.lower() else [0.0, 1.0],
        )
        self.gerar_vetor = vetor_falso.start()
        self.addCleanup(vetor_falso.stop)

    def enviar_txt(self, cab, repo, nome="gastos.txt", texto="nota fiscal e gastos do mes"):
        resposta = self.enviar(cab, repo, [(io.BytesIO(texto.encode()), nome)])
        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()["enviados"][0]

    def listar(self, cab, repo):
        return self.c.get(f"/api/repositorios/{repo}/arquivos", headers=cab).get_json()

    def pedir(self, cab, arquivo_id):
        return self.c.post(f"/api/arquivos/{arquivo_id}/sugestao", headers=cab)

    def aplicar(self, cab, arquivo_id):
        return self.c.post(f"/api/arquivos/{arquivo_id}/sugestao/aplicar", headers=cab)

    # Sugerir
    def test_sugestao_aparece_na_listagem_e_nao_muda_nada(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)

        resposta = self.pedir(cab, arquivo["id"])
        self.assertEqual(resposta.status_code, 200)

        dados = resposta.get_json()
        self.assertEqual(dados["sugestao_categoria"], "Finanças")
        self.assertEqual(dados["sugestao_pasta"], "Documentos / 2024")
        self.assertEqual(dados["sugestao_motivo"], "Fala de gastos")
        self.assertIsNone(dados["categoria_id"])
        self.assertIsNone(dados["pasta_id"])

        # Nada foi criado ainda
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/categorias", headers=cab).get_json(), [])
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json(), [])
        self.assertEqual(self.listar(cab, repo)[0]["sugestao_categoria"], "Finanças")

    def test_nova_sugestao_troca_a_anterior(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)
        self.pedir(cab, arquivo["id"])

        self.resposta_ia = {"categoria": "Estudos", "pasta": [], "motivo": "outra"}
        dados = self.pedir(cab, arquivo["id"]).get_json()
        self.assertEqual(dados["sugestao_categoria"], "Estudos")
        self.assertIsNone(dados["sugestao_pasta"])

        with app.app_context():
            self.assertEqual(db.session.execute(db.select(db.func.count(SugestaoIA.id))).scalar(), 1)

    def test_condicoes_para_sugerir(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)

        # IA desligada nas configurações
        self.c.patch("/api/usuarios/me/config", headers=cab, json={"ia_ativa": False})
        self.assertEqual(self.pedir(cab, arquivo["id"]).status_code, 403)
        self.c.patch("/api/usuarios/me/config", headers=cab, json={"ia_ativa": True})

        # Servidor sem chave
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertEqual(self.pedir(cab, arquivo["id"]).status_code, 503)

        # Arquivo sem texto
        with app.app_context():
            db.session.get(Arquivo, arquivo["id"]).status = "sem_texto"
            db.session.commit()
        self.assertEqual(self.pedir(cab, arquivo["id"]).status_code, 400)

        self.assertEqual(self.pedir(cab, 99999).status_code, 404)
        self.gerar_json.assert_not_called()

    def test_resposta_inutil_da_ia_da_502(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)

        self.resposta_ia = {"categoria": None, "pasta": [], "motivo": ""}
        self.assertEqual(self.pedir(cab, arquivo["id"]).status_code, 502)
        self.assertIsNone(self.listar(cab, repo)[0]["sugestao_categoria"])

    # Aplicar
    def test_aplicar_cria_categoria_e_pastas_e_move_o_arquivo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)
        self.pedir(cab, arquivo["id"])

        resposta = self.aplicar(cab, arquivo["id"])
        self.assertEqual(resposta.status_code, 200)

        dados = resposta.get_json()
        self.assertEqual(dados["criadas"], {"categoria": "Finanças", "pastas": ["Documentos", "2024"]})
        self.assertEqual(dados["arquivo"]["categoria_nome"], "Finanças")
        self.assertEqual(dados["arquivo"]["status"], "processado")
        self.assertIsNone(dados["arquivo"]["sugestao_categoria"])

        pastas = {p["nome"]: p for p in self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json()}
        self.assertIsNone(pastas["Documentos"]["pasta_pai_id"])
        self.assertEqual(pastas["2024"]["pasta_pai_id"], pastas["Documentos"]["id"])
        self.assertEqual(dados["arquivo"]["pasta_id"], pastas["2024"]["id"])

        # A sugestão some depois de aplicada
        self.assertEqual(self.aplicar(cab, arquivo["id"]).status_code, 404)

    def test_aplicar_reaproveita_o_que_ja_existe(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        self.c.post(f"/api/repositorios/{repo}/categorias", json={"nome": "Finanças"}, headers=cab)
        documentos = self.nova_pasta(cab, repo, "Documentos").get_json()

        arquivo = self.enviar_txt(cab, repo)
        self.resposta_ia = {"categoria": "financas", "pasta": ["documentos", "2024"], "motivo": ""}
        self.pedir(cab, arquivo["id"])

        dados = self.aplicar(cab, arquivo["id"]).get_json()
        self.assertEqual(dados["criadas"], {"categoria": None, "pastas": ["2024"]})

        categorias = self.c.get(f"/api/repositorios/{repo}/categorias", headers=cab).get_json()
        self.assertEqual([c["nome"] for c in categorias], ["Finanças"])

        pastas = self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json()
        self.assertEqual(len(pastas), 2)
        subpasta = next(p for p in pastas if p["nome"] == "2024")
        self.assertEqual(subpasta["pasta_pai_id"], documentos["id"])

    def test_aplicar_so_categoria_mantem_a_pasta(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        pasta = self.nova_pasta(cab, repo, "Fotos").get_json()
        arquivo = self.enviar_txt(cab, repo)
        self.c.patch(f"/api/arquivos/{arquivo['id']}", json={"pasta_id": pasta["id"]}, headers=cab)

        self.resposta_ia = {"categoria": "Lazer", "pasta": [], "motivo": ""}
        self.pedir(cab, arquivo["id"])

        dados = self.aplicar(cab, arquivo["id"]).get_json()["arquivo"]
        self.assertEqual(dados["categoria_nome"], "Lazer")
        self.assertEqual(dados["pasta_id"], pasta["id"])

    # Ignorar
    def test_ignorar_descarta_sem_mudar_o_arquivo(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)
        self.pedir(cab, arquivo["id"])

        self.assertEqual(self.c.delete(f"/api/arquivos/{arquivo['id']}/sugestao", headers=cab).status_code, 200)

        item = self.listar(cab, repo)[0]
        self.assertIsNone(item["sugestao_categoria"])
        self.assertIsNone(item["categoria_id"])
        self.assertEqual(item["status"], "extraido")
        self.assertEqual(self.c.get(f"/api/repositorios/{repo}/pastas", headers=cab).get_json(), [])

    # Permissões
    def test_permissoes(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")

        repo = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana).get_json()["id"]
        arquivo = self.enviar_txt(cab_ana, repo)
        self.pedir(cab_ana, arquivo["id"])

        # Quem não é membro não vê nada
        self.assertEqual(self.pedir(cab_bia, arquivo["id"]).status_code, 404)
        self.assertEqual(self.aplicar(cab_bia, arquivo["id"]).status_code, 404)
        self.assertEqual(self.c.delete(f"/api/arquivos/{arquivo['id']}/sugestao", headers=cab_bia).status_code, 404)

        # Leitor não pede, não aplica e não ignora
        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "leitor"}, headers=cab_ana)
        self.assertEqual(self.pedir(cab_bia, arquivo["id"]).status_code, 403)
        self.assertEqual(self.aplicar(cab_bia, arquivo["id"]).status_code, 403)
        self.assertEqual(self.c.delete(f"/api/arquivos/{arquivo['id']}/sugestao", headers=cab_bia).status_code, 403)

        # Sem login
        self.assertEqual(self.c.post(f"/api/arquivos/{arquivo['id']}/sugestao").status_code, 401)

    def test_excluir_arquivo_apaga_a_sugestao(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        arquivo = self.enviar_txt(cab, repo)
        self.pedir(cab, arquivo["id"])

        self.assertEqual(self.c.delete(f"/api/arquivos/{arquivo['id']}", headers=cab).status_code, 200)

        with app.app_context():
            self.assertEqual(db.session.execute(db.select(db.func.count(SugestaoIA.id))).scalar(), 0)

    # Busca por significado
    def test_busca_por_significado(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        frutas = self.enviar_txt(cab, repo, "frutas.txt", "banana e maçã")
        self.enviar_txt(cab, repo, "carros.txt", "motor e rodas")

        resposta = self.c.get(f"/api/repositorios/{repo}/busca-semantica?q=banana", headers=cab)
        self.assertEqual(resposta.status_code, 200)

        dados = resposta.get_json()
        self.assertEqual([a["id"] for a in dados["resultados"]], [frutas["id"]])
        self.assertGreater(dados["resultados"][0]["pontuacao"], 0.9)
        self.assertEqual(dados["nao_indexados"], 0)

        # Segunda busca não gera vetores dos arquivos de novo
        chamadas = self.gerar_vetor.call_count
        self.c.get(f"/api/repositorios/{repo}/busca-semantica?q=banana", headers=cab)
        self.assertEqual(self.gerar_vetor.call_count, chamadas + 1)

    def test_busca_por_significado_nao_vaza_outro_repositorio(self):
        cab_ana, repo_ana = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, repo_bia = self.criar_usuario_logado("bia@exemplo.com")
        self.enviar_txt(cab_ana, repo_ana, "frutas.txt", "banana")

        dados = self.c.get(f"/api/repositorios/{repo_bia}/busca-semantica?q=banana", headers=cab_bia).get_json()
        self.assertEqual(dados["resultados"], [])
        self.assertEqual(self.c.get(f"/api/repositorios/{repo_ana}/busca-semantica?q=banana", headers=cab_bia).status_code, 404)

    def test_busca_por_significado_validacoes(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        url = f"/api/repositorios/{repo}/busca-semantica"

        self.assertEqual(self.c.get(url, headers=cab).status_code, 400)
        self.assertEqual(self.c.get(url + "?q=%20%20", headers=cab).status_code, 400)
        self.assertEqual(self.c.get(url + "?q=" + "a" * 201, headers=cab).status_code, 400)

        self.c.patch("/api/usuarios/me/config", headers=cab, json={"ia_ativa": False})
        self.assertEqual(self.c.get(url + "?q=banana", headers=cab).status_code, 403)

    def test_leitor_pode_buscar_por_significado(self):
        cab_ana, _ = self.criar_usuario_logado("ana@exemplo.com")
        cab_bia, _ = self.criar_usuario_logado("bia@exemplo.com")
        repo = self.c.post("/api/repositorios", json={"nome": "Empresa"}, headers=cab_ana).get_json()["id"]
        self.enviar_txt(cab_ana, repo, "frutas.txt", "banana")
        self.c.post(f"/api/repositorios/{repo}/membros", json={"email": "bia@exemplo.com", "papel": "leitor"}, headers=cab_ana)

        resposta = self.c.get(f"/api/repositorios/{repo}/busca-semantica?q=banana", headers=cab_bia)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.get_json()["resultados"]), 1)

    def test_falha_ao_indexar_nao_derruba_a_busca(self):
        cab, repo = self.criar_usuario_logado("ana@exemplo.com")
        self.enviar_txt(cab, repo, "frutas.txt", "banana")

        chamadas = []

        def vetor(texto, tarefa):
            chamadas.append(tarefa)
            if tarefa == "RETRIEVAL_DOCUMENT":
                raise ErroServico("limite", 429)
            return [1.0, 0.0]

        self.gerar_vetor.side_effect = vetor
        resposta = self.c.get(f"/api/repositorios/{repo}/busca-semantica?q=banana", headers=cab)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["resultados"], [])
        self.assertEqual(resposta.get_json()["nao_indexados"], 1)


if __name__ == "__main__":
    unittest.main()
