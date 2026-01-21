import streamlit as st
import requests
import json

# 1. Configuração Básica (Sem frescura)
st.set_page_config(page_title="NutriVendas Funcional", page_icon="💪", layout="wide")

# 2. Menu Lateral (Seleção de Motor)
with st.sidebar:
    st.header("⚙️ Configuração")
    st.write("Se um falhar, tente o outro:")
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        [
            "gemini-2.5-flash",                    # O potente (seu favorito)
            "gemini-2.0-flash-lite-preview-02-05", # O grátis (reserva)
            "gemini-exp-1206"                      # O experimental
        ]
    )

# 3. Função de Inteligência
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "ERRO: Configure a GOOGLE_API_KEY nos Secrets."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    # Prompt Organizado
    prompt = f"""
    Atue como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Crie 3 seções. Use EXATAMENTE estes marcadores para separar:
    
    [PARTE1]
    3 Ideias de Posts (Título chamativo + Legenda curta)
    
    [PARTE2]
    1 Script de Vendas para Direct (Respondendo "como funciona")
    1 Script de Quebra de Objeção (Respondendo "tá caro")
    
    [PARTE3]
    Bio do Instagram Otimizada e frase para link.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=25)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            return "QUOTA_EXCEEDED"
        else:
            return f"ERRO GOOGLE ({response.status_code}): {response.text}"
    except Exception as e:
        return f"ERRO DE CONEXÃO: {e}"

# 4. Login Simples
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if "ACCESS_PASSWORD" in st.secrets and senha == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha incorreta")
    st.stop()

# 5. Interface Principal
st.title("🥗 NutriVendas: Modo Seguro")
st.write("Gerador de Marketing (Visual Padrão)")

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form_principal"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with col2:
    if btn:
        with st.spinner(f"Processando com {modelo}..."):
            texto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            
            if texto == "QUOTA_EXCEEDED":
                st.error("⚠️ Limite atingido neste modelo!")
                st.info("👉 Tente mudar a opção no menu lateral esquerdo.")
            elif "ERRO" in texto:
                st.error(texto)
            else:
                # Separação Segura
                p1, p2, p3 = texto, "...", "..."
                
                if "[PARTE1]" in texto:
                    partes = texto.split("[PARTE2]")
                    p1 = partes[0].replace("[PARTE1]", "").strip()
                    if len(partes) > 1:
                        resto = partes[1].split("[PARTE3]")
                        p2 = resto[0].strip()
                        if len(resto) > 1:
                            p3 = resto[1].strip()
                
                # Abas Padrão (Sem estilo customizado)
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                abas[0].markdown(p1)
                abas[1].markdown(p2)
                abas[2].markdown(p3)