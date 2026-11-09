document.addEventListener("DOMContentLoaded", async () => {
    if (!Sessao.exigirLogin()) return;

    // Elementos da tela
    const seletorModo = document.getElementById("modo-select");
    const formularioRepo = document.getElementById("repo-form");
    const campoRepo = document.getElementById("repo-nome");
    const botaoCriarRepo = document.getElementById("btnCriarRepo");
    const seletorPasta = document.getElementById("pasta-select");
    const seletor = document.getElementById("repositorio-select");
    const entradaArquivos = document.getElementById("file-input");
    const caixaUpload = document.getElementById("upload-box");
    const formularioLink = document.getElementById("link-form");
    const campoLink = document.getElementById("link-url");
    const botaoLink = document.getElementById("btnLink");
    const botaoVer = document.getElementById("btnVerRepositorio");
    const lista = document.getElementById("resultado");
    const mensagem = document.getElementById("mensagem");

    // Repositórios do modo escolhido
    let repositorios = [];

    document.getElementById("nome-usuario").textContent = (Sessao.usuario && Sessao.usuario.nome) || "";
    document.getElementById("btnSair").addEventListener("click", () => Sessao.sair());

    // Repositório escolhido
    function repositorioAtual() {
        return repositorios.find((r) => String(r.id) === seletor.value);
    }

    function podeEnviar() {
        const repo = repositorioAtual();
        return Boolean(repo) && (repo.papel === "editor" || repo.papel === "dono");
    }

    // Pastas do repositório (destino do envio)
    async function carregarPastas() {
        seletorPasta.replaceChildren();

        const raiz = document.createElement("option");
        raiz.value = "";
        raiz.textContent = t("upload.pasta_raiz");
        seletorPasta.appendChild(raiz);

        const repo = repositorioAtual();
        if (!repo) return;

        try {
            const pastas = caminhosDasPastas(await api(`/repositorios/${repo.id}/pastas`));

            pastas.forEach((pasta) => {
                const opcao = document.createElement("option");
                opcao.value = String(pasta.id);
                opcao.textContent = pasta.caminho;
                seletorPasta.appendChild(opcao);
            });

            const sugerida = Sessao.ler("sindex_pasta");
            if (sugerida && pastas.some((p) => String(p.id) === sugerida)) {
                seletorPasta.value = sugerida;
            }
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
        }
    }

    function pastaEscolhida() {
        return seletorPasta.value ? Number(seletorPasta.value) : null;
    }

    // Libera ou bloqueia o envio conforme a permissão
    function atualizarEstado() {
        const pode = podeEnviar();

        seletorPasta.disabled = !pode;
        entradaArquivos.disabled = !pode;
        campoLink.disabled = !pode;
        botaoLink.disabled = !pode;
        botaoVer.disabled = !repositorioAtual();
        caixaUpload.classList.toggle("desativado", !pode);

        if (!repositorioAtual()) {
            const aviso = Sessao.metodo === "corporativo"
                ? t("upload.sem_repo_corp")
                : t("upload.sem_repo");
            mostrarMensagem(mensagem, aviso, "erro");
        } else if (!pode) {
            mostrarMensagem(mensagem, t("upload.somente_leitura"), "erro");
        } else {
            limparMensagem(mensagem);
        }
    }

    // Carrega os repositórios do usuário
    async function carregarRepositorios() {
        try {
            repositorios = await api(`/repositorios?tipo=${encodeURIComponent(Sessao.metodo)}`);
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
            return;
        }

        seletor.replaceChildren();

        repositorios.forEach((repo) => {
            const opcao = document.createElement("option");
            opcao.value = String(repo.id);
            opcao.textContent = repo.nome;
            seletor.appendChild(opcao);
        });

        const lembrado = Sessao.ler("sindex_repositorio");

        if (lembrado && repositorios.some((r) => String(r.id) === lembrado)) {
            seletor.value = lembrado;
        }

        atualizarEstado();
        await carregarPastas();
    }

    // Trocar entre pessoal e corporativo
    seletorModo.value = Sessao.metodo;

    seletorModo.addEventListener("change", async () => {
        Sessao.gravar("sindex_metodo", seletorModo.value);
        Sessao.remover("sindex_repositorio");
        lista.replaceChildren();
        await carregarRepositorios();
    });

    // Criar repositório corporativo
    formularioRepo.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        botaoCriarRepo.disabled = true;

        try {
            const novo = await api("/repositorios", {
                metodo: "POST",
                corpo: { nome: campoRepo.value.trim() },
            });

            campoRepo.value = "";
            formularioRepo.closest("details").open = false;

            Sessao.gravar("sindex_metodo", "corporativo");
            Sessao.gravar("sindex_repositorio", String(novo.id));
            seletorModo.value = "corporativo";
            lista.replaceChildren();

            await carregarRepositorios();
            mostrarMensagem(mensagem, t("upload.repo_criado", { nome: novo.nome }), "sucesso");
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
        } finally {
            botaoCriarRepo.disabled = false;
        }
    });

    // Trocar de repositório
    seletor.addEventListener("change", async () => {
        Sessao.gravar("sindex_repositorio", seletor.value);
        Sessao.remover("sindex_pasta");
        lista.replaceChildren();
        atualizarEstado();
        await carregarPastas();
    });

    // Abrir o repositório
    botaoVer.addEventListener("click", () => {
        const repo = repositorioAtual();
        if (!repo) return;

        Sessao.gravar("sindex_repositorio", String(repo.id));

        const pasta = pastaEscolhida();
        window.location.href = `repositorio.html?id=${repo.id}` + (pasta ? `&pasta=${pasta}` : "");
    });

    // Upload de arquivos
    function adicionarLinhaResultado(texto, classe) {
        const item = document.createElement("li");
        item.className = classe;
        item.textContent = texto;
        lista.appendChild(item);
    }

    async function enviar(arquivos) {
        if (!podeEnviar() || arquivos.length === 0) return;

        limparMensagem(mensagem);
        lista.replaceChildren();
        adicionarLinhaResultado(t("upload.enviando", { n: arquivos.length }), "");

        const formulario = new FormData();
        arquivos.forEach((arquivo) => formulario.append("arquivos", arquivo));

        if (pastaEscolhida()) formulario.append("pasta_id", String(pastaEscolhida()));

        let resultado;

        try {
            resultado = await api(`/repositorios/${seletor.value}/arquivos`, {
                metodo: "POST",
                corpo: formulario,
            });
        } catch (erro) {
            resultado = erro.dados && erro.dados.erros ? { enviados: [], erros: erro.dados.erros } : null;

            if (!resultado) {
                lista.replaceChildren();
                mostrarMensagem(mensagem, erro.message);
                return;
            }
        }

        lista.replaceChildren();
        resultado.enviados.forEach((a) => descreverResultado(a, t("upload.enviado", { nome: a.nome })));
        resultado.erros.forEach((e) => adicionarLinhaResultado(`✖ ${e.arquivo}: ${traduzirServidor(e.erro)}`, "falha"));
    }

    // Mostra o que aconteceu com a leitura do conteúdo
    function descreverResultado(item, textoBase) {
        if (item.status === "extraido") {
            adicionarLinhaResultado(t("upload.texto_lido", { base: textoBase }), "ok");
        } else if (item.status === "sem_texto") {
            adicionarLinhaResultado(t("upload.sem_texto", { base: textoBase }) + (item.observacao ? ` (${traduzirServidor(item.observacao)})` : ""), "aviso");
        } else if (item.status === "falhou") {
            adicionarLinhaResultado(t("upload.leitura_falhou", { base: textoBase, motivo: traduzirServidor(item.observacao) || t("upload.erro_desconhecido") }), "aviso");
        } else {
            adicionarLinhaResultado(textoBase, "ok");
        }
    }

    entradaArquivos.addEventListener("change", async () => {
        const arquivos = Array.from(entradaArquivos.files);
        entradaArquivos.value = "";
        await enviar(arquivos);
    });

    // Arrastar e soltar
    ["dragenter", "dragover"].forEach((tipo) => {
        caixaUpload.addEventListener(tipo, (evento) => {
            evento.preventDefault();
            if (podeEnviar()) caixaUpload.classList.add("arrastando");
        });
    });

    ["dragleave", "drop"].forEach((tipo) => {
        caixaUpload.addEventListener(tipo, (evento) => {
            evento.preventDefault();
            caixaUpload.classList.remove("arrastando");
        });
    });

    caixaUpload.addEventListener("drop", async (evento) => {
        await enviar(Array.from(evento.dataTransfer.files));
    });

    // Adicionar link
    formularioLink.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        if (!podeEnviar()) return;

        limparMensagem(mensagem);
        lista.replaceChildren();

        try {
            botaoLink.disabled = true;
            adicionarLinhaResultado(t("upload.lendo_link"), "");

            const link = await api(`/repositorios/${seletor.value}/links`, {
                metodo: "POST",
                corpo: { url: campoLink.value.trim(), pasta_id: pastaEscolhida() },
            });

            lista.replaceChildren();
            descreverResultado(link, t("upload.link_adicionado", { nome: link.nome }));
            campoLink.value = "";
        } catch (erro) {
            lista.replaceChildren();
            mostrarMensagem(mensagem, erro.message);
        } finally {
            botaoLink.disabled = !podeEnviar();
        }
    });

    // Início
    await carregarRepositorios();
});
