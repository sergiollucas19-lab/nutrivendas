import streamlit as st
import requests
import json

# 1. Configuração da Página
st.set_page_config(
    page_title="NutriVendas Elite",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS "CLEAN" (Só o necessário para o luxo, sem quebrar o site)
st.markdown("""
<style>
    /* Fundo Preto Profundo */
    .stApp {
        background-color: #000000;
        color: #E0E0E0;
    }
    
    /* Títulos Dourados */
    h1, h2, h3, h4 {
        color: #D4AF37 !important;
        font-family: sans-serif;
        font-weight: 600;
    }
    
    /* Ajuste da Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333;
    }
    
    /* Botão Dourado Seguro */
    div.stButton > button {
        background-color: #D4AF37;
        color: black;
        border: none;
        font-weight: bold;
        text-transform: uppercase;
        width: 100%;
        padding: 0.5rem;
    }
    div.stButton > button:hover {
        background-color: #F2C94C;
        color: black;
    }
    
    /* Caixas de Texto (Deixar nativo do Streamlit escuro, é mais seguro) */
    .stTextArea textarea {
        background-color: #1a1a1a;
        color: #f0f0f0;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)

# 3. Menu Lateral
with st.sidebar:
    st.header("⚙️ Painel Elite")
    modelo = st.selectbox(
        "Motor de Inteligência:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.markdown("---")
    st.success("💎 Status: VIP Ativo")

# 4. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Configure a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    # Prompt Direto
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: Não use Markdown complexo (tabelas/negrito). Use texto simples.
    
    Estrutura:
    [PARTE1] 3 Ideias de Posts (Título e Legenda)
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

# 5. Sanitização (Segurança contra o crash do cifrão)
def limpar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    # Troca cifrão por texto para não ativar matemática
    return texto.replace("$", " reais ")

# 6. Login
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ACESSAR"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# 7. Interface Principal
st.title("🏆 NutriVendas Elite")
st.markdown("Estratégia de Marketing Premium.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        st.write("")
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with col2:
    if btn:
        with st.spinner("💎 Processando estratégia..."):
            texto_bruto = gerar_marketing(nicho, tipo, preco, obj, modelo)
            texto = limpar_texto(texto_bruto)
            
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
                
                # Exibição Segura (Abas com Caixa de Texto Nativa)
                # Não tentamos pintar a caixa de texto com CSS agressivo
                # O fundo do site já é preto, então a caixa cinza escuro fica elegante.
                
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                with abas[0]:
                    st.text_area("Posts Sugeridos", value=p1, height=500)
                    
                with abas[1]:
                    st.text_area("Scripts de Vendas", value=p2, height=500)
                    
                with abas[2]:
                    st.text_area("Bio Sugerida", value=p3, height=200)