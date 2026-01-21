import streamlit as st
import requests
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="NutriVendas 2.5", page_icon="⚡", layout="wide")

# --- ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    div.stButton > button { background-color: #008000; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    input, select, textarea { background-color: #262730 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- SEGURANÇA ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ Falta GOOGLE_API_KEY")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ Falta ACCESS_PASSWORD")
    st.stop()

# --- FUNÇÃO (Gemini 2.5 Flash) ---
def gerar_conteudo(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Prompt ajustado para evitar confusão
    prompt = f"""
    Aja como especialista em marketing para Nutricionistas.
    Dados: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
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
            dados = response.json()
            if "candidates" in dados and len(dados["candidates"]) > 0:
                parts = dados["candidates"][0]["content"]["parts"]
                if len(parts) > 0:
                    return parts[0]["text"]
            return "FALHA: A IA respondeu vazio."
        else:
            return f"FALHA: Google Status {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"FALHA: Conexão {str(e)}"

def separar_texto(text):
    c, v, b = text, "", ""
    # Se tiver falha real de conexão
    if text.startswith("FALHA:"):
        return text, "", ""
        
    if "[CONTEUDO]" in text:
        p = text.split("[VENDAS]")
        c = p[0].replace("[CONTEUDO]", "").strip()
        if len(p) > 1:
            p2 = p[1].split("[BIO]")
            v = p2[0].strip()
            if len(p2) > 1: b = p2[1].strip()
    return c, v, b

# --- LOGIN ---
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

# --- APP PRINCIPAL ---
st.title("⚡ NutriVendas Oficial")

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("form"):
        nicho = st.text_input("Nicho", "Hipertrofia")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR AGORA")

with c2:
    if btn:
        with st.spinner("🤖 Consultando IA..."):
            res = gerar_conteudo(nicho, tipo, preco, obj)
            
            # MUDANÇA: Só dá erro se começar com a palavra FALHA
            if res.startswith("FALHA:"):
                st.error(res)
            else:
                c, v, b = separar_texto(res)
                
                t1, t2, t3 = st.tabs(["📲 Conteúdo", "💰 Scripts", "🔗 Bio"])
                t1.markdown(c)
                t2.markdown(v)
                t3.markdown(b)