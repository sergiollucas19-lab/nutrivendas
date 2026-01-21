import streamlit as st
import requests
import json

# 1. Configuração da Página
st.set_page_config(page_title="NutriVendas Black", page_icon="💎", layout="wide")

# 2. CSS DE LUXO (A MÁGICA VISUAL)
st.markdown("""
<style>
    /* Fundo Dark Mode Real */
    .stApp {
        background-color: #050505;
        color: #E0E0E0;
    }
    
    /* Títulos Dourados Metálicos */
    h1, h2, h3 {
        color: #F2C94C !important;
        font-family: 'Arial', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    /* Maquiagem das Caixas de Texto (Para não parecerem simples) */
    .stTextArea textarea {
        background-color: #121212 !important;
        color: #D4AF37 !important; /* Texto Dourado */
        border: 1px solid #333 !important;
        border-radius: 10px;
        font-family: 'Courier New', monospace; /* Fonte estilo Hacker/Premium */
    }
    .stTextArea textarea:focus {
        border-color: #F2C94C !important;
        box-shadow: 0 0 10px rgba(242, 201, 76, 0.2);
    }
    
    /* Inputs (Onde você digita) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1E1E1E !important;
        color: white !important;
        border-radius: 8px;
        border: 1px solid #444;
    }
    
    /* Botão de Ouro */
    div.stButton > button {
        background: linear-gradient(90deg, #BF953F, #FCF6BA, #B38728, #FBF5B7, #AA771C);
        color: black;
        font-weight: 900;
        border: none;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        width: 100%;
        text-transform: uppercase;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(191, 149, 63, 0.6);
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        border-radius: 5px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #D4AF37 !important;
        color: black !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 3. Menu Lateral
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox(
        "Motor de IA:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.markdown("---")
    st.info("💎 **Licença VIP Ativa**")

# 4. Função IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Falta API Key."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing de luxo para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: Não use Markdown complexo ou tabelas.
    
    Estrutura:
    [PARTE1] 3 Ideias de Posts Virais (Título e Legenda)
    [PARTE2] Scripts de Vendas (Direct e Quebra de Objeção)
    [PARTE3] Bio Magnética (Promessa e CTA)
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

# 5. Sanitização (Troca cifrão por texto pra não quebrar)
def limpar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    return texto.replace("$", " reais ")

# 6. Login
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Acesso VIP")
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("DESBLOQUEAR SISTEMA"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# 7. Interface Principal
st.title("💎 NutriVendas Black")
st.markdown("Estratégia Premium com Tecnologia Blindada.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Parâmetros")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with col2:
    if btn:
        with st.spinner("Conectando ao Neural Engine..."):
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
                
                # AQUI ESTÁ O TRUQUE:
                # Usamos st.text_area (que é seguro e nunca cai)
                # Mas o CSS lá em cima pintou ele de PRETO E DOURADO.
                
                abas = st.tabs(["Conteúdo", "Vendas", "Bio"])
                
                with abas[0]:
                    st.markdown("### 📝 Posts Prontos")
                    st.text_area("Posts", value=p1, height=500, label_visibility="collapsed")
                    
                with abas[1]:
                    st.markdown("### 💰 Scripts de Conversão")
                    st.text_area("Scripts", value=p2, height=500, label_visibility="collapsed")
                    
                with abas[2]:
                    st.markdown("### 🔗 Bio do Perfil")
                    st.text_area("Bio", value=p3, height=200, label_visibility="collapsed")