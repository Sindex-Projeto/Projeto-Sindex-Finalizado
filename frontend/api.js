// Endereço do backend
const API_URL = "http://127.0.0.1:5000/api";

// Sessão: guarda o login no navegador
const Sessao = {
    ler(chave) {
        try { return localStorage.getItem(chave); } catch { return null; }
    },

    gravar(chave, valor) {
        try { localStorage.setItem(chave, valor); } catch { }
    },

    remover(chave) {
        try { localStorage.removeItem(chave); } catch { }
    },

    get token() {
        return this.ler("sindex_token");
    },

    get metodo() {
        return this.ler("sindex_metodo") || "pessoal";
    },

    get usuario() {
        try { return JSON.parse(this.ler("sindex_usuario")); } catch { return null; }
    },

    // Guarda o login (e as configurações da conta)
    iniciar(token, usuario, metodo) {
        this.gravar("sindex_token", token);
        this.gravar("sindex_usuario", JSON.stringify(usuario));
        this.gravar("sindex_metodo", metodo);
        this.remover("sindex_repositorio");

        if (usuario && usuario.config) Config.gravarLocal(usuario.config);
    },

    encerrar() {
        ["sindex_token", "sindex_usuario", "sindex_metodo", "sindex_repositorio"]
            .forEach((chave) => this.remover(chave));
    },

    // Volta para o login se não houver sessão
    exigirLogin() {
        if (!this.token) {
            window.location.href = "index.html";
            return false;
        }
        return true;
    },

    sair() {
        this.encerrar();
        window.location.href = "index.html";
    },
};

// Chamada à API: devolve o JSON ou lança erro com a mensagem do servidor
async function api(caminho, { metodo = "GET", corpo, publico = false } = {}) {
    const cabecalhos = {};

    if (!publico && Sessao.token) {
        cabecalhos["Authorization"] = `Bearer ${Sessao.token}`;
    }

    let body;

    if (corpo instanceof FormData) {
        body = corpo;
    } else if (corpo !== undefined) {
        cabecalhos["Content-Type"] = "application/json";
        body = JSON.stringify(corpo);
    }

    let resposta;

    try {
        resposta = await fetch(`${API_URL}${caminho}`, { method: metodo, headers: cabecalhos, body });
    } catch {
        throw new Error(t("comum.erro_conexao"));
    }

    // Sessão vencida: volta para o login
    if (resposta.status === 401 && !publico) {
        Sessao.encerrar();
        window.location.href = "index.html";
        throw new Error(t("comum.sessao_expirada"));
    }

    const dados = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
        const erro = new Error(traduzirServidor(dados.erro) || t("comum.erro_generico"));
        erro.dados = dados;
        erro.status = resposta.status;
        throw erro;
    }

    return dados;
}

// Download (precisa do token, por isso não é um link simples)
async function baixarArquivo(id, nomeSugerido) {
    let resposta;

    try {
        resposta = await fetch(`${API_URL}/arquivos/${id}/download`, {
            headers: { Authorization: `Bearer ${Sessao.token}` },
        });
    } catch {
        throw new Error(t("comum.erro_conexao"));
    }

    if (!resposta.ok) {
        const dados = await resposta.json().catch(() => ({}));
        throw new Error(traduzirServidor(dados.erro) || t("comum.erro_baixar"));
    }

    const blob = await resposta.blob();
    const endereco = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = endereco;
    link.download = nomeSugerido;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(endereco);
}

// Mensagens de erro e sucesso na tela
function mostrarMensagem(elemento, texto, tipo = "erro") {
    elemento.textContent = texto;
    elemento.className = `mensagem ${tipo}`;
    elemento.hidden = false;
}

function limparMensagem(elemento) {
    elemento.textContent = "";
    elemento.hidden = true;
}

// Monta o caminho de cada pasta (ex.: Ciências / Física)
function caminhosDasPastas(pastas) {
    const porId = new Map(pastas.map((p) => [p.id, p]));
    const cache = new Map();

    function caminho(pasta) {
        if (cache.has(pasta.id)) return cache.get(pasta.id);

        const pai = pasta.pasta_pai_id ? porId.get(pasta.pasta_pai_id) : null;
        const texto = pai ? `${caminho(pai)} / ${pasta.nome}` : pasta.nome;

        cache.set(pasta.id, texto);
        return texto;
    }

    return pastas
        .map((p) => ({ ...p, caminho: caminho(p) }))
        .sort((a, b) => a.caminho.localeCompare(b.caminho, Config.localeNavegador));
}

// Texto da situação do arquivo
function textoDoStatus(status) {
    if (status === "extraido" && !Config.iaAtiva) return t("status.extraido_sem_ia");
    return TEXTOS["pt-BR"][`status.${status}`] ? t(`status.${status}`) : status;
}

// Formatação de tamanho e data
function formatarTamanho(bytes) {
    if (bytes === null || bytes === undefined) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatarData(iso) {
    const data = new Date(iso);
    return isNaN(data) ? "—" : data.toLocaleString(Config.localeNavegador, { dateStyle: "short", timeStyle: "short" });
}
