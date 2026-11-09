document.addEventListener("DOMContentLoaded", () => {
    // Botão de configurações
    const barra = document.querySelector(".lang-selector");
    if (!barra) return;

    const logado = Boolean(Sessao.token);

    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "link-btn";
    botao.id = "btnConfig";

    const icone = document.createElement("span");
    icone.setAttribute("aria-hidden", "true");
    icone.textContent = "⚙ ";

    const rotulo = document.createElement("span");
    rotulo.dataset.i18n = "config.botao";
    rotulo.textContent = t("config.botao");

    botao.append(icone, rotulo);
    barra.prepend(botao);

    // Janela de configurações
    const janela = document.createElement("dialog");
    janela.className = "modal";
    janela.setAttribute("aria-labelledby", "config-titulo");

    janela.innerHTML = `
      <h2 id="config-titulo" data-i18n="config.titulo"></h2>

      <div class="config-linha" id="linha-ia">
        <label class="config-switch">
          <input type="checkbox" id="config-ia" role="switch">
          <span data-i18n="config.ia"></span>
        </label>
        <p class="dica" data-i18n="config.ia_dica"></p>
      </div>

      <div class="config-linha">
        <label for="config-tema" data-i18n="config.tema"></label>
        <select id="config-tema" class="select-field">
          <option value="escuro" data-i18n="config.tema_escuro"></option>
          <option value="claro" data-i18n="config.tema_claro"></option>
        </select>
      </div>

      <div class="config-linha">
        <label for="config-idioma" data-i18n="config.idioma"></label>
        <select id="config-idioma" class="select-field">
          <option value="pt-BR">Português (Brasil)</option>
          <option value="en">English</option>
        </select>
      </div>

      <p id="config-aviso" class="mensagem" role="status" hidden></p>

      <div class="config-rodape">
        <button type="button" id="config-fechar" class="btn" data-i18n="config.fechar"></button>
      </div>
    `;

    document.body.appendChild(janela);
    traduzirPagina(janela);

    // Campos da janela
    const campoIa = janela.querySelector("#config-ia");
    const campoTema = janela.querySelector("#config-tema");
    const campoIdioma = janela.querySelector("#config-idioma");
    const aviso = janela.querySelector("#config-aviso");

    janela.querySelector("#linha-ia").hidden = !logado;

    // Mostra os valores atuais
    function mostrarValores() {
        const config = Config.ler();
        campoIa.checked = config.ia_ativa;
        campoTema.value = config.tema;
        campoIdioma.value = config.idioma;
    }

    // Salva a mudança (no navegador e na conta)
    async function salvar(parcial) {
        const antes = Config.ler();
        const nova = Config.gravarLocal({ ...antes, ...parcial });

        Config.aplicarTema();
        limparMensagem(aviso);

        if (logado) {
            try {
                await api("/usuarios/me/config", { metodo: "PATCH", corpo: parcial });
            } catch (erro) {
                mostrarMensagem(aviso, t("config.erro_salvar"));
            }
        }

        if (nova.idioma !== antes.idioma) {
            window.location.reload();
        } else if (aviso.hidden) {
            document.dispatchEvent(new CustomEvent("sindex:config"));
        }
    }

    // Quando o usuário muda uma opção
    campoIa.addEventListener("change", () => salvar({ ia_ativa: campoIa.checked }));
    campoTema.addEventListener("change", () => salvar({ tema: campoTema.value }));
    campoIdioma.addEventListener("change", () => salvar({ idioma: campoIdioma.value }));

    // Abrir e fechar a janela
    botao.addEventListener("click", () => {
        mostrarValores();
        limparMensagem(aviso);
        janela.showModal();
    });

    janela.querySelector("#config-fechar").addEventListener("click", () => janela.close());

    janela.addEventListener("click", (evento) => {
        if (evento.target === janela) janela.close();
    });

    // Traz as configurações da conta (se mudou em outro computador)
    if (logado) {
        api("/usuarios/me").then((usuario) => {
            if (!usuario || !usuario.config) return;

            const local = Config.ler();
            const remota = Config.gravarLocal(usuario.config);

            Config.aplicarTema();

            if (remota.idioma !== local.idioma) {
                window.location.reload();
            } else if (remota.ia_ativa !== local.ia_ativa) {
                document.dispatchEvent(new CustomEvent("sindex:config"));
            }
        }).catch(() => { });
    }
});
