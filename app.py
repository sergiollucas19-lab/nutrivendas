import streamlit as st
import requests
import json

# 1. Configuração (Visual Padrão para não dar conflito)
st.set_page_config(page_title="NutriVendas Blindado", page_icon="🛡️", layout="wide")

# 2. Menu Lateral (Seu motor novo)
with st.sidebar:
    st.header("⚙️ Motor PRO")
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        [
            "gemini-1.5-flash",    # O MELHOR (Sua conta paga libera este)
            "gemini-2.0-flash",    # Alternativa
            "gemini-2.5-flash"     # Alternativa
        ]
    )
    st.success(f"Conta Ativa. Usando: {modelo}")

# 3. Função IA (Prompt Seguro)
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "ERRO: Falta a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: 
    - NÃO use tabelas.
    - NÃO use formatação matemática (LaTeX).
    - Escreva apenas texto simples.
    
    Crie 3 seções separadas EXATAMENTE assim:
    
    [PARTE1]
    3 Ideias de Posts (Título e Legenda)
    
    [PARTE2]
    Script de Vendas (Direct e Objeção)
    
    [PARTE3]
    Bio do Instagram
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"ERRO GOOGLE ({response.status_code}): {response.text}"
    except Exception as e:
        return f"ERRO CONEXÃO: {e}"

# 4. Login
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login VIP")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if "ACCESS_PASSWORD" in st.secrets and senha == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# 5. Interface Principal (MODO SEGURO)
st.title("💎 NutriVendas: Modo Texto Puro")
st.info("Visualização em Caixas de Texto (Anti-Crash)")

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with col2:
    if btn:
        with st.spinner(f"Gerando com {modelo}..."):
            texto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            
            if "ERRO" in texto:
                st.error(texto)
            else:
                p1, p2, p3 = texto, "...", "..."
                
                # Tenta separar as partes
                if "[PARTE1]" in texto:
                    try:
                        partes = texto.split("[PARTE2]")
                        p1 = partes[0].replace("[PARTE1]", "").strip()
                        if len(partes) > 1:
                            resto = partes[1].split("[PARTE3]")
                            p2 = resto[0].strip()
                            if len(resto) > 1:
                                p3 = resto[1].strip()
                    except:
                        pass 
                
                # AQUI É O SEGREDO: Usamos 'text_area' em vez de 'markdown'
                # Isso impede o navegador de tentar desenhar símbolos matemáticos
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                with abas[0]:
                    st.write("🔽 Copie o texto abaixo:")
                    st.text_area("Posts", value=p1, height=450)
                    
                with abas[1]:
                    st.write("🔽 Copie o texto abaixo:")
                    st.text_area("Scripts", value=p2, height=450)
                    
                with abas[2]:
                    st.write("🔽 Copie o texto abaixo:")
                    st.text_area("Bio", value=p3, height=200)