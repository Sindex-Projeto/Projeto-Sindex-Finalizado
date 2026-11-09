// Configurações (IA, tema e idioma) guardadas no navegador
const CONFIG_PADRAO = { ia_ativa: true, tema: "escuro", idioma: "pt-BR" };

const Config = {
    ler() {
        try {
            const salvo = JSON.parse(localStorage.getItem("sindex_config"));
            return { ...CONFIG_PADRAO, ...(salvo && typeof salvo === "object" ? salvo : {}) };
        } catch {
            return { ...CONFIG_PADRAO };
        }
    },

    gravarLocal(config) {
        const limpa = {
            ia_ativa: config.ia_ativa !== false,
            tema: config.tema === "claro" ? "claro" : "escuro",
            idioma: config.idioma === "en" ? "en" : "pt-BR",
        };

        try { localStorage.setItem("sindex_config", JSON.stringify(limpa)); } catch { }
        return limpa;
    },

    get tema() { return this.ler().tema; },
    get idioma() { return this.ler().idioma; },
    get iaAtiva() { return this.ler().ia_ativa; },

    get localeNavegador() { return this.idioma === "en" ? "en-US" : "pt-BR"; },

    aplicarTema() {
        document.documentElement.setAttribute("data-tema", this.tema);
    },
};

// Aplica o tema antes da página aparecer (evita piscar)
Config.aplicarTema();

// Textos da interface em português e inglês
const TEXTOS = {
    "pt-BR": {
        // Títulos das páginas
        "titulo.login": "Sindex - Login",
        "titulo.cadastro": "Sindex - Criar Conta",
        "titulo.upload": "Sindex - Upload",
        "titulo.repositorio": "Sindex - Repositório",

        // Textos usados em várias telas
        "comum.sair": "Sair",
        "comum.raiz": "Raiz",
        "comum.sem_categoria": "Sem categoria",
        "comum.arquivo_generico": "arquivo",
        "comum.erro_conexao": "Não foi possível conectar ao servidor.",
        "comum.erro_baixar": "Não foi possível baixar o arquivo.",
        "comum.erro_generico": "Erro inesperado no servidor.",
        "comum.sessao_expirada": "Sessão expirada. Entre novamente.",

        // Papéis no repositório
        "papel.dono": "Dono",
        "papel.editor": "Editor",
        "papel.leitor": "Leitor",

        // Modo (pessoal ou corporativo)
        "modo.pessoal": "Pessoal",
        "modo.corporativo": "Corporativo",

        // Situação do arquivo
        "status.pendente": "Aguardando leitura",
        "status.extraido": "Aguardando IA",
        "status.extraido_sem_ia": "Texto lido",
        "status.sem_texto": "Sem texto para ler",
        "status.falhou": "Falha na leitura",
        "status.processado": "Organizado",

        // Janela de configurações
        "config.botao": "Configurações",
        "config.titulo": "Configurações",
        "config.ia": "Inteligência artificial",
        "config.ia_dica": "Quando ligada, a IA (Google Gemini) sugere categorias e pastas para seus arquivos e permite buscar por significado; você escolhe aplicar ou não. Para isso, o texto dos arquivos é enviado ao Google. Desligada, você organiza tudo manualmente.",
        "config.tema": "Tema",
        "config.tema_escuro": "Escuro",
        "config.tema_claro": "Claro",
        "config.idioma": "Idioma",
        "config.fechar": "Fechar",
        "config.salvo": "Salvo.",
        "config.erro_salvar": "Não foi possível salvar na sua conta; a mudança vale só neste navegador.",

        // Tela de login
        "login.email": "E-mail",
        "login.senha": "Senha",
        "login.metodo": "Selecione o método de Login",
        "login.cadastrar": "Cadastrar",
        "login.entrar": "Login",

        // Tela de cadastro
        "cadastro.titulo": "Criar Conta",
        "cadastro.sub": "Preencha os dados abaixo para se cadastrar.",
        "cadastro.nome": "Nome completo",
        "cadastro.nome_ph": "Seu nome",
        "cadastro.email_ph": "seuemail@exemplo.com",
        "cadastro.senha": "Senha (mínimo 8 caracteres)",
        "cadastro.confirma": "Confirmar senha",
        "cadastro.botao": "Cadastrar",
        "cadastro.tem_conta": "Já possui uma conta?",
        "cadastro.fazer_login": "Fazer login",
        "cadastro.erro_curta": "A senha deve ter pelo menos 8 caracteres.",
        "cadastro.erro_diferente": "As senhas não são iguais.",
        "cadastro.sucesso": "Conta criada! Redirecionando para o login...",

        // Tela de upload
        "upload.modo": "Modo",
        "upload.repositorio": "Repositório",
        "upload.pasta": "Pasta de destino",
        "upload.pasta_raiz": "Raiz do repositório",
        "upload.criar_repo": "Criar repositório corporativo",
        "upload.repo_nome_ph": "Nome da empresa ou equipe",
        "upload.criar": "Criar",
        "upload.caixa": "Faça upload de arquivos",
        "upload.formatos": "PDF, TXT, MD, CSV, DOCX, imagens, MP4 e MOV",
        "upload.link_ph": "Ou cole um link (https://...)",
        "upload.adicionar": "Adicionar",
        "upload.ver_repo": "Ver Repositório",
        "upload.sem_repo_corp": "Você ainda não participa de nenhum repositório corporativo. Crie um abaixo ou peça um convite ao dono.",
        "upload.sem_repo": "Nenhum repositório encontrado.",
        "upload.somente_leitura": "Você tem acesso somente leitura a este repositório.",
        "upload.repo_criado": "Repositório \"{nome}\" criado. Use \"Ver Repositório\" para convidar membros.",
        "upload.enviando": "Enviando {n} arquivo(s)...",
        "upload.enviado": "✔ {nome} enviado",
        "upload.texto_lido": "{base} — texto lido",
        "upload.sem_texto": "{base} — sem texto para ler",
        "upload.leitura_falhou": "{base} — a leitura falhou: {motivo}",
        "upload.erro_desconhecido": "erro desconhecido",
        "upload.lendo_link": "Adicionando e lendo o link...",
        "upload.link_adicionado": "✔ Link adicionado: {nome}",

        // Tela do repositório
        "repo.titulo_padrao": "Repositório",
        "repo.enviar": "+ Enviar arquivos",
        "repo.trilha": "Caminho das pastas",
        "repo.nova_pasta_ph": "Nome da nova pasta",
        "repo.nova_pasta": "Nova pasta",
        "repo.busca_ph": "Buscar pelo nome (em todas as pastas)...",
        "repo.busca_aria": "Buscar arquivos pelo nome",
        "repo.filtro_aria": "Filtrar por categoria",
        "repo.aviso_busca": "Mostrando resultados de todas as pastas do repositório.",
        "repo.col_nome": "Nome",
        "repo.col_tipo": "Tipo",
        "repo.col_tamanho": "Tamanho",
        "repo.col_pasta": "Pasta",
        "repo.col_categoria": "Categoria",
        "repo.col_situacao": "Situação",
        "repo.col_data": "Enviado em",
        "repo.col_acoes": "Ações",
        "repo.vazio": "Nenhum arquivo neste repositório ainda.",
        "repo.vazio_busca": "Nenhum arquivo corresponde à busca.",
        "repo.vazio_pasta": "Nenhum arquivo nesta pasta.",
        "repo.categorias": "Categorias",
        "repo.sem_categorias": "Nenhuma categoria criada ainda.",
        "repo.categoria_ph": "Nova categoria (ex.: Ciências)",
        "repo.todas_categorias": "Todas as categorias",
        "repo.filtro_tipo_aria": "Filtrar por tipo",
        "repo.tipo_todos": "Arquivos e links",
        "repo.tipo_arquivos": "Só arquivos",
        "repo.tipo_links": "Só links",

        // IA: sugestões e busca por significado
        "ia.sugerir": "Sugerir com IA",
        "ia.sugerindo": "Pensando...",
        "ia.sugestao_titulo": "Sugestão da IA",
        "ia.categoria": "Categoria",
        "ia.pasta": "Pasta",
        "ia.nova": "nova",
        "ia.aplicar": "Aplicar",
        "ia.ignorar": "Ignorar",
        "ia.aplicada": "Sugestão aplicada.",
        "ia.aplicada_criou": "Sugestão aplicada. Criado: {itens}.",
        "ia.organizar_todos": "Organizar tudo com IA",
        "ia.aplicar_todas": "Aplicar todas ({n})",
        "ia.confirma_aplicar_todas": "Aplicar as sugestões pendentes ({n})? Categorias e pastas novas serão criadas.",
        "ia.progresso": "Analisando {atual} de {total}...",
        "ia.prontas": "Sugestões prontas: {n}. Revise e aplique.",
        "ia.prontas_restam": "Sugestões prontas: {n}. Arquivos restantes: {r} (clique de novo).",
        "ia.parou": "Parou. Sugestões criadas: {n}. Motivo: {motivo}",
        "ia.nada": "Nenhum arquivo com texto aguardando sugestão.",
        "ia.aplicadas": "Sugestões aplicadas: {n}.",
        "ia.busca_significado": "Por significado (IA)",
        "ia.busca_ph_significado": "Descreva o que procura (ex.: contrato de aluguel)...",
        "ia.aviso_significado": "Resultados por significado, do mais parecido ao menos.",
        "ia.nao_indexados": "Arquivos ainda não analisados pela busca: {n}. Pesquise de novo para incluí-los.",
        "ia.parecido": "{n}% parecido",
        "repo.membros": "Membros",
        "repo.col_email": "E-mail",
        "repo.col_papel": "Papel",
        "repo.membro_email_ph": "E-mail de quem já tem conta",
        "repo.convidar": "Convidar",
        "repo.dica_papeis": "Editor envia, move e exclui arquivos. Leitor só vê e baixa.",
        "repo.arquivo_um": "arquivo",
        "repo.arquivo_outro": "arquivos",
        "repo.subpasta_um": "subpasta",
        "repo.subpasta_outro": "subpastas",
        "repo.renomear": "Renomear",
        "repo.mover_para": "Mover para...",
        "repo.mover_aria": "Mover a pasta {nome}",
        "repo.excluir": "Excluir",
        "repo.novo_nome": "Novo nome da pasta:",
        "repo.confirma_pasta": "Apagar a pasta \"{nome}\"? Os arquivos e subpastas dentro dela NÃO são excluídos: sobem para a pasta de cima.",
        "repo.pasta_de": "Pasta de {nome}",
        "repo.categoria_de": "Categoria de {nome}",
        "repo.papel_de": "Papel de {nome}",
        "repo.em": "em {caminho}",
        "repo.na_raiz": "na raiz",
        "repo.tipo_link": "Link",
        "repo.abrir": "Abrir",
        "repo.baixar": "Baixar",
        "repo.ler_de_novo": "Ler de novo",
        "repo.remover": "Remover",
        "repo.confirma_arquivo": "Excluir \"{nome}\"? Esta ação não pode ser desfeita.",
        "repo.apagar_categoria_aria": "Apagar categoria {nome}",
        "repo.confirma_categoria": "Apagar a categoria \"{nome}\"? Os arquivos dela ficam sem categoria, nada é excluído.",
        "repo.confirma_membro": "Remover {nome} do repositório? Os arquivos enviados por essa pessoa continuam aqui.",
        "repo.membro_adicionado": "Membro adicionado.",
        "repo.nenhum_selecionado": "Nenhum repositório selecionado. Volte e escolha um.",
        "repo.nao_encontrado": "Repositório não encontrado.",
    },

    en: {
        // Títulos das páginas
        "titulo.login": "Sindex - Sign in",
        "titulo.cadastro": "Sindex - Create account",
        "titulo.upload": "Sindex - Upload",
        "titulo.repositorio": "Sindex - Repository",

        // Textos usados em várias telas
        "comum.sair": "Sign out",
        "comum.raiz": "Root",
        "comum.sem_categoria": "No category",
        "comum.arquivo_generico": "file",
        "comum.erro_conexao": "Could not connect to the server.",
        "comum.erro_baixar": "Could not download the file.",
        "comum.erro_generico": "Unexpected server error.",
        "comum.sessao_expirada": "Session expired. Please sign in again.",

        // Papéis no repositório
        "papel.dono": "Owner",
        "papel.editor": "Editor",
        "papel.leitor": "Reader",

        // Modo (pessoal ou corporativo)
        "modo.pessoal": "Personal",
        "modo.corporativo": "Corporate",

        // Situação do arquivo
        "status.pendente": "Waiting to be read",
        "status.extraido": "Waiting for AI",
        "status.extraido_sem_ia": "Text read",
        "status.sem_texto": "No text to read",
        "status.falhou": "Reading failed",
        "status.processado": "Organized",

        // Janela de configurações
        "config.botao": "Settings",
        "config.titulo": "Settings",
        "config.ia": "Artificial intelligence",
        "config.ia_dica": "When on, the AI (Google Gemini) suggests categories and folders for your files and lets you search by meaning; you choose whether to apply them. To do this, the text of your files is sent to Google. When off, you organize everything manually.",
        "config.tema": "Theme",
        "config.tema_escuro": "Dark",
        "config.tema_claro": "Light",
        "config.idioma": "Language",
        "config.fechar": "Close",
        "config.salvo": "Saved.",
        "config.erro_salvar": "Could not save to your account; the change only applies to this browser.",

        // Tela de login
        "login.email": "Email",
        "login.senha": "Password",
        "login.metodo": "Select the sign-in method",
        "login.cadastrar": "Sign up",
        "login.entrar": "Sign in",

        // Tela de cadastro
        "cadastro.titulo": "Create account",
        "cadastro.sub": "Fill in the details below to sign up.",
        "cadastro.nome": "Full name",
        "cadastro.nome_ph": "Your name",
        "cadastro.email_ph": "youremail@example.com",
        "cadastro.senha": "Password (at least 8 characters)",
        "cadastro.confirma": "Confirm password",
        "cadastro.botao": "Sign up",
        "cadastro.tem_conta": "Already have an account?",
        "cadastro.fazer_login": "Sign in",
        "cadastro.erro_curta": "The password must be at least 8 characters long.",
        "cadastro.erro_diferente": "The passwords do not match.",
        "cadastro.sucesso": "Account created! Redirecting to sign in...",

        // Tela de upload
        "upload.modo": "Mode",
        "upload.repositorio": "Repository",
        "upload.pasta": "Destination folder",
        "upload.pasta_raiz": "Repository root",
        "upload.criar_repo": "Create corporate repository",
        "upload.repo_nome_ph": "Company or team name",
        "upload.criar": "Create",
        "upload.caixa": "Upload files",
        "upload.formatos": "PDF, TXT, MD, CSV, DOCX, images, MP4 and MOV",
        "upload.link_ph": "Or paste a link (https://...)",
        "upload.adicionar": "Add",
        "upload.ver_repo": "View repository",
        "upload.sem_repo_corp": "You are not a member of any corporate repository yet. Create one below or ask the owner for an invitation.",
        "upload.sem_repo": "No repository found.",
        "upload.somente_leitura": "You have read-only access to this repository.",
        "upload.repo_criado": "Repository \"{nome}\" created. Use \"View repository\" to invite members.",
        "upload.enviando": "Uploading {n} file(s)...",
        "upload.enviado": "✔ {nome} uploaded",
        "upload.texto_lido": "{base} — text read",
        "upload.sem_texto": "{base} — no text to read",
        "upload.leitura_falhou": "{base} — reading failed: {motivo}",
        "upload.erro_desconhecido": "unknown error",
        "upload.lendo_link": "Adding and reading the link...",
        "upload.link_adicionado": "✔ Link added: {nome}",

        // Tela do repositório
        "repo.titulo_padrao": "Repository",
        "repo.enviar": "+ Upload files",
        "repo.trilha": "Folder path",
        "repo.nova_pasta_ph": "New folder name",
        "repo.nova_pasta": "New folder",
        "repo.busca_ph": "Search by name (in all folders)...",
        "repo.busca_aria": "Search files by name",
        "repo.filtro_aria": "Filter by category",
        "repo.aviso_busca": "Showing results from all folders in the repository.",
        "repo.col_nome": "Name",
        "repo.col_tipo": "Type",
        "repo.col_tamanho": "Size",
        "repo.col_pasta": "Folder",
        "repo.col_categoria": "Category",
        "repo.col_situacao": "Status",
        "repo.col_data": "Uploaded on",
        "repo.col_acoes": "Actions",
        "repo.vazio": "No files in this repository yet.",
        "repo.vazio_busca": "No files match your search.",
        "repo.vazio_pasta": "No files in this folder.",
        "repo.categorias": "Categories",
        "repo.sem_categorias": "No categories created yet.",
        "repo.categoria_ph": "New category (e.g. Science)",
        "repo.todas_categorias": "All categories",
        "repo.filtro_tipo_aria": "Filter by type",
        "repo.tipo_todos": "Files and links",
        "repo.tipo_arquivos": "Files only",
        "repo.tipo_links": "Links only",

        // AI: suggestions and search by meaning
        "ia.sugerir": "Suggest with AI",
        "ia.sugerindo": "Thinking...",
        "ia.sugestao_titulo": "AI suggestion",
        "ia.categoria": "Category",
        "ia.pasta": "Folder",
        "ia.nova": "new",
        "ia.aplicar": "Apply",
        "ia.ignorar": "Ignore",
        "ia.aplicada": "Suggestion applied.",
        "ia.aplicada_criou": "Suggestion applied. Created: {itens}.",
        "ia.organizar_todos": "Organize all with AI",
        "ia.aplicar_todas": "Apply all ({n})",
        "ia.confirma_aplicar_todas": "Apply the pending suggestions ({n})? New categories and folders will be created.",
        "ia.progresso": "Analyzing {atual} of {total}...",
        "ia.prontas": "Suggestions ready: {n}. Review and apply.",
        "ia.prontas_restam": "Suggestions ready: {n}. Files remaining: {r} (click again).",
        "ia.parou": "Stopped. Suggestions created: {n}. Reason: {motivo}",
        "ia.nada": "No files with text waiting for a suggestion.",
        "ia.aplicadas": "Suggestions applied: {n}.",
        "ia.busca_significado": "By meaning (AI)",
        "ia.busca_ph_significado": "Describe what you are looking for (e.g. rental contract)...",
        "ia.aviso_significado": "Results by meaning, from most to least similar.",
        "ia.nao_indexados": "Files not analyzed by search yet: {n}. Search again to include them.",
        "ia.parecido": "{n}% match",
        "repo.membros": "Members",
        "repo.col_email": "Email",
        "repo.col_papel": "Role",
        "repo.membro_email_ph": "Email of someone who already has an account",
        "repo.convidar": "Invite",
        "repo.dica_papeis": "Editors upload, move and delete files. Readers can only view and download.",
        "repo.arquivo_um": "file",
        "repo.arquivo_outro": "files",
        "repo.subpasta_um": "subfolder",
        "repo.subpasta_outro": "subfolders",
        "repo.renomear": "Rename",
        "repo.mover_para": "Move to...",
        "repo.mover_aria": "Move folder {nome}",
        "repo.excluir": "Delete",
        "repo.novo_nome": "New folder name:",
        "repo.confirma_pasta": "Delete the folder \"{nome}\"? The files and subfolders inside it are NOT deleted: they move up to the parent folder.",
        "repo.pasta_de": "Folder of {nome}",
        "repo.categoria_de": "Category of {nome}",
        "repo.papel_de": "Role of {nome}",
        "repo.em": "in {caminho}",
        "repo.na_raiz": "in the root",
        "repo.tipo_link": "Link",
        "repo.abrir": "Open",
        "repo.baixar": "Download",
        "repo.ler_de_novo": "Read again",
        "repo.remover": "Remove",
        "repo.confirma_arquivo": "Delete \"{nome}\"? This action cannot be undone.",
        "repo.apagar_categoria_aria": "Delete category {nome}",
        "repo.confirma_categoria": "Delete the category \"{nome}\"? Its files become uncategorized; nothing is deleted.",
        "repo.confirma_membro": "Remove {nome} from the repository? The files uploaded by this person stay here.",
        "repo.membro_adicionado": "Member added.",
        "repo.nenhum_selecionado": "No repository selected. Go back and choose one.",
        "repo.nao_encontrado": "Repository not found.",
    },
};

// Busca um texto pelo código e troca {nome} pelos valores
function t(chave, valores = {}) {
    const modelo = (TEXTOS[Config.idioma] || {})[chave] ?? TEXTOS["pt-BR"][chave] ?? chave;
    return modelo.replace(/\{(\w+)\}/g, (_, nome) => (nome in valores ? String(valores[nome]) : `{${nome}}`));
}

// Singular e plural ("1 arquivo", "2 arquivos")
function tPlural(base, n) {
    return `${n} ${t(`${base}_${n === 1 ? "um" : "outro"}`)}`;
}

// Mensagens do servidor (vêm em português) traduzidas para inglês
const ERROS_SERVIDOR_EN = {
    "A biblioteca pypdf não está instalada no servidor.": "The pypdf library is not installed on the server.",
    "A biblioteca python-docx não está instalada no servidor.": "The python-docx library is not installed on the server.",
    "A senha deve ter pelo menos 8 caracteres.": "The password must be at least 8 characters long.",
    "A senha pode ter no máximo 128 caracteres.": "The password can have at most 128 characters.",
    "Arquivo não encontrado.": "File not found.",
    "Categoria inválida.": "Invalid category.",
    "Categoria não encontrada.": "Category not found.",
    "Descrição inválida.": "Invalid description.",
    "E-mail inválido.": "Invalid email.",
    "E-mail já cadastrado.": "Email already registered.",
    "E-mail ou senha incorretos.": "Incorrect email or password.",
    "Envie os dados em formato JSON.": "Send the data as JSON.",
    "Erro inesperado ao ler o conteúdo.": "Unexpected error while reading the content.",
    "Esse endereço não é permitido (aponta para uma rede interna).": "This address is not allowed (it points to an internal network).",
    "Esse usuário não é membro do repositório.": "This user is not a member of the repository.",
    "Este link não é uma página de texto (pode ser um arquivo, imagem ou vídeo).": "This link is not a text page (it may be a file, image or video).",
    "Este tipo de arquivo ainda não tem leitura de texto.": "Text reading is not available for this file type yet.",
    "Faça login para continuar.": "Sign in to continue.",
    "Idioma inválido.": "Invalid language.",
    "Informe e-mail e senha.": "Enter your email and password.",
    "Informe o e-mail do membro.": "Enter the member's email.",
    "Informe o endereço do link.": "Enter the link address.",
    "Informe o nome da categoria.": "Enter the category name.",
    "Informe o nome da pasta.": "Enter the folder name.",
    "Informe o nome do repositório.": "Enter the repository name.",
    "Informe um link válido, começando com http:// ou https://.": "Enter a valid link starting with http:// or https://.",
    "Já existe uma categoria com esse nome.": "A category with this name already exists.",
    "Já existe uma pasta com esse nome aqui.": "A folder with this name already exists here.",
    "Já existe uma pasta com esse nome no destino.": "A folder with this name already exists at the destination.",
    "Links com usuário e senha não são permitidos.": "Links with a username and password are not allowed.",
    "Links não têm arquivo para baixar.": "Links have no file to download.",
    "Método de login inválido.": "Invalid sign-in method.",
    "Nenhum arquivo enviado.": "No file was sent.",
    "Nenhum texto encontrado (pode ser um documento escaneado, só com imagens).": "No text found (it may be a scanned document with only images).",
    "Nenhum usuário encontrado com esse e-mail.": "No user found with this email.",
    "Nome inválido.": "Invalid name.",
    "Não dá para mover uma pasta para dentro dela mesma.": "A folder cannot be moved into itself.",
    "Não foi possível abrir o arquivo.": "Could not open the file.",
    "Não foi possível acessar o site (sem resposta ou conexão recusada).": "Could not reach the site (no response or connection refused).",
    "Não foi possível encontrar esse endereço na internet.": "Could not find this address on the internet.",
    "Não foi possível interpretar a página.": "Could not interpret the page.",
    "Não foi possível ler o PDF (arquivo corrompido ou em formato inesperado).": "Could not read the PDF (corrupted file or unexpected format).",
    "Não foi possível ler o documento (arquivo corrompido ou em formato inesperado).": "Could not read the document (corrupted file or unexpected format).",
    "Não foi possível salvar o arquivo.": "Could not save the file.",
    "O arquivo não está mais disponível no servidor.": "The file is no longer available on the server.",
    "O campo ia_ativa deve ser verdadeiro ou falso.": "The ia_ativa field must be true or false.",
    "O documento é grande demais para ser lido.": "The document is too large to be read.",
    "O dono do repositório não pode ser removido.": "The repository owner cannot be removed.",
    "O dono do repositório não pode ter o papel alterado.": "The repository owner's role cannot be changed.",
    "O link precisa começar com http:// ou https://.": "The link must start with http:// or https://.",
    "O link tem redirecionamentos demais.": "The link has too many redirects.",
    "O link tem uma porta inválida.": "The link has an invalid port.",
    "O link é grande demais.": "The link is too long.",
    "O nome da pasta não pode ter barras (/ ou \\).": "The folder name cannot contain slashes (/ or \\).",
    "O nome da pasta pode ter no máximo 100 caracteres.": "The folder name can have at most 100 characters.",
    "O nome pode ter no máximo 100 caracteres.": "The name can have at most 100 characters.",
    "O papel deve ser 'editor' ou 'leitor'.": "The role must be 'editor' or 'leitor' (reader).",
    "O site demorou demais para responder.": "The site took too long to respond.",
    "O site redirecionou sem informar para onde.": "The site redirected without saying where to.",
    "PDF protegido por senha.": "Password-protected PDF.",
    "Pasta inválida.": "Invalid folder.",
    "Pasta não encontrada.": "Folder not found.",
    "Preencha todos os campos.": "Fill in all fields.",
    "Repositório não encontrado.": "Repository not found.",
    "Repositórios pessoais não têm outros membros.": "Personal repositories have no other members.",
    "Sessão expirada. Entre novamente.": "Session expired. Please sign in again.",
    "Sessão inválida. Entre novamente.": "Invalid session. Please sign in again.",
    "Só são aceitos links nas portas padrão (80 e 443).": "Only links on the standard ports (80 and 443) are accepted.",
    "Tema inválido.": "Invalid theme.",
    "Tipo inválido.": "Invalid type.",
    "A IA está desativada nas suas configurações.": "AI is turned off in your settings.",
    "A IA não está configurada no servidor.": "AI is not configured on the server.",
    "Este arquivo não tem texto para a IA analisar.": "This file has no text for the AI to analyze.",
    "A IA não conseguiu sugerir uma organização para este arquivo.": "The AI could not suggest an organization for this file.",
    "A IA não conseguiu analisar este arquivo.": "The AI could not analyze this file.",
    "Não foi possível falar com a IA. Tente de novo.": "Could not reach the AI. Try again.",
    "A IA devolveu uma resposta inválida.": "The AI returned an invalid response.",
    "A chave da IA é inválida ou sem permissão.": "The AI key is invalid or lacks permission.",
    "Modelo de IA não encontrado. Ajuste GEMINI_MODELO.": "AI model not found. Adjust GEMINI_MODELO.",
    "O limite gratuito da IA foi atingido. Tente mais tarde.": "The free AI limit was reached. Try again later.",
    "A IA está indisponível no momento. Tente de novo.": "The AI is unavailable right now. Try again.",
    "Não há sugestão para este arquivo.": "There is no suggestion for this file.",
    "Não foi possível aplicar: já existe um item com esse nome.": "Could not apply: an item with that name already exists.",
    "Digite o que você procura.": "Type what you are looking for.",
    "A busca pode ter no máximo 200 caracteres.": "The search can have at most 200 characters.",
    "Situação inválida.": "Invalid status.",
    "A busca pode ter no máximo 100 caracteres.": "The search can have at most 100 characters.",
    "Tipo de arquivo não permitido.": "File type not allowed.",
    "Tipo de repositório inválido.": "Invalid repository type.",
    "Título inválido.": "Invalid title.",
    "Usuário não encontrado.": "User not found.",
    "Você ainda não participa de nenhum repositório corporativo.": "You are not a member of any corporate repository yet.",
    "Você não tem permissão para esta ação.": "You do not have permission for this action.",
};

// Mensagens com números no meio
const ERROS_SERVIDOR_EN_PADROES = [
    [/^Muitas tentativas de login\. Tente novamente em (\d+) minuto\(s\)\.$/, "Too many sign-in attempts. Try again in $1 minute(s)."],
    [/^O envio passou do limite de (\d+) MB\.$/, "The upload exceeded the limit of $1 MB."],
    [/^O limite é de (\d+) níveis de pastas\.$/, "The limit is $1 folder levels."],
    [/^O site respondeu com erro (\d+)\.$/, "The site responded with error $1."],
];

// Traduz uma mensagem do servidor (se não achar, mostra como veio)
function traduzirServidor(mensagem) {
    if (Config.idioma !== "en" || typeof mensagem !== "string") return mensagem;

    if (ERROS_SERVIDOR_EN[mensagem]) return ERROS_SERVIDOR_EN[mensagem];

    for (const [padrao, troca] of ERROS_SERVIDOR_EN_PADROES) {
        if (padrao.test(mensagem)) return mensagem.replace(padrao, troca);
    }

    return mensagem;
}

// Aplica as traduções nos elementos com data-i18n
function traduzirPagina(raiz = document) {
    document.documentElement.lang = Config.idioma;

    raiz.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    raiz.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    raiz.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
}

// Traduz o HTML assim que a página carrega
document.addEventListener("DOMContentLoaded", () => traduzirPagina());
