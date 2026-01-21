import streamlit as st
import google.generativeai as genai

# ----------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ----------------------------
st.set_page_config(page_title="NutriVendas", page_icon="📈", layout="wide")

# ----------------------------
# 2. ESTILO (CSS para ficar bonito)
# ----------------------------
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #EEEEEE !important; }
    .block-container { padding-top: 2rem; }
    
    /* Botão Principal */
    div.stButton > button {
        background-color: #800020;
        color: white;
        border: 1px solid #4a0012;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        transition: 0.2s;
        width: 100%;
        font-weight: 600;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #a30029;
        border-color: #ff0040;
    }
    
    /* Campos de Texto */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: white !important;
        border-radius: 10px !important;
        border: 1px solid #3a3a3a !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 3. SEGURANÇA & PAYWALL (Onde você ganha dinheiro)
# ----------------------------
def check_secrets():
    """Verifica se as chaves estão configuradas no Streamlit Cloud"""
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("⚠️ ERRO: Falta configurar a GOOGLE_API_KEY nos Secrets.")
        st.stop()
    if "ACCESS_PASSWORD" not in st.secrets:
        st.error("⚠️ ERRO: Falta configurar a ACCESS_PASSWORD nos Secrets.")
        st.stop()

def login_screen():
    """Tela de bloqueio simples"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    def check_password():
        if st.session_state.get("password_input") == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.authenticated = True
        else:
            st.error("🚫 Senha incorreta. Tente novamente.")

    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.title("🔒 NutriVendas")
            st.info("Acesso exclusivo para membros fundadores.")
            st.markdown("---")
            
            st.text_input("Digite sua Chave de Acesso:", type="password", key="password_input", on_change=check_password)
            
            st.markdown("### Não tem acesso?")
            # IMPORTANTE: TROQUE SEU NUMERO AQUI EMBAIXO 👇
            st.markdown("👉 [Clique aqui para comprar seu acesso vitalício](https://wa.me/5511999999999?text=Oi%20quero%20acesso%20ao%20NutriVendas)")
            st.stop()

# ----------------------------
# 4. INTELIGÊNCIA ARTIFICIAL (PROMPT)
# ----------------------------
def get_ai_content(nicho, tipo, preco, objetivo):
    prompt = f"""
    Você é um especialista em marketing e vendas para nutricionistas no Brasil.
    
    CONTEXTO DO CLIENTE:
    - Nicho: {nicho}
    - Atendimento: {tipo}
    - Preço da Consulta: {preco}
    - Objetivo Atual: {objetivo}
    
    Sua missão é gerar conteúdo prático que traga pacientes pagantes.
    
    REGRAS OBRIGATÓRIAS:
    - Use linguagem natural, humana e empática.
    - Foque na dor e no desejo do paciente.
    - NÃO use hashtags genéricas demais.
    - NÃO use termos técnicos de nutrição que ninguém entende.
    
    GERE O SEGUINTE CONTEÚDO (Separado por marcadores):
    
    [CONTEUDO]
    Crie 3 ideias de POSTS PARA O FEED com legenda completa e sugestão de imagem.
    Crie 3 ideias de STORIES para engajamento (com Enquete ou Caixinha).
    
    [VENDAS]
    Escreva um SCRIPT DE DIRECT (DM) para responder alguém que perguntou "como funciona?".
    Escreva um SCRIPT DE QUEBRA DE OBJEÇÃO para quem diz "tá caro".
    
    [BIO]
    Crie uma BIO otimizada para o perfil do Instagram (curta e direta).
    Crie uma frase curta para o link da bio (CTA).
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def split_text(text):
    """Separa o texto da IA nas abas corretas"""
    conteudo = text
    vendas = ""
    bio = ""
    
    if "[CONTEUDO]" in text:
        parts = text.split("[VENDAS]")
        conteudo = parts[0].replace("[CONTEUDO]", "").strip()
        if len(parts) > 1:
            sales_parts = parts[1].split("[BIO]")
            vendas = sales_parts[0].strip()
            if len(sales_parts) > 1:
                bio = sales_parts[1].strip()
    
    return conteudo, vendas, bio

# ----------------------------
# 5. EXECUÇÃO DO APP
# ----------------------------

# Verifica chaves e senha
check_secrets()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
login_screen()

# Se passou da senha, mostra o app:
st.title("📈 NutriVendas: Máquina de Clientes")
st.write("Preencha os dados abaixo e deixe a IA trabalhar.")
st.markdown("---")

# Layout de Colunas
left_col, right_col = st.columns([1, 2])

with left_col:
    st.header("1. Configuração")
    with st.form("nutri_form"):
        nicho = st.text_input("Seu Nicho (ex: Emagrecimento, Hipertrofia):", value="Emagrecimento")
        tipo = st.selectbox("Atendimento:", ["Online", "Presencial", "Híbrido"])
        preco = st.text_input("Valor da Consulta:", value="R$ 200")
        objetivo = st.selectbox("Objetivo:", ["Encher a Agenda", "Vender Consultas Online", "Captar Leads"])
        
        submitted = st.form_submit_button("🚀 GERAR ESTRATÉGIA")

with right_col:
    st.header("2. Resultado")
    
    if submitted:
        with st.spinner("🤖 A IA está analisando seu perfil e criando os textos..."):
            raw_text = get_ai_content(nicho, tipo, preco, objetivo)
            txt_conteudo, txt_vendas, txt_bio = split_text(raw_text)
            
            # Criação das Abas
            tab1, tab2, tab3 = st.tabs(["📲 Posts & Stories", "💰 Scripts de Venda", "🔗 Bio Perfeita"])
            
            with tab1:
                st.subheader("Conteúdo para Atrair")
                st.code(txt_conteudo, language="markdown")
            
            with tab2:
                st.subheader("Scripts para Fechar")
                st.code(txt_vendas, language="markdown")
                
            with tab3:
                st.subheader("Otimização do Perfil")
                st.code(txt_bio, language="markdown")
    
    else:
        st.info("👈 Preencha os dados ao lado e clique no botão para gerar.")