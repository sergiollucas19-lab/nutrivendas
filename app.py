import streamlit as st
import requests
import json

# 1. Configuração (Blindada)
st.set_page_config(page_title="NutriVendas VIP", page_icon="💎", layout="wide")

# 2. Menu Lateral (Voltando para o 2.5 que funciona e agora é pago/ilimitado)
with st.sidebar:
    st.header("⚙️ Motor Potente")
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        [
            "gemini-2.5-flash",                    # O CAMPEÃO (Agora ilimitado)
            "gemini-2.0-flash-lite-preview-02-05", # O Backup rápido
            "gemini-2.0-flash"                     # Outra opção
        ]
    )
    st.success(f"Modo VIP Ativo. Usando: {modelo}")

# 3. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "ERRO: Falta a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    REGRAS DE SEGURANÇA:
    - NÃO use tabelas.
    - NÃO use LaTeX.
    - Escreva texto simples e direto.
    
    Crie 3 seções:
    [PARTE1] 3 Ideias de Posts
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

# 5. Interface
st.title("💎 NutriVendas: Versão Final")
st.info("Sistema operando com Gemini 2.5 (Ilimitado) e Proteção Anti-Crash.")

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

                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                # PROTEÇÃO TOTAL: Caixas de Texto
                with abas[0]:
                    st.write("### Posts Sugeridos:")
                    st.text_area("Copie aqui:", value=p1, height=450)
                with abas[1]:
                    st.write("### Scripts de Vendas:")
                    st.text_area("Copie aqui:", value=p2, height=450)
                with abas[2]:
                    st.write("### Bio do Perfil:")
                    st.text_area("Copie aqui:", value=p3, height=200)