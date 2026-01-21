import streamlit as st
import requests
import json

# ----------------------------
# 1. CONFIGURAÇÃO VISUAL
# ----------------------------
st.set_page_config(page_title="NutriVendas", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    h1, h2, h3, h4 { color: #EEEEEE !important; }
    div.stButton > button {
        background-color: #008000; color: white; border-radius: 8px; width: 100%; font-weight: bold;
    }
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: #262730 !important; color: white !important; border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# 2. SEGURANÇA (SECRETS)
# ----------------------------
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configure a GOOGLE_API_KEY nos Secrets!")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ Configure a ACCESS_PASSWORD nos Secrets!")
    st.stop()

# ----------------------------
# 3. FUNÇÃO DE CONEXÃO DIRETA
# ----------------------------
def chamar_ia_direto(nicho, tipo, preco, objetivo):
    # Conexão direta com o Google (Ignora erros de biblioteca)
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Aja como especialista em marketing para Nutricionistas.
    Dados: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Crie 3 seções separadas por marcadores EXATOS:
    
    [CONTEUDO]
    - 3 Ideias de Posts (Título + Legenda)
    - 3 Ideias de Stories
    
    [VENDAS]
    - Script de resposta para "Como funciona?"
    - Script para objeção "Tá caro"
    
    [BIO]
    - Bio otimizada
    - Frase para Link
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            resultado = response.json()
            # Pega o texto da resposta
            try:
                texto_final = resultado['candidates'][0]['content']['parts'][0]['text']
                return texto_final
            except:
                return "Erro ao ler resposta da IA. Tente novamente."
        else:
            return f"Erro no Google (Status {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"Erro de conexão: {e}"

def separar_texto(text):
    c, v, b = text, "", ""
    if "[CONTEUDO]" in text:
        parts = text.split("[VENDAS]")
        c = parts[0].replace("[CONTEUDO]", "").strip()
        if len(parts) > 1:
            sales_parts = parts[1].split("[BIO]")
            v = sales_parts[0].strip()
            if len(sales_parts) > 1:
                b = sales_parts[1].strip()
    return c, v, b

# ----------------------------
# 4. TELA DE LOGIN
# ----------------------------
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Login NutriVendas")
        pwd = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            if pwd == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# ----------------------------
# 5. O APP PRINCIPAL
# ----------------------------
st.title("🚀 NutriVendas: Modo Turbo")
st.write("Sistema de Marketing Automático")

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("main_form"):
        st.subheader("Dados do Nutri")
        nicho = st.text_input("Nicho:", "Emagrecimento")
        tipo = st.selectbox("Atendimento:", ["Online", "Presencial"])
        preco = st.text_input("Preço Consulta:", "R$ 200")
        obj = st.selectbox("Objetivo:", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR AGORA ⚡")

with col2:
    if btn:
        with st.spinner("Conectando direto no cérebro da IA..."):
            texto_bruto = chamar_ia_direto(nicho, tipo, preco, obj)
            
            if "Erro" in texto_bruto:
                st.error(texto_bruto)
            else:
                conteudo, vendas, bio = separar_texto(texto_bruto)
                
                t1, t2, t3 = st.tabs(["📲 Conteúdo", "💰 Scripts", "🔗 Bio"])
                t1.markdown(conteudo)
                t2.markdown(vendas)
                t3.markdown(bio)