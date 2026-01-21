import streamlit as st
import requests
import json
import uuid

# ================= CONFIG =================
st.set_page_config(
    page_title="NutriVendas Ultimate",
    page_icon="💎",
    layout="wide"
)

# ================= CSS =================
st.markdown("""
<style>
.stApp { background-color:#000000; color:#E0E0E0; }
h1, h2, h3 { color:#D4AF37 !important; }
p, .stMarkdown { color:#CCCCCC !important; }
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox("Motor de IA:", ["gemini-2.5-flash", "gemini-1.5-flash"])
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= IA =================
def gerar_marketing(nicho, tipo, preco, objetivo, modelo_escolhido):

    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    prompt = f"""
Você é um(a) Diretor(a) Criativo(a) e Copywriter sênior especializado(a) em marketing para nutricionistas.

Crie um PACOTE COMPLETO "COPIAR E POSTAR" para Instagram.

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}

REGRAS:
- Nada de ideias vagas.
- Tudo deve estar pronto para copiar e colar.
- Linguagem profissional e clara.
- Foco em conversão.
- Não use tabelas.

ENTREGAR OBRIGATORIAMENTE:

[PARTE1] POSICIONAMENTO + OFERTA
- Persona
- Promessa
- Diferenciais
- Pacotes de serviço

[PARTE2] BIO + DESTAQUES
- 3 bios prontas
- CTA
- Destaques com nomes

[PARTE3] CALENDÁRIO 14 DIAS
- Dia, tipo de post e CTA

[PARTE4] 6 CARROSSÉIS PRONTOS
Para cada um:
- Texto de cada slide
- Sugestão de imagem
- Legenda
- CTA
- Hashtags

[PARTE5] 4 REELS PRONTOS
- Hook
- Roteiro de fala
- Cenas
- Texto na tela
- Legenda
- CTA

[PARTE6] 10 STORIES PRONTOS
- Texto exato de cada story
- Sticker sugerido
- CTA

[PARTE7] SCRIPTS DE VENDAS
- DM
- WhatsApp
- Objeções
"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        r = requests.post(url, json=payload, timeout=45)
        if r.status_code != 200:
            return {"ok": False, "error": r.text}

        data = r.json()
        candidates = data.get("candidates", [])

        if not candidates:
            return {"ok": False, "error": "Gemini retornou vazio."}

        text = candidates[0]["content"]["parts"][0]["text"]
        return {"ok": True, "text": text}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# ================= HELPERS =================
def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("\x00", "")
    texto = texto.replace("$", " reais ")
    return texto

def split_partes(texto):
    partes = {}
    chaves = ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6","PARTE7"]
    for i, chave in enumerate(chaves):
        if f"[{chave}]" in texto:
            start = texto.index(f"[{chave}]")
            end = len(texto)
            for prox in chaves[i+1:]:
                if f"[{prox}]" in texto:
                    end = texto.index(f"[{prox}]")
                    break
            partes[chave] = texto[start:end].replace(f"[{chave}]", "").strip()
    return partes

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if senha == st.secrets.get("ACCESS_PASSWORD"):
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    st.stop()

# ================= APP =================
st.title("💎 NutriVendas Ultimate")
st.write("Marketing profissional para nutricionistas.")

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())

col1, col2 = st.columns([1,2])

with col1:
    with st.form("form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        objetivo = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        gerar = st.form_submit_button("GERAR PACOTE COMPLETO")

if gerar:
    with st.spinner("Gerando pacote premium..."):
        resp = gerar_marketing(nicho, tipo, preco, objetivo, modelo)
        if not resp["ok"]:
            st.session_state.resultado = {"erro": resp["error"]}
        else:
            texto = limpar_texto(resp["text"])
            if len(texto) > 35000:
                texto = texto[:35000] + "\n\n[conteúdo cortado para evitar travamento]"
            st.session_state.resultado = split_partes(texto)
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

with col2:
    res = st.session_state.resultado
    rodada = st.session_state.rodada

    if res is None:
        st.info("Preencha os dados e clique em **GERAR PACOTE COMPLETO**")
    elif "erro" in res:
        st.error(res["erro"])
    else:
        abas = st.tabs([
            "🎯 Posicionamento",
            "🔗 Bio",
            "📅 Calendário",
            "🖼️ Carrosséis",
            "🎬 Reels",
            "📲 Stories",
            "💬 Vendas"
        ])

        chaves = ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6","PARTE7"]
        for aba, chave in zip(abas, chaves):
            with aba:
                st.text_area(
                    "Copiar e colar:",
                    value=res.get(chave, "Não gerado."),
                    height=600,
                    key=f"{chave}_{rodada}"
                )
