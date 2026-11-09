document.addEventListener("DOMContentLoaded", async () => {
    if (!Sessao.exigirLogin()) return;

    // Elementos da tela
    const titulo = document.getElementById("titulo-repositorio");
    const papelEl = document.getElementById("papel-repositorio");
    const corpoTabela = document.getElementById("corpo-tabela");
    const tabelaWrap = document.getElementById("tabela-wrap");
    const vazio = document.getElementById("vazio");
    const mensagem = document.getElementById("mensagem");
    const barraFiltros = document.getElementById("filtros");
    const campoBusca = document.getElementById("busca");
    const filtroCategoria = document.getElementById("filtro-categoria");
    const filtroTipo = document.getElementById("filtro-tipo");
    const avisoBusca = document.getElementById("aviso-busca");
    const buscaIaWrap = document.getElementById("busca-ia-wrap");
    const buscaIa = document.getElementById("busca-ia");
    const barraIa = document.getElementById("barra-ia");
    const botaoOrganizar = document.getElementById("btnOrganizarTodos");
    const botaoAplicarTodas = document.getElementById("btnAplicarTodas");
    const progressoIa = document.getElementById("progresso-ia");

    const trilha = document.getElementById("trilha");
    const secaoPastas = document.getElementById("secao-pastas");
    const listaPastasEl = document.getElementById("lista-pastas");
    const formPasta = document.getElementById("pasta-form");
    const campoPasta = document.getElementById("pasta-nome");

    const secaoCategorias = document.getElementById("secao-categorias");
    const listaCategoriasEl = document.getElementById("lista-categorias");
    const semCategorias = document.getElementById("sem-categorias");
    const formCategoria = document.getElementById("categoria-form");
    const campoCategoria = document.getElementById("categoria-nome");

    const secaoMembros = document.getElementById("secao-membros");
    const corpoMembros = document.getElementById("corpo-membros");
    const formMembro = document.getElementById("membro-form");
    const campoMembroEmail = document.getElementById("membro-email");
    const campoMembroPapel = document.getElementById("membro-papel");

    document.getElementById("nome-usuario").textContent = (Sessao.usuario && Sessao.usuario.nome) || "";
    document.getElementById("btnSair").addEventListener("click", () => Sessao.sair());

    // Qual repositório abrir (vem na URL)
    const parametros = new URLSearchParams(window.location.search);
    const repositorioId = parametros.get("id") || Sessao.ler("sindex_repositorio");

    // Dados em uso na tela
    let repositorio = null;
    let podeEditar = false;
    let souDono = false;
    let listaCategorias = [];
    let categorias = {};
    let listaPastas = [];
    let pastaPorId = {};
    let pastaAtualId = null;
    let todosArquivos = [];
    let visiveis = [];
    let buscaAtiva = false;
    let numeroBusca = 0;
    let esperaDaBusca = null;
    let buscaSignificado = false;
    let naoIndexados = 0;

    // Quantos arquivos a IA analisa por clique em "Organizar tudo" (protege o limite gratuito)
    const LOTE_IA = 20;

    // Funções de apoio
    function celula(texto, classe) {
        const td = document.createElement("td");
        td.textContent = texto;
        if (classe) td.className = classe;
        return td;
    }

    function botaoAcao(texto, aoClicar, perigo = false) {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = perigo ? "acao perigo" : "acao";
        botao.textContent = texto;
        botao.addEventListener("click", aoClicar);
        return botao;
    }

    function opcao(valor, texto) {
        const o = document.createElement("option");
        o.value = valor;
        o.textContent = texto;
        return o;
    }

    // Executa uma ação e mostra o erro na tela se falhar
    async function tentar(acao) {
        try {
            limparMensagem(mensagem);
            await acao();
            return true;
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
            return false;
        }
    }

    // Texto sem acento, maiúsculas e espaços extras (para comparar nomes)
    function normalizar(texto) {
        return String(texto || "")
            .split("/").map((parte) => parte.trim()).join("/")
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    }

    function iaLigada() {
        return Config.iaAtiva;
    }

    // Todas as subpastas de uma pasta
    function idsDescendentes(pastaId) {
        const ids = new Set();
        const pilha = [pastaId];

        while (pilha.length) {
            const atual = pilha.pop();

            listaPastas.filter((p) => p.pasta_pai_id === atual).forEach((p) => {
                ids.add(p.id);
                pilha.push(p.id);
            });
        }

        return ids;
    }

    // Pastas: navegação (guarda a pasta aberta na URL)
    function atualizarEndereco() {
        const novo = `?id=${repositorioId}` + (pastaAtualId ? `&pasta=${pastaAtualId}` : "");
        window.history.replaceState(null, "", novo);

        if (pastaAtualId) Sessao.gravar("sindex_pasta", String(pastaAtualId));
        else Sessao.remover("sindex_pasta");
    }

    function irParaPasta(id) {
        pastaAtualId = id;
        campoBusca.value = "";
        atualizarEndereco();
        desenharPastas();
        tentar(buscarVisiveis);
    }

    // Trilha de pastas (Raiz / Ciências / Física)
    function desenharTrilha() {
        const caminho = [];
        let atual = pastaAtualId ? pastaPorId[pastaAtualId] : null;

        while (atual) {
            caminho.unshift(atual);
            atual = atual.pasta_pai_id ? pastaPorId[atual.pasta_pai_id] : null;
        }

        const itens = [{ id: null, nome: t("comum.raiz") }, ...caminho];

        trilha.replaceChildren(...itens.flatMap((pasta, indice) => {
            const ultimo = indice === itens.length - 1;
            const elementos = [];

            if (indice > 0) {
                const separador = document.createElement("span");
                separador.className = "trilha-sep";
                separador.textContent = "/";
                elementos.push(separador);
            }

            if (ultimo) {
                const atualEl = document.createElement("span");
                atualEl.className = "trilha-atual";
                atualEl.textContent = pasta.nome;
                atualEl.setAttribute("aria-current", "page");
                elementos.push(atualEl);
            } else {
                const botao = document.createElement("button");
                botao.type = "button";
                botao.className = "trilha-item";
                botao.textContent = pasta.nome;
                botao.addEventListener("click", () => irParaPasta(pasta.id));
                elementos.push(botao);
            }

            return elementos;
        }));

        trilha.hidden = false;
    }

    // Cartões das pastas
    function resumoDaPasta(pasta) {
        const arquivos = todosArquivos.filter((a) => a.pasta_id === pasta.id).length;
        const subpastas = listaPastas.filter((p) => p.pasta_pai_id === pasta.id).length;

        const partes = [tPlural("repo.arquivo", arquivos)];
        if (subpastas) partes.push(tPlural("repo.subpasta", subpastas));

        return partes.join(" · ");
    }

    // Cartão de uma pasta (abrir, renomear, mover, excluir)
    function cartaoDaPasta(pasta) {
        const item = document.createElement("li");
        item.className = "pasta-card";

        const abrir = document.createElement("button");
        abrir.type = "button";
        abrir.className = "pasta-abrir";
        abrir.addEventListener("click", () => irParaPasta(pasta.id));

        const icone = document.createElement("span");
        icone.className = "mini-pasta";
        icone.setAttribute("aria-hidden", "true");

        const nome = document.createElement("span");
        nome.className = "pasta-nome";
        nome.textContent = pasta.nome;

        const resumo = document.createElement("span");
        resumo.className = "pasta-resumo";
        resumo.textContent = resumoDaPasta(pasta);

        abrir.append(icone, nome, resumo);
        item.appendChild(abrir);

        if (podeEditar) {
            const acoes = document.createElement("div");
            acoes.className = "acoes pasta-acoes";

            acoes.appendChild(botaoAcao(t("repo.renomear"), () => renomearPasta(pasta)));

            const proibidas = idsDescendentes(pasta.id);
            proibidas.add(pasta.id);

            const mover = document.createElement("select");
            mover.className = "select-mini";
            mover.setAttribute("aria-label", t("repo.mover_aria", { nome: pasta.nome }));
            mover.appendChild(opcao("__nenhum", t("repo.mover_para")));
            mover.appendChild(opcao("__raiz", t("comum.raiz")));
            listaPastas.filter((p) => !proibidas.has(p.id)).forEach((p) => mover.appendChild(opcao(String(p.id), p.caminho)));

            mover.addEventListener("change", async () => {
                const destino = mover.value === "__raiz" ? null : Number(mover.value);
                mover.value = "__nenhum";

                await tentar(async () => {
                    await api(`/pastas/${pasta.id}`, { metodo: "PATCH", corpo: { pasta_pai_id: destino } });
                    await carregarPastas();
                });
            });

            acoes.appendChild(mover);
            acoes.appendChild(botaoAcao(t("repo.excluir"), () => excluirPasta(pasta), true));
            item.appendChild(acoes);
        }

        return item;
    }

    function desenharPastas() {
        desenharTrilha();

        const filhas = listaPastas.filter((p) => (p.pasta_pai_id ?? null) === pastaAtualId);

        listaPastasEl.replaceChildren(...filhas.map(cartaoDaPasta));
        listaPastasEl.hidden = filhas.length === 0;
        formPasta.hidden = !podeEditar;
        secaoPastas.hidden = filhas.length === 0 && !podeEditar;
    }

    // Carrega as pastas
    async function carregarPastas() {
        listaPastas = caminhosDasPastas(await api(`/repositorios/${repositorioId}/pastas`));
        pastaPorId = Object.fromEntries(listaPastas.map((p) => [p.id, p]));

        if (pastaAtualId && !pastaPorId[pastaAtualId]) {
            pastaAtualId = null;
            atualizarEndereco();
        }

        desenharPastas();
        await buscarVisiveis();
    }

    // Renomear e excluir pasta
    async function renomearPasta(pasta) {
        const novoNome = window.prompt(t("repo.novo_nome"), pasta.nome);

        if (novoNome === null || novoNome.trim() === "" || novoNome.trim() === pasta.nome) return;

        await tentar(async () => {
            await api(`/pastas/${pasta.id}`, { metodo: "PATCH", corpo: { nome: novoNome.trim() } });
            await carregarPastas();
        });
    }

    async function excluirPasta(pasta) {
        const aviso = t("repo.confirma_pasta", { nome: pasta.nome });

        if (!window.confirm(aviso)) return;

        await tentar(async () => {
            await api(`/pastas/${pasta.id}`, { metodo: "DELETE" });
            await carregarPastas();
            await carregarArquivos();
        });
    }

    // Criar pasta
    formPasta.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const criada = await tentar(async () => {
            await api(`/repositorios/${repositorioId}/pastas`, {
                metodo: "POST",
                corpo: { nome: campoPasta.value.trim(), pasta_pai_id: pastaAtualId },
            });
            await carregarPastas();
        });

        if (criada) campoPasta.value = "";
    });

    // Arquivos: colunas da tabela
    function celulaPasta(arquivo) {
        const td = document.createElement("td");

        if (!podeEditar) {
            td.textContent = arquivo.pasta_id && pastaPorId[arquivo.pasta_id] ? pastaPorId[arquivo.pasta_id].caminho : t("comum.raiz");
            return td;
        }

        const seletor = document.createElement("select");
        seletor.className = "select-mini";
        seletor.setAttribute("aria-label", t("repo.pasta_de", { nome: arquivo.nome }));
        seletor.appendChild(opcao("", t("comum.raiz")));
        listaPastas.forEach((p) => seletor.appendChild(opcao(String(p.id), p.caminho)));

        seletor.value = arquivo.pasta_id ? String(arquivo.pasta_id) : "";
        let anterior = seletor.value;

        seletor.addEventListener("change", async () => {
            const sucesso = await tentar(() => api(`/arquivos/${arquivo.id}`, {
                metodo: "PATCH",
                corpo: { pasta_id: seletor.value ? Number(seletor.value) : null },
            }));

            if (sucesso) {
                anterior = seletor.value;
                await tentar(carregarArquivos);
            } else {
                seletor.value = anterior;
            }
        });

        td.appendChild(seletor);
        return td;
    }

    // Coluna Categoria
    function celulaCategoria(arquivo) {
        const td = document.createElement("td");

        if (!podeEditar) {
            td.textContent = categorias[arquivo.categoria_id] || t("comum.sem_categoria");
            return td;
        }

        const seletor = document.createElement("select");
        seletor.className = "select-mini";
        seletor.setAttribute("aria-label", t("repo.categoria_de", { nome: arquivo.nome }));
        seletor.appendChild(opcao("", t("comum.sem_categoria")));
        listaCategorias.forEach((c) => seletor.appendChild(opcao(String(c.id), c.nome)));

        seletor.value = arquivo.categoria_id ? String(arquivo.categoria_id) : "";
        let anterior = seletor.value;

        seletor.addEventListener("change", async () => {
            const sucesso = await tentar(() => api(`/arquivos/${arquivo.id}`, {
                metodo: "PATCH",
                corpo: { categoria_id: seletor.value ? Number(seletor.value) : null },
            }));

            if (sucesso) {
                anterior = seletor.value;
                arquivo.categoria_id = seletor.value ? Number(seletor.value) : null;
            } else {
                seletor.value = anterior;
            }
        });

        td.appendChild(seletor);
        return td;
    }

    // Coluna Situação
    function celulaSituacao(arquivo) {
        const td = document.createElement("td");
        td.className = "situacao";

        const texto = document.createElement("span");
        texto.className = `situacao-${arquivo.status}`;
        texto.textContent = textoDoStatus(arquivo.status);
        td.appendChild(texto);

        if (arquivo.observacao) {
            const obs = document.createElement("small");
            obs.className = "obs";
            obs.textContent = traduzirServidor(arquivo.observacao);
            td.appendChild(obs);
        }

        return td;
    }

    // Linha de um arquivo (nome, tipo, tamanho, ações...)
    function linhaDoArquivo(arquivo, emBusca) {
        const linha = document.createElement("tr");

        const tdNome = celula(arquivo.nome, "nome");

        if (emBusca) {
            const onde = document.createElement("small");
            onde.className = "obs";
            onde.textContent = arquivo.pasta_id && pastaPorId[arquivo.pasta_id]
                ? t("repo.em", { caminho: pastaPorId[arquivo.pasta_id].caminho })
                : t("repo.na_raiz");

            if (buscaSignificado && arquivo.pontuacao !== undefined) {
                onde.textContent += ` · ${t("ia.parecido", { n: Math.round(arquivo.pontuacao * 100) })}`;
            }

            tdNome.appendChild(onde);
        }

        const tdTipo = document.createElement("td");
        const etiqueta = document.createElement("span");
        etiqueta.className = "etiqueta";
        etiqueta.textContent = arquivo.tipo === "link" ? t("repo.tipo_link") : (arquivo.extensao || t("comum.arquivo_generico")).toUpperCase();
        tdTipo.appendChild(etiqueta);

        const tdAcoes = document.createElement("td");
        const acoes = document.createElement("div");
        acoes.className = "acoes";

        if (arquivo.tipo === "link") {
            if (/^https?:\/\//i.test(arquivo.url || "")) {
                const abrir = document.createElement("a");
                abrir.className = "acao";
                abrir.textContent = t("repo.abrir");
                abrir.href = arquivo.url;
                abrir.target = "_blank";
                abrir.rel = "noopener noreferrer";
                acoes.appendChild(abrir);
            }
        } else {
            acoes.appendChild(botaoAcao(t("repo.baixar"), () => tentar(() => baixarArquivo(arquivo.id, arquivo.nome))));
        }

        if (podeEditar && (arquivo.status === "falhou" || arquivo.status === "pendente")) {
            acoes.appendChild(botaoAcao(t("repo.ler_de_novo"), () => lerDeNovo(arquivo)));
        }

        if (podeEditar && iaLigada() && podeSugerir(arquivo) && !temSugestao(arquivo)) {
            const sugerir = botaoAcao(t("ia.sugerir"), () => pedirSugestao(arquivo, sugerir));
            sugerir.classList.add("ia");
            acoes.appendChild(sugerir);
        }

        if (podeEditar) {
            acoes.appendChild(botaoAcao(t("repo.excluir"), () => excluirArquivo(arquivo), true));
        }

        tdAcoes.appendChild(acoes);

        linha.append(
            tdNome,
            tdTipo,
            celula(arquivo.tipo === "link" ? "—" : formatarTamanho(arquivo.tamanho)),
            celulaPasta(arquivo),
            celulaCategoria(arquivo),
            celulaSituacao(arquivo),
            celula(formatarData(arquivo.criado_em)),
            tdAcoes
        );

        return linha;
    }

    // IA: sugestões
    function podeSugerir(arquivo) {
        return arquivo.status === "extraido" || arquivo.status === "processado";
    }

    function temSugestao(arquivo) {
        return Boolean(arquivo.sugestao_categoria || arquivo.sugestao_pasta);
    }

    // Linha extra com a sugestão da IA (o usuário escolhe aplicar ou ignorar)
    function linhaDaSugestao(arquivo) {
        const linha = document.createElement("tr");
        linha.className = "linha-sugestao";

        const td = document.createElement("td");
        td.colSpan = 8;

        const caixa = document.createElement("div");
        caixa.className = "sugestao-ia";

        const titulo = document.createElement("span");
        titulo.className = "sugestao-titulo";
        titulo.textContent = `✦ ${t("ia.sugestao_titulo")}`;
        caixa.appendChild(titulo);

        function parte(rotulo, valor, nova) {
            const el = document.createElement("span");
            el.textContent = `${rotulo}: `;

            const forte = document.createElement("strong");
            forte.textContent = valor;
            el.appendChild(forte);

            if (nova) {
                const selo = document.createElement("span");
                selo.className = "selo-novo";
                selo.textContent = t("ia.nova");
                el.appendChild(selo);
            }

            caixa.appendChild(el);
        }

        if (arquivo.sugestao_categoria) {
            const existe = listaCategorias.some((c) => normalizar(c.nome) === normalizar(arquivo.sugestao_categoria));
            parte(t("ia.categoria"), arquivo.sugestao_categoria, !existe);
        }

        if (arquivo.sugestao_pasta) {
            const existe = listaPastas.some((p) => normalizar(p.caminho) === normalizar(arquivo.sugestao_pasta));
            parte(t("ia.pasta"), arquivo.sugestao_pasta, !existe);
        }

        const acoes = document.createElement("div");
        acoes.className = "acoes";

        const aplicar = botaoAcao(t("ia.aplicar"), () => aplicarSugestao(arquivo));
        aplicar.classList.add("principal");
        acoes.append(aplicar, botaoAcao(t("ia.ignorar"), () => ignorarSugestao(arquivo)));
        caixa.appendChild(acoes);

        if (arquivo.sugestao_motivo) {
            const motivo = document.createElement("span");
            motivo.className = "sugestao-motivo";
            motivo.textContent = arquivo.sugestao_motivo;
            caixa.appendChild(motivo);
        }

        td.appendChild(caixa);
        linha.appendChild(td);
        return linha;
    }

    // Atualiza o arquivo na tela com o que o servidor devolveu
    function atualizarLocal(dados) {
        [todosArquivos, visiveis].forEach((lista) => {
            const atual = lista.find((a) => a.id === dados.id);
            if (atual) Object.assign(atual, dados);
        });
        desenharTabela();
    }

    async function pedirSugestao(arquivo, botao) {
        botao.disabled = true;
        botao.textContent = t("ia.sugerindo");

        const ok = await tentar(async () => {
            atualizarLocal(await api(`/arquivos/${arquivo.id}/sugestao`, { metodo: "POST" }));
        });

        if (!ok) {
            botao.disabled = false;
            botao.textContent = t("ia.sugerir");
        }
    }

    async function recarregarTudo() {
        await carregarCategorias();
        await carregarPastas();
        await carregarArquivos();
    }

    async function aplicarSugestao(arquivo) {
        await tentar(async () => {
            const resposta = await api(`/arquivos/${arquivo.id}/sugestao/aplicar`, { metodo: "POST" });
            await recarregarTudo();

            const criados = [resposta.criadas.categoria, ...resposta.criadas.pastas].filter(Boolean);

            mostrarMensagem(
                mensagem,
                criados.length ? t("ia.aplicada_criou", { itens: criados.join(", ") }) : t("ia.aplicada"),
                "sucesso"
            );
        });
    }

    async function ignorarSugestao(arquivo) {
        await tentar(async () => {
            await api(`/arquivos/${arquivo.id}/sugestao`, { metodo: "DELETE" });
            arquivo.sugestao_categoria = arquivo.sugestao_pasta = arquivo.sugestao_motivo = null;
            atualizarLocal(arquivo);
        });
    }

    // Pede sugestões para os arquivos que ainda não têm (um por vez, para respeitar o limite gratuito)
    async function organizarTodos() {
        const alvos = todosArquivos.filter((a) => a.status === "extraido" && !temSugestao(a));

        if (alvos.length === 0) {
            progressoIa.textContent = t("ia.nada");
            return;
        }

        const lote = alvos.slice(0, LOTE_IA);
        let feitas = 0;
        let falhasSeguidas = 0;
        let motivoDaParada = null;

        botaoOrganizar.disabled = true;
        limparMensagem(mensagem);

        for (const [indice, arquivo] of lote.entries()) {
            progressoIa.textContent = t("ia.progresso", { atual: indice + 1, total: lote.length });

            try {
                atualizarLocal(await api(`/arquivos/${arquivo.id}/sugestao`, { metodo: "POST" }));
                feitas += 1;
                falhasSeguidas = 0;
            } catch (erro) {
                falhasSeguidas += 1;

                // Sem permissão, sem chave ou limite gratuito: não adianta continuar
                if ([403, 429, 503].includes(erro.status) || falhasSeguidas >= 3) {
                    motivoDaParada = erro.message;
                    break;
                }
            }
        }

        botaoOrganizar.disabled = false;

        const restantes = alvos.length - lote.length;

        if (motivoDaParada) {
            progressoIa.textContent = t("ia.parou", { n: feitas, motivo: motivoDaParada });
        } else if (restantes > 0) {
            progressoIa.textContent = t("ia.prontas_restam", { n: feitas, r: restantes });
        } else {
            progressoIa.textContent = t("ia.prontas", { n: feitas });
        }
    }

    // Aplica todas as sugestões pendentes (depois de confirmar)
    async function aplicarTodas() {
        const pendentes = todosArquivos.filter(temSugestao);

        if (pendentes.length === 0) return;
        if (!window.confirm(t("ia.confirma_aplicar_todas", { n: pendentes.length }))) return;

        botaoAplicarTodas.disabled = true;
        let feitas = 0;

        await tentar(async () => {
            try {
                for (const arquivo of pendentes) {
                    await api(`/arquivos/${arquivo.id}/sugestao/aplicar`, { metodo: "POST" });
                    feitas += 1;
                }
            } finally {
                await recarregarTudo();
                progressoIa.textContent = t("ia.aplicadas", { n: feitas });
            }
        });

        botaoAplicarTodas.disabled = false;
    }

    botaoOrganizar.addEventListener("click", organizarTodos);
    botaoAplicarTodas.addEventListener("click", aplicarTodas);

    // Ler de novo e excluir arquivo
    async function lerDeNovo(arquivo) {
        await tentar(async () => {
            await api(`/arquivos/${arquivo.id}/extrair`, { metodo: "POST" });
            await carregarArquivos();
        });
    }

    async function excluirArquivo(arquivo) {
        if (!window.confirm(t("repo.confirma_arquivo", { nome: arquivo.nome }))) return;

        await tentar(async () => {
            await api(`/arquivos/${arquivo.id}`, { metodo: "DELETE" });
            await carregarArquivos();
        });
    }

    // Busca os arquivos no servidor (os filtros são feitos em SQL no backend)
    async function buscarVisiveis() {
        const texto = campoBusca.value.trim();
        const parametros = new URLSearchParams();

        if (texto) parametros.set("q", texto);
        if (filtroCategoria.value) parametros.set("categoria", filtroCategoria.value);
        if (filtroTipo.value) parametros.set("tipo", filtroTipo.value);

        // Sem busca, mostra só a pasta aberta. Com busca, procura no repositório inteiro.
        if (!texto) parametros.set("pasta", pastaAtualId ? String(pastaAtualId) : "raiz");

        const minha = ++numeroBusca;

        // Busca por significado (IA): só com texto digitado
        if (texto && iaLigada() && buscaIa.checked) {
            const resposta = await api(`/repositorios/${repositorioId}/busca-semantica?q=${encodeURIComponent(texto)}`);

            if (minha !== numeroBusca) return;

            // Categoria e tipo filtram o resultado aqui no navegador
            visiveis = resposta.resultados.filter((a) =>
                (!filtroTipo.value || a.tipo === filtroTipo.value)
                && (!filtroCategoria.value
                    || (filtroCategoria.value === "sem" ? !a.categoria_id : String(a.categoria_id) === filtroCategoria.value)));

            buscaSignificado = true;
            naoIndexados = resposta.nao_indexados;
            buscaAtiva = true;
            desenharTabela();
            return;
        }

        const resposta = await api(`/repositorios/${repositorioId}/arquivos?${parametros}`);

        // Se o usuário digitou mais enquanto esperava, ignora a resposta velha
        if (minha !== numeroBusca) return;

        visiveis = resposta;
        buscaSignificado = false;
        naoIndexados = 0;
        buscaAtiva = texto !== "";
        desenharTabela();
    }

    // Controles da IA (aparecem só com a IA ligada)
    function atualizarControlesIa() {
        const ligada = iaLigada();
        const pendentes = todosArquivos.filter(temSugestao).length;

        buscaIaWrap.hidden = !ligada;
        barraIa.hidden = !(ligada && podeEditar && todosArquivos.length > 0);
        botaoAplicarTodas.hidden = pendentes === 0;
        botaoAplicarTodas.textContent = t("ia.aplicar_todas", { n: pendentes });

        campoBusca.placeholder = ligada && buscaIa.checked ? t("ia.busca_ph_significado") : t("repo.busca_ph");
    }

    // Tabela: desenha o que o servidor devolveu
    function desenharTabela() {
        corpoTabela.replaceChildren(...visiveis.flatMap((a) => {
            const linhas = [linhaDoArquivo(a, buscaAtiva)];
            if (podeEditar && iaLigada() && temSugestao(a)) linhas.push(linhaDaSugestao(a));
            return linhas;
        }));

        atualizarControlesIa();

        barraFiltros.hidden = todosArquivos.length === 0;
        avisoBusca.hidden = !buscaAtiva;
        avisoBusca.textContent = buscaSignificado
            ? t("ia.aviso_significado") + (naoIndexados > 0 ? ` ${t("ia.nao_indexados", { n: naoIndexados })}` : "")
            : t("repo.aviso_busca");
        secaoPastas.classList.toggle("escondida", buscaAtiva);
        tabelaWrap.hidden = visiveis.length === 0;
        vazio.hidden = visiveis.length !== 0;

        if (todosArquivos.length === 0 && listaPastas.length === 0) {
            vazio.textContent = t("repo.vazio");
        } else if (buscaAtiva || filtroCategoria.value !== "" || filtroTipo.value !== "") {
            vazio.textContent = t("repo.vazio_busca");
        } else {
            vazio.textContent = t("repo.vazio_pasta");
        }
    }

    // Carrega os arquivos (todos, para contar por pasta, e os filtrados para a tabela)
    async function carregarArquivos() {
        todosArquivos = await api(`/repositorios/${repositorioId}/arquivos`);
        desenharPastas();
        await buscarVisiveis();
    }

    // Busca (espera o usuário parar de digitar), filtros e mudança de configuração
    campoBusca.addEventListener("input", () => {
        clearTimeout(esperaDaBusca);

        // A busca por significado usa a IA, então espera mais para não gastar o limite gratuito
        esperaDaBusca = setTimeout(() => tentar(buscarVisiveis), iaLigada() && buscaIa.checked ? 800 : 250);
    });
    buscaIa.addEventListener("change", () => {
        atualizarControlesIa();
        tentar(buscarVisiveis);
    });

    document.addEventListener("sindex:config", () => {
        // IA desligada: volta para a busca comum
        if (!iaLigada() && buscaIa.checked) {
            buscaIa.checked = false;
            tentar(buscarVisiveis);
        } else {
            desenharTabela();
        }
    });
    filtroCategoria.addEventListener("change", () => tentar(buscarVisiveis));
    filtroTipo.addEventListener("change", () => tentar(buscarVisiveis));

    // Categorias
    function desenharOpcoesDeFiltro() {
        const atual = filtroCategoria.value;

        filtroCategoria.replaceChildren(
            opcao("", t("repo.todas_categorias")),
            opcao("sem", t("comum.sem_categoria")),
            ...listaCategorias.map((c) => opcao(String(c.id), c.nome))
        );

        filtroCategoria.value = atual;

        if (filtroCategoria.value !== atual) filtroCategoria.value = "";
    }

    function desenharCategorias() {
        desenharOpcoesDeFiltro();
        secaoCategorias.hidden = false;
        formCategoria.hidden = !podeEditar;
        semCategorias.hidden = listaCategorias.length !== 0;

        listaCategoriasEl.replaceChildren(...listaCategorias.map((categoria) => {
            const item = document.createElement("li");
            item.className = "chip";

            const nome = document.createElement("span");
            nome.textContent = categoria.nome;
            item.appendChild(nome);

            if (podeEditar) {
                const apagar = document.createElement("button");
                apagar.type = "button";
                apagar.className = "chip-x";
                apagar.textContent = "✕";
                apagar.setAttribute("aria-label", t("repo.apagar_categoria_aria", { nome: categoria.nome }));
                apagar.addEventListener("click", () => excluirCategoria(categoria));
                item.appendChild(apagar);
            }

            return item;
        }));
    }

    // Carrega e apaga categorias
    async function carregarCategorias() {
        listaCategorias = await api(`/repositorios/${repositorioId}/categorias`);
        categorias = Object.fromEntries(listaCategorias.map((c) => [c.id, c.nome]));
        desenharCategorias();
    }

    async function excluirCategoria(categoria) {
        if (!window.confirm(t("repo.confirma_categoria", { nome: categoria.nome }))) return;

        await tentar(async () => {
            await api(`/categorias/${categoria.id}`, { metodo: "DELETE" });
            await carregarCategorias();
            await carregarArquivos();
        });
    }

    // Criar categoria
    formCategoria.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const criada = await tentar(async () => {
            await api(`/repositorios/${repositorioId}/categorias`, {
                metodo: "POST",
                corpo: { nome: campoCategoria.value.trim() },
            });
            await carregarCategorias();
            await carregarArquivos();
        });

        if (criada) campoCategoria.value = "";
    });

    // Membros (só em repositórios corporativos)
    function linhaDoMembro(membro) {
        const linha = document.createElement("tr");
        const tdPapel = document.createElement("td");
        const tdAcoes = document.createElement("td");

        const podeAlterar = souDono && membro.papel !== "dono";

        if (podeAlterar) {
            const seletor = document.createElement("select");
            seletor.className = "select-mini";
            seletor.setAttribute("aria-label", t("repo.papel_de", { nome: membro.nome }));
            seletor.append(opcao("editor", t("papel.editor")), opcao("leitor", t("papel.leitor")));
            seletor.value = membro.papel;

            seletor.addEventListener("change", async () => {
                const sucesso = await tentar(async () => {
                    await api(`/repositorios/${repositorioId}/membros`, {
                        metodo: "POST",
                        corpo: { email: membro.email, papel: seletor.value },
                    });
                });

                if (sucesso) {
                    membro.papel = seletor.value;
                } else {
                    seletor.value = membro.papel;
                }
            });

            tdPapel.appendChild(seletor);

            const acoes = document.createElement("div");
            acoes.className = "acoes";
            acoes.appendChild(botaoAcao(t("repo.remover"), () => removerMembro(membro), true));
            tdAcoes.appendChild(acoes);
        } else {
            tdPapel.textContent = t(`papel.${membro.papel}`);
        }

        linha.append(celula(membro.nome, "nome"), celula(membro.email), tdPapel, tdAcoes);
        return linha;
    }

    // Carrega e remove membros
    async function carregarMembros() {
        const membros = await api(`/repositorios/${repositorioId}/membros`);

        secaoMembros.hidden = false;
        formMembro.hidden = !souDono;
        corpoMembros.replaceChildren(...membros.map(linhaDoMembro));
    }

    async function removerMembro(membro) {
        if (!window.confirm(t("repo.confirma_membro", { nome: membro.nome }))) return;

        await tentar(async () => {
            await api(`/repositorios/${repositorioId}/membros/${membro.usuario_id}`, { metodo: "DELETE" });
            await carregarMembros();
        });
    }

    // Convidar membro
    formMembro.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const convidou = await tentar(async () => {
            await api(`/repositorios/${repositorioId}/membros`, {
                metodo: "POST",
                corpo: { email: campoMembroEmail.value.trim(), papel: campoMembroPapel.value },
            });
            await carregarMembros();
        });

        if (convidou) {
            campoMembroEmail.value = "";
            mostrarMensagem(mensagem, t("repo.membro_adicionado"), "sucesso");
        }
    });

    // Início: carrega o repositório e mostra tudo
    if (!repositorioId) {
        mostrarMensagem(mensagem, t("repo.nenhum_selecionado"));
        return;
    }

    await tentar(async () => {
        const repositorios = await api("/repositorios");
        repositorio = repositorios.find((r) => String(r.id) === String(repositorioId));

        if (!repositorio) {
            mostrarMensagem(mensagem, t("repo.nao_encontrado"));
            return;
        }

        titulo.textContent = repositorio.nome;
        papelEl.textContent = `(${t(`papel.${repositorio.papel}`)})`;
        podeEditar = repositorio.papel === "editor" || repositorio.papel === "dono";
        souDono = repositorio.papel === "dono";

        // Pasta pedida na URL (se não existir, começa na raiz)
        const pedida = Number(parametros.get("pasta")) || null;

        await carregarCategorias();
        listaPastas = caminhosDasPastas(await api(`/repositorios/${repositorioId}/pastas`));
        pastaPorId = Object.fromEntries(listaPastas.map((p) => [p.id, p]));
        pastaAtualId = pedida && pastaPorId[pedida] ? pedida : null;
        atualizarEndereco();

        await carregarArquivos();

        if (repositorio.tipo === "corporativo") {
            await carregarMembros();
        }
    });
});
