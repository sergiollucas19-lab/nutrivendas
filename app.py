import streamlit as st
import requests
import json
import uuid # Importante para gerar identidades únicas

# 1. CONFIGURAÇÃO (Modo Wide)
st.set_page_config(
    page_title="NutriVendas Ultimate",
    page_icon="💎",
    layout="wide"
)

# 2. CSS PRETO E DOURADO (Sem mexer em componentes perigosos)
st.markdown("""
<style>
    /* Fundo Preto Absoluto */
    .stApp {
        background-color: #000000;
        color: #E0E0E0;
    }
    
    /* Títulos Dourados */
    h1, h2, h3 {
        color: #D4AF37 !important;
        font-family: sans-serif;
    }
    
    /* Ajustes finos de contraste */
    p, .stMarkdown {
        color: #CCCCCC !important;
    }
    
    /* Esconde menu padrão para ficar mais clean */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# 3. MENU LATERAL
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox(
        "Motor de IA:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.divider()
    st.success("💎 Status: VIP Ativo")

# 4. FUNÇÃO IA
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Configure a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    Estrutura Obrigatória:
    [PARTE1] 3 Ideias de Posts (Título e Legenda)
    [PARTE2] Scripts de Vendas (Direct e Quebra de Objeção)
    [PARTE3] Bio do Instagram
    
    Regra: Não use tabelas. Use texto corrido.
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

# 5. SANITIZAÇÃO
def limpar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    return texto.replace("$", " reais ")

# 6. LOGIN
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# 7. INTERFACE PRINCIPAL
st.title("💎 NutriVendas Ultimate")
st.write("Estratégia de Marketing Premium.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        st.write("")
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

with col2:
    if btn:
        with st.spinner("💎 Processando..."):
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
                
                # Gera um ID único para essa rodada
                # Isso impede o navegador de "reaproveitar" a caixa antiga e travar
                rodada_id = str(uuid.uuid4())
                
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                with abas[0]:
                    # Adicionamos key=rodada_id para forçar recriação
                    st.text_area("Copie seus posts:", value=p1, height=500, key=f"posts_{rodada_id}")
                    
                with abas[1]:
                    st.text_area("Copie seus scripts:", value=p2, height=500, key=f"scripts_{rodada_id}")
                    
                with abas[2]:
                    st.text_area("Copie sua bio:", value=p3, height=200, key=f"bio_{rodada_id}")