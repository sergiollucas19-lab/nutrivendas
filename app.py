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
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: white !important;
        border-radius: 10px !important;
        border: 1px solid #3a3a3a !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 3. SEGURANÇA & PAYWALL
# ----------------------------
def check_secrets():
    if "GOOGLE_API_KEY" not in st.secrets:
        st.error("⚠️ ERRO: Falta configurar a GOOGLE_API_KEY nos Secrets.")
        st.stop()
    if "ACCESS_PASSWORD" not in st.secrets:
        st.error("⚠️ ERRO: Falta configurar a ACCESS_PASSWORD nos Secrets.")
        st.stop()

def login_screen():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    def check_password():
        if st.session_state.get("password_input") == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.authenticated = True
        else:
            st.error("🚫 Senha incorreta.")

    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.title("🔒 NutriVendas")
            st.info("Acesso exclusivo para membros fundadores.")
            st.text_input("Digite sua Chave de Acesso:", type="password", key="password_input", on_change=check_password)
            st.stop()

# ----------------------------
# 4. INTELIGÊNCIA ARTIFICIAL (CORRIGIDA)
# ----------------------------
def get_ai_content(nicho, tipo, preco, objetivo):
    prompt = f"""
    Você é um especialista em marketing para nutricionistas.
    
    CLIENTE:
    - Nicho: {nicho}
    - Atendimento: {tipo}
    - Preço: {preco}
    - Objetivo: {objetivo}
    
    GERE O SEGUINTE (Separado por marcadores exatos):
    
    [CONTEUDO]
    3 ideias de POSTS (legenda + imagem sugerida).
    3 ideias de STORIES.
    
    [VENDAS]
    Script de DIRECT para "como funciona?".
    Script de QUEBRA DE OBJEÇÃO "tá caro".
    
    [BIO]
    Bio otimizada para Instagram.
    CTA para link.
    """
    
    try:
        # CORREÇÃO AQUI: Mudamos para gemini-pro que é mais estável
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"

def split_text(text):
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
# 5. EXECUÇÃO
# ----------------------------
check_secrets()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
login_screen()

st.title("📈 NutriVendas: Máquina de Clientes")
st.write("Preencha os dados abaixo e deixe a IA trabalhar.")

left_col, right_col = st.columns([1, 2])

with left_col:
    with st.form("nutri_form"):
        nicho = st.text_input("Seu Nicho:", value="Emagrecimento")
        tipo = st.selectbox("Atendimento:", ["Online", "Presencial"])
        preco = st.text_input("Valor:", value="R$ 200")
        objetivo = st.selectbox("Objetivo:", ["Encher a Agenda", "Vender Online"])
        submitted = st.form_submit_button("🚀 GERAR ESTRATÉGIA")

with right_col:
    if submitted:
        with st.spinner("🤖 Criando conteúdo..."):
            raw_text = get_ai_content(nicho, tipo, preco, objetivo)
            txt_conteudo, txt_vendas, txt_bio = split_text(raw_text)
            
            tab1, tab2, tab3 = st.tabs(["📲 Conteúdo", "💰 Vendas", "🔗 Bio"])
            with tab1: st.code(txt_conteudo, language="markdown")
            with tab2: st.code(txt_vendas, language="markdown")
            with tab3: st.code(txt_bio, language="markdown")