import streamlit as st
import requests
import json

# 1. Configuração
st.set_page_config(page_title="NutriVendas 2.0", page_icon="🚀", layout="wide")

# 2. CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    div.stButton > button { background-color: #008000; color: white; font-weight: bold; }
    input, select, textarea { background-color: #262730 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 3. Função IA (Agora usando GEMINI 2.0 FLASH)
def chamar_ia(nicho, tipo, preco, objetivo):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Falta configurar GOOGLE_API_KEY"
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # MUDANÇA AQUI: Trocamos 2.5 por 2.0 para fugir do limite
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    prompt = f"""
    Crie conteúdo de marketing para nutricionista.
    Nicho: {nicho}. Tipo: {tipo}. Valor: {preco}. Meta: {objetivo}.
    
    SEPARE O TEXTO EXATAMENTE ASSIM:
    
    [PARTE1]
    3 Ideias de Posts (Título e Legenda)
    
    [PARTE2]
    Script de Vendas para Direct e Quebra de Objeção
    
    [PARTE3]
    Bio do Instagram Otimizada
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "⚠️ Limite diário atingido! Tente novamente amanhã ou crie uma nova chave API no Google."
        else:
            return f"ERRO GOOGLE: {response.text}"
    except Exception as e:
        return f"ERRO CONEXÃO: {e}"

# 4. Login
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 NutriVendas")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if "ACCESS_PASSWORD" in st.secrets and senha == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha Incorreta")
    st.stop()

# 5. Interface
st.title("🚀 NutriVendas: Versão 2.0")

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("meu_form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Tipo", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Meta", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR CONTEÚDO")

with col2:
    if btn:
        with st.spinner("🤖 A IA está escrevendo (Motor 2.0)..."):
            texto = chamar_ia(nicho, tipo, preco, obj)
            
            p1, p2, p3 = texto, "...", "..."
            
            if "[PARTE1]" in texto:
                partes = texto.split("[PARTE2]")
                p1 = partes[0].replace("[PARTE1]", "").strip()
                if len(partes) > 1:
                    resto = partes[1].split("[PARTE3]")
                    p2 = resto[0].strip()
                    if len(resto) > 1:
                        p3 = resto[1].strip()
            
            aba1, aba2, aba3 = st.tabs(["📝 Posts", "💬 Scripts", "🔗 Bio"])
            aba1.markdown(p1)
            aba2.markdown(p2)
            aba3.markdown(p3)