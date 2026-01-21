import streamlit as st
import requests
import json

# 1. Configuração da Página
st.set_page_config(page_title="NutriVendas PRO", page_icon="💎", layout="wide")

# 2. Menu Lateral (Agora com o modelo 1.5 liberado!)
with st.sidebar:
    st.header("⚙️ Motor da IA")
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        [
            "gemini-1.5-flash",    # O MELHOR (Agora liberado para você)
            "gemini-2.5-flash",    # O mais novo
            "gemini-2.0-flash"     # Alternativa
        ]
    )
    st.success(f"Conta VIP Ativa. Usando: {modelo}")

# 3. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets:
        return "ERRO: Configure a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    # Prompt Otimizado
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: NÃO use formatação matemática (LaTeX) ou cifrão solto.
    
    Estrutura da Resposta:
    
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

# 4. Função de Limpeza (O Segredo para não dar Tela Branca)
def limpar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    # Troca o cifrão ($) por HTML seguro para não bugar o site
    return texto.replace("$", "&#36;")

# 5. Login
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

# 6. Interface Principal
st.title("💎 NutriVendas: Versão PRO")
st.write("Sistema desbloqueado e sem limites.")

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
            bruto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            
            # Limpeza de Segurança
            texto = limpar_texto(bruto)
            
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
                    except:
                        pass # Se falhar a divisão, mostra tudo bruto
                
                # Exibição Segura
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                abas[0].markdown(p1, unsafe_allow_html=True)
                abas[1].markdown(p2, unsafe_allow_html=True)
                abas[2].markdown(p3, unsafe_allow_html=True)