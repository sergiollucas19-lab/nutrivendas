import streamlit as st
import requests
import json

# 1. CONFIGURAÇÃO (O segredo da estabilidade)
st.set_page_config(
    page_title="NutriVendas Pro",
    page_icon="💎",
    layout="wide"
)

# 2. ESTILO SEGURO (Apenas cores de fundo e texto, sem mexer nos botões)
st.markdown("""
<style>
    /* Fundo Preto Real */
    .stApp {
        background-color: #050505;
    }
    
    /* Textos Principais em Dourado */
    h1, h2, h3 {
        color: #D4AF37 !important;
    }
    
    /* Texto normal em cinza claro para leitura confortável */
    p, label, .stMarkdown {
        color: #E0E0E0 !important;
    }
    
    /* Removemos as estilizações forçadas de botão e input que davam tela branca */
</style>
""", unsafe_allow_html=True)

# 3. BARRA LATERAL
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox(
        "Motor de Inteligência:", 
        ["gemini-2.5-flash", "gemini-1.5-flash"]
    )
    st.write("---")
    st.info("💎 Status: Conta VIP Ativa")

# 4. FUNÇÃO IA (Blindada contra erros)
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets: return "ERRO: Configure a GOOGLE_API_KEY."
    
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"
    
    prompt = f"""
    Aja como expert em marketing para Nutricionistas.
    Contexto: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    IMPORTANTE: Não use tabelas ou formatação complexa.
    
    Estrutura:
    [PARTE1] 3 Ideias de Posts (Título e Legenda)
    [PARTE2] Scripts de Vendas (Direct e Quebra de Objeção)
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

# 5. SANITIZAÇÃO (Troca cifrão por texto)
def limpar_texto(texto):
    if not isinstance(texto, str): return str(texto)
    # Essa substituição é essencial para o nicho de emagrecimento
    return texto.replace("$", " reais ")

# 6. LOGIN SIMPLES
if "auth" not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Acesso")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# 7. INTERFACE PRINCIPAL
st.title("💎 NutriVendas Premium")
st.write("Estratégia de Marketing de Alta Conversão.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        st.write("") # Espaço
        # O botão nativo é mais estável
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
                
                # Visualização Segura e Limpa
                abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])
                
                with abas[0]:
                    st.text_area("Copie seus posts:", value=p1, height=500)
                    
                with abas[1]:
                    st.text_area("Copie seus scripts:", value=p2, height=500)
                    
                with abas[2]:
                    st.text_area("Copie sua bio:", value=p3, height=200)