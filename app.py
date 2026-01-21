import streamlit as st
import requests
import json

# 1. CONFIGURAÇÃO (Obrigatório ser a primeira linha do Streamlit)
st.set_page_config(page_title="NutriVendas 2.5", page_icon="⚡", layout="wide")

# 2. ESTILO
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    div.stButton > button { background-color: #008000; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    input, select, textarea { background-color: #262730 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 3. VERIFICAÇÃO DE SEGURANÇA
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configure a GOOGLE_API_KEY nos Secrets!")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ Configure a ACCESS_PASSWORD nos Secrets!")
    st.stop()

# 4. FUNÇÃO DO CÉREBRO (Conexão Direta Gemini 2.5)
def gerar_conteudo(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # URL Direta para o modelo que confirmamos que você tem
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Aja como especialista em marketing para Nutricionistas.
    Dados: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Crie 3 seções separadas por marcadores EXATOS:
    
    [CONTEUDO]
    - 3 Ideias de Posts (Título + Legenda)
    
    [VENDAS]
    - Script de resposta para "Como funciona?"
    - Script para objeção "Tá caro"
    
    [BIO]
    - Bio otimizada
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Erro Google: {response.text}"
    except Exception as e:
        return f"Erro Conexão: {e}"

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

# 5. TELA DE LOGIN
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    st.stop()

# 6. APP PRINCIPAL
st.title("⚡ NutriVendas: Gemini 2.5 Turbo")

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with c2:
    if btn:
        with st.spinner("Conectando ao Gemini 2.5..."):
            res = gerar_conteudo(nicho, tipo, preco, obj)
            if "Erro" in res:
                st.error(res)
            else:
                c, v, b = separar_texto(res)
                t1, t2, t3 = st.tabs(["Conteúdo", "Vendas", "Bio"])
                t1.markdown(c)
                t2.markdown(v)
                t3.markdown(b)