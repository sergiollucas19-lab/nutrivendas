import streamlit as st
import requests
import json

# 1. Configuração da Página
st.set_page_config(page_title="NutriVendas Gold", page_icon="🏆", layout="wide")

# 2. DESIGN PREMIUM (CSS CUSTOMIZADO)
st.markdown("""
<style>
    /* Fundo Geral */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Títulos Dourados */
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Card de Resultado (O Segredo da Beleza) */
    .premium-card {
        background-color: #1E1E1E;
        border: 1px solid #D4AF37;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Texto dentro do card */
    .premium-card p, .premium-card li {
        color: #E0E0E0;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* Botão de Luxo */
    div.stButton > button {
        background: linear-gradient(45deg, #D4AF37, #C5A028);
        color: black;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 12px;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div.stButton > button:hover {
        background: linear-gradient(45deg, #EDC967, #D4AF37);
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
    }
    
    /* Inputs Estilizados */
    input, select, textarea {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Menu Lateral
with st.sidebar:
    st.header("⚙️ Motor V8")
    modelo = st.selectbox(
        "Escolha o Modelo:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.info("💎 Status: Conta VIP Ativa")

# 4. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Falta API Key."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing de luxo para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: 
    - Use formatação Markdown (negrito, tópicos).
    - NÃO use tabelas complexas.
    
    Estrutura:
    [PARTE1] 
    ### 💡 3 Ideias de Conteúdo Viral
    (Desenvolva títulos e legendas)
    
    [PARTE2] 
    ### 💰 Scripts de Alta Conversão
    (Direct e Quebra de Objeção)
    
    [PARTE3] 
    ### 🚀 Bio Magnética
    (Nome, Promessa e CTA)
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

# 5. O SEGREDO ANTI-CRASH (Mantém bonito, mas seguro)
def sanitizar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    # Substitui o cifrão ($) pelo código HTML dele (&#36;)
    # O navegador desenha o cifrão, mas não tenta calcular matemática!
    texto = texto.replace("$", "&#36;") 
    return texto

# 6. Login
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.markdown("### 🔐 Acesso Restrito")
        senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR SISTEMA"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# 7. Interface Principal
st.title("🏆 NutriVendas Gold")
st.markdown("Transforme seguidores em pacientes com estratégia premium.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR ESTRATÉGIA PREMIUM")

with col2:
    if btn:
        with st.spinner("💎 Criando estratégia de alto padrão..."):
            texto_bruto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            
            # Limpeza de Segurança (Para não dar tela branca)
            texto = sanitizar_texto(texto_bruto)
            
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
                
                # Exibição "CARD" (Bonito e Organizado)
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                with abas[0]:
                    st.markdown(f'<div class="premium-card">{p1}</div>', unsafe_allow_html=True)
                    st.download_button("Baixar Posts", p1)
                    
                with abas[1]:
                    st.markdown(f'<div class="premium-card">{p2}</div>', unsafe_allow_html=True)
                    st.download_button("Baixar Scripts", p2)
                    
                with abas[2]:
                    st.markdown(f'<div class="premium-card">{p3}</div>', unsafe_allow_html=True)