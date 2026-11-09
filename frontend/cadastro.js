document.addEventListener("DOMContentLoaded", () => {
    // Elementos da tela
    const formulario = document.getElementById("cadastro-form");
    const botao = document.getElementById("btnCadastro");
    const mensagem = document.getElementById("mensagem");

    // Cadastro
    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        limparMensagem(mensagem);

        const nome = document.getElementById("nome").value.trim();
        const email = document.getElementById("email").value.trim();
        const senha = document.getElementById("senha").value;
        const confirmaSenha = document.getElementById("confirma-senha").value;

        // Confere a senha antes de enviar
        if (senha.length < 8) {
            mostrarMensagem(mensagem, t("cadastro.erro_curta"));
            return;
        }

        if (senha !== confirmaSenha) {
            mostrarMensagem(mensagem, t("cadastro.erro_diferente"));
            return;
        }

        botao.disabled = true;

        try {
            // Cria a conta e volta para o login
            await api("/usuarios", {
                metodo: "POST",
                publico: true,
                corpo: { nome, email, senha },
            });

            mostrarMensagem(mensagem, t("cadastro.sucesso"), "sucesso");
            formulario.reset();

            setTimeout(() => {
                window.location.href = "index.html";
            }, 1200);
        } catch (erro) {
            mostrarMensagem(mensagem, erro.message);
            botao.disabled = false;
        }
    });
});
