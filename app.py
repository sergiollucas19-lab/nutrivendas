import streamlit as st
import requests
import json
import time

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO (Blindada contra erros de inicialização)
# ---------------------------------------------------------
try:
    st.set_page_config(page_title="NutriVendas", page_icon="🛡️", layout="wide")
except:
    pass # Ignora se já estiver configurado

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: white; }
    div.stButton > button { background-color: #008000; color: white; border-radius: 8px; width: 100%; font-weight: bold; }
    input, select, textarea { background-color: #262730 !important; color: white !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #262730; border-radius: 5px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #008000; color: white; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SEGURANÇA
# ---------------------------------------------------------
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("⚠️ ERRO CRÍTICO: Configure a GOOGLE_API_KEY nos Secrets!")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("⚠️ ERRO CRÍTICO: Configure a ACCESS_PASSWORD nos Secrets!")
    st.stop()

# ---------------------------------------------------------
# 3. FUNÇÃO DE CONEXÃO (Gemini 2.5)
# ---------------------------------------------------------
def gerar_conteudo_seguro(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # Usando o modelo que sabemos que existe
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    # Prompt simplificado para evitar quebra de formatação
    prompt = f"""
    Atue como expert em marketing para Nutricionistas.
    Dados: Nicho {nicho}, Atendimento {tipo}, Valor {preco}, Meta {objetivo}.
    
    CRIE O CONTEÚDO ABAIXO.
    IMPORTANTE: Use EXATAMENTE os marcadores [MARCADOR_1], [MARCADOR_2], [MARCADOR_3] para separar.
    
    [MARCADOR_1]
    Escreva 3 Ideias de Posts (Título chamativo + Legenda curta).
    
    [MARCADOR_2]
    Escreva 1 Script de Direct para quem pergunta "como funciona?" e 1 Script para quem diz "tá caro".
    
    [MARCADOR_3]
    Escreva uma Bio de Instagram otimizada e uma frase curta para o link da bio.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            # Tenta extrair o texto com segurança
            if 'candidates' in dados and len(dados['candidates']) > 0:
                content = dados['candidates'][0].get('content')
                if content and 'parts' in content:
                    return content['parts'][0]['text']
            return "Erro: A IA respondeu vazio."
        else:
            return f"Erro Google (Status {response.status_code}): {response.text}"
    except Exception as e:
        return f"Erro de Conexão: {str(e)}"

# ---------------------------------------------------------
# 4. TELA DE LOGIN
# ---------------------------------------------------------
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        st.title("🔒 Login Seguro")
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    st.stop()

# ---------------------------------------------------------
# 5. APP PRINCIPAL (Com proteção Anti-Tela Branca)
# ---------------------------------------------------------
st.title("🛡️ NutriVendas: Modo Blindado")

c1, c2 = st.columns([1, 2])
with c1:
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR AGORA")

with c2:
    if btn:
        # AQUI ESTÁ A PROTEÇÃO CONTRA TELA BRANCA
        try:
            with st.spinner("🤖 Conectando ao Gemini 2.5... (Isso pode levar uns segundos)"):
                resultado = gerar_conteudo_seguro(nicho, tipo, preco, obj)
                
                # Se voltou mensagem de erro da função
                if "Erro" in resultado and len(resultado) < 200:
                    st.error(resultado)
                else:
                    # Lógica de separação mais robusta
                    conteudo = "Não foi possível separar."
                    vendas = "..."
                    bio = "..."
                    
                    # Tenta separar pelos marcadores novos
                    parts = resultado.split("[MARCADOR_")
                    
                    if len(parts) > 1:
                        # Reconstrói a lógica simples
                        # parts[0] é lixo antes do primeiro marcador
                        # parts[1] deve ser o conteudo (1])
                        # parts[2] deve ser vendas (2])
                        # parts[3] deve ser bio (3])
                        
                        for p in parts:
                            if p.startswith("1]"):
                                conteudo = p.replace("1]", "").strip()
                            elif p.startswith("2]"):
                                vendas = p.replace("2]", "").strip()
                            elif p.startswith("3]"):
                                bio = p.replace("3]", "").strip()
                    else:
                        # Se falhar a separação, joga tudo no conteúdo
                        conteudo = resultado

                    # Exibe nas abas
                    t1, t2, t3 = st.tabs(["📲 Posts", "💰 Vendas", "🔗 Bio"])
                    t1.markdown(conteudo)
                    t2.markdown(vendas)
                    t3.markdown(bio)
                    
                    # Debug: Se der ruim nas abas, o usuário pode ver o texto bruto aqui
                    with st.expander("Ver Texto Bruto (Caso as abas falhem)"):
                        st.text(resultado)

        except Exception as e:
            # SE DER ERRO, VAI CAIR AQUI EM VEZ DE TELA BRANCA
            st.error(f"❌ Ocorreu um erro inesperado: {str(e)}")
            st.warning("Tente clicar em GERAR novamente.")