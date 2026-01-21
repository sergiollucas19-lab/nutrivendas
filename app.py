import streamlit as st
import google.generativeai as genai

# ----------------------------
# CONFIGURAÇÃO INICIAL
# ----------------------------
st.set_page_config(page_title="NutriVendas", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #EEEEEE !important; }
    div.stButton > button {
        background-color: #800020; color: white; border-radius: 10px; width: 100%;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important; color: white !important; border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# SEGURANÇA
# ----------------------------
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configure a GOOGLE_API_KEY nos Secrets!")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ Configure a ACCESS_PASSWORD nos Secrets!")
    st.stop()

# Configura a chave aqui, uma única vez
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def login():
    if "auth" not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        pwd = st.text_input("🔒 Senha de Acesso:", type="password")
        if pwd == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        elif pwd:
            st.error("Senha incorreta.")
        st.stop()

# ----------------------------
# FUNÇÃO INTELIGENTE (MODEL HUNTER)
# ----------------------------
def obter_modelo_disponivel():
    """
    Procura automaticamente um modelo válido para não dar erro 404.
    Tenta o Flash primeiro (mais rápido), depois o Pro, depois qualquer um.
    """
    try:
        # Tenta listar os modelos disponíveis na sua conta
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name # Prioridade: Flash
        
        # Se não achou flash, pega o primeiro que gera texto
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
                
    except Exception:
        pass
    
    # Se tudo falhar, chuta o padrão atual
    return 'gemini-1.5-flash'

# ----------------------------
# IA E PROMPTS
# ----------------------------
def gerar_estrategia(nicho, tipo, preco, objetivo):
    model_name = obter_modelo_disponivel()
    # Mostra qual modelo foi escolhido (pra gente saber se deu certo)
    print(f"Modelo escolhido: {model_name}") 
    
    prompt = f"""
    Você é especialista em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Crie separadamente:
    [CONTEUDO] 3 ideias de posts (Legenda + Imagem).
    [VENDAS] Script de Direct para interessados.
    [BIO] Bio do Instagram + CTA.
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erro na IA ({model_name}): {e}"

def separar_texto(text):
    c, v, b = text, "", ""
    if "[CONTEUDO]" in text:
        p = text.split("[VENDAS]")
        c = p[0].replace("[CONTEUDO]", "").strip()
        if len(p) > 1:
            p2 = p[1].split("[BIO]")
            v = p2[0].strip()
            if len(p2) > 1: b = p2[1].strip()
    return c, v, b

# ----------------------------
# INTERFACE
# ----------------------------
login()

st.title("📈 NutriVendas: Gerador Automático")

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("form"):
        nicho = st.text_input("Nicho:", "Emagrecimento")
        tipo = st.selectbox("Tipo:", ["Online", "Presencial"])
        preco = st.text_input("Preço:", "R$ 200")
        obj = st.selectbox("Meta:", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("🚀 GERAR")

with c2:
    if btn:
        with st.spinner("🤖 A IA está escolhendo o melhor modelo e gerando..."):
            raw = gerar_estrategia(nicho, tipo, preco, obj)
            tc, tv, tb = separar_texto(raw)
            
            t1, t2, t3 = st.tabs(["Conteúdo", "Vendas", "Bio"])
            t1.markdown(tc)
            t2.markdown(tv)
            t3.markdown(tb)