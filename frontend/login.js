document.addEventListener("DOMContentLoaded", () => {
    // Elementos da tela
    const formulario = document.getElementById("loginForm");
    const botaoLogin = document.getElementById("loginButton");
    const botaoCadastrar = document.getElementById("btnCadastrar");
    const mensagem = document.getElementById("mensagem");

    // Ir para o cadastro
    botaoCadastrar.addEventListener("click", () => {
        window.location.href = "cadastro.html";
    });

    // Login
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        limparMensagem(mensagem);

        const email = document.getElementById("login").value.trim();
        const senha = document.getElementById("senha").value;
        const metodo = document.getElementById("metodo").value;

        botaoLogin.disabled = true;

        try {
            const dados = await api("/usuarios/login", {
                metodo: "POST",
                publico: true,
                corpo: { email, senha, metodo },
            });

            // Deu certo: guarda o login e vai para o upload
            Sessao.iniciar(dados.token, dados.usuario, dados.metodo);
            window.location.href = "upload.html";
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
            botaoLogin.disabled = false;
        }
    });
});
