import streamlit as st
import requests
import json

# 1. Configuração (Simples e Leve)
st.set_page_config(page_title="NutriVendas Cofre", page_icon="🔐", layout="wide")

# 2. Menu Lateral
with st.sidebar:
    st.header("⚙️ Motor VIP")
    # Mantendo o 2.5 que é o melhor
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.success("Modo Seguro Ativo")

# 3. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Falta API Key."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    # Prompt pedindo texto limpo
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: Não use Markdown, Tabelas ou LaTeX.
    
    Estrutura Obrigatória:
    [PARTE1] 3 Posts (Título e Legenda)
    [PARTE2] Scripts de Vendas
    [PARTE3] Bio do Instagram
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"ERRO GOOGLE: {response.text}"
    except Exception as e:
        return f"ERRO CONEXÃO: {e}"

# 4. Função de Lavagem Química (Remove o veneno do texto)
def lavar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    # Substitui o Cifrão ($) por " reais " para não ativar matemática
    texto = texto.replace("$", " reais ")
    # Substitui porcentagem solta
    texto = texto.replace("%", " porcento ")
    return texto

# 5. Login
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔒 Login")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
    st.stop()

# 6. Interface Principal
st.title("🔐 NutriVendas: Modo Cofre")
st.warning("Usando visualização de código para blindagem total contra erros.")

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR BLINDADO")

with col2:
    if btn:
        with st.spinner("Gerando texto seguro..."):
            texto_bruto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            
            # AQUI A MÁGICA: Limpa os símbolos antes de qualquer coisa
            texto = lavar_texto(texto_bruto)
            
            if "ERRO" in texto:
                st.error(texto)
            else:
                p1, p2, p3 = texto, "...", "..."
                if "[PARTE1]" in texto:
                    try:
                        partes = texto.split("[PARTE2]")
                        p1 = partes[0].replace("[PARTE1]", "").strip()
                        if len(partes) > 1:
                            resto = partes[1].split("[PARTE3]")
                            p2 = resto[0].strip()
                            if len(resto) > 1:
                                p3 = resto[1].strip()
                    except: pass
                
                # VISUALIZAÇÃO DE CÓDIGO (Anti-Crash Absoluto)
                # O st.code não renderiza nada, só mostra o texto cru.
                
                st.subheader("📝 Posts")
                st.code(p1, language="text")
                
                st.subheader("💰 Scripts")
                st.code(p2, language="text")
                
                st.subheader("🔗 Bio")
                st.code(p3, language="text")