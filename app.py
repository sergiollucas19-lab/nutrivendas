import streamlit as st
import requests
import json
import uuid

st.set_page_config(page_title="NutriVendas Ultimate", page_icon="💎", layout="wide")

st.markdown("""
<style>
    .stApp { background-color:#000000; color:#E0E0E0; }
    h1, h2, h3 { color:#D4AF37 !important; font-family:sans-serif; }
    p, .stMarkdown { color:#CCCCCC !important; }
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox("Motor de IA:", ["gemini-2.5-flash", "gemini-1.5-flash"])
    st.divider()
    st.success("💎 Status: VIP Ativo")

def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "Configure a GOOGLE_API_KEY no st.secrets."}

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
    try:
        # IMPORTANTÍSSIMO: use json=payload (evita bugs de encoding)
        r = requests.post(url, json=payload, timeout=45)
        if r.status_code != 200:
            return {"ok": False, "error": f"ERRO GOOGLE ({r.status_code}): {r.text}"}

        data = r.json()

        # Gemini às vezes retorna candidates vazio / bloqueado
        candidates = data.get("candidates", [])
        if not candidates:
            return {"ok": False, "error": f"Resposta sem candidates. Retorno: {data}"}

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            return {"ok": False, "error": f"Resposta sem texto. Retorno: {data}"}

        return {"ok": True, "text": parts[0]["text"]}

    except Exception as e:
        return {"ok": False, "error": f"ERRO CONEXÃO: {e}"}

def limpar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        texto = str(texto)
    # evita coisas estranhas em render
    texto = texto.replace("\x00", "")
    texto = texto.replace("$", " reais ")
    return texto

def split_partes(texto):
    p1, p2, p3 = texto, "", ""
    if "[PARTE1]" in texto and "[PARTE2]" in texto and "[PARTE3]" in texto:
        try:
            a = texto.split("[PARTE2]", 1)
            p1 = a[0].replace("[PARTE1]", "").strip()
            b = a[1].split("[PARTE3]", 1)
            p2 = b[0].strip()
            p3 = b[1].strip() if len(b) > 1 else ""
        except:
            pass
    return p1, p2, p3

# ------------------ LOGIN ------------------
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if "ACCESS_PASSWORD" not in st.secrets:
                st.error("ACCESS_PASSWORD não configurado no st.secrets.")
            elif senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# ------------------ APP ------------------
st.title("💎 NutriVendas Ultimate")
st.write("Estratégia de Marketing Premium.")

# Estado para persistir resultado (isso evita “tela branca” por rerun)
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "rodada_id" not in st.session_state:
    st.session_state.rodada_id = str(uuid.uuid4())

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Valor", "R$ 200")
        obj = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        btn = st.form_submit_button("GERAR ESTRATÉGIA")

# Geração (só atualiza o estado)
if btn:
    with st.spinner("💎 Processando..."):
        resp = gerar_marketing(nicho, tipo, preco, obj, modelo)
        if not resp["ok"]:
            st.session_state.resultado = {"erro": resp["error"]}
        else:
            texto = limpar_texto(resp["text"])

            # Proteção anti-travamento: corta se vier enorme
            MAX_CHARS = 30000
            if len(texto) > MAX_CHARS:
                texto = texto[:MAX_CHARS] + "\n\n[...cortado para evitar travamento no navegador...]"

            p1, p2, p3 = split_partes(texto)
            st.session_state.resultado = {"p1": p1, "p2": p2, "p3": p3}

        st.session_state.rodada_id = str(uuid.uuid4())  # “reset” seguro
        st.rerun()

with col2:
    # Renderiza SEMPRE (mesmo após rerun)
    abas = st.tabs(["📝 Conteúdo", "💰 Vendas", "🔗 Bio"])

    res = st.session_state.resultado
    rodada_id = st.session_state.rodada_id

    if res and "erro" in res:
        st.error(res["erro"])
    elif res:
        with abas[0]:
            st.text_area("Copie seus posts:", value=res["p1"], height=500, key=f"posts_{rodada_id}")
        with abas[1]:
            st.text_area("Copie seus scripts:", value=res["p2"], height=500, key=f"scripts_{rodada_id}")
        with abas[2]:
            st.text_area("Copie sua bio:", value=res["p3"], height=200, key=f"bio_{rodada_id}")
    else:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR ESTRATÉGIA**.")
