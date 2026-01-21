import streamlit as st
import requests
import json

# --- 1. CONFIGURAÇÃO OBRIGATÓRIA (PRIMEIRA LINHA) ---
st.set_page_config(page_title="NutriVendas", page_icon="⚡", layout="wide")

# --- 2. VERIFICAÇÃO DE SEGURANÇA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Configure a GOOGLE_API_KEY nos Secrets!")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ Configure a ACCESS_PASSWORD nos Secrets!")
    st.stop()

# --- 3. FUNÇÃO DE CONEXÃO ---
def gerar_conteudo(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Aja como especialista em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Crie 3 seções separadas por marcadores EXATOS:
    
    [CONTEUDO]
    - 3 Ideias de Posts (Título + Legenda)
    
    [VENDAS]
    - 1 Script de Direct
    - 1 Script de Objeção
    
    [BIO]
    - Bio otimizada + Link
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Erro Google: {response.text}"
    except Exception as e:
        return f"Erro Conexão: {e}"

def separar_texto(text):
    c, v, b = text, "...", "..."
    if "[CONTEUDO]" in text:
        p = text.split("[VENDAS]")
        c = p[0].replace("[CONTEUDO]", "").strip()
        if len(p) > 1:
            p2 = p[1].split("[BIO]")
            v = p2[0].strip()
            if len(p2) > 1: b = p2[1].strip()
    return c, v, b

# --- 4. LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    st.stop()

# --- 5. APP ---
st.title("⚡ NutriVendas 2.5")
st.info("Sistema Online e Operante") # Aviso visual que carregou

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR")

with c2:
    if btn:
        with st.spinner("Gerando..."):
            res = gerar_conteudo(nicho, tipo, preco, obj)
            if "Erro" in res:
                st.error(res)
            else:
                c, v, b = separar_texto(res)
                t1, t2, t3 = st.tabs(["Conteúdo", "Vendas", "Bio"])
                t1.markdown(c)
                t2.markdown(v)
                t3.markdown(b)