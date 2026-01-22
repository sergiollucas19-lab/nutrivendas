import streamlit as st
import requests
import uuid
import time

# ================= CONFIG =================
st.set_page_config(page_title="NutriVendas Weekly", page_icon="💎", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.stApp { background-color:#000000; color:#E0E0E0; }
h1, h2, h3 { color:#D4AF37 !important; font-family:sans-serif; }
p, .stMarkdown { color:#CCCCCC !important; }
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    modelo = st.selectbox("Motor de IA:", ["gemini-2.5-flash", "gemini-1.5-flash"])
    semana = st.selectbox("Pacote:", ["Semana 1", "Semana 2", "Semana 3", "Semana 4"])
    debug_mode = st.toggle("🔎 Debug (ver bruto)", value=False)
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= HELPERS =================
SECTIONS = [
    "POSICIONAMENTO",
    "BIO",
    "CALENDARIO",
    "CARROSSEL_1",
    "CARROSSEL_2",
    "CARROSSEL_3",
    "REELS_IDEIAS",
    "STORIES_IDEIAS",
]

def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ")

def call_gemini(prompt, modelo_escolhido, max_output_tokens=2000, timeout_segundos=120, max_tentativas=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada no st.secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.65,
            "maxOutputTokens": int(max_output_tokens)
        }
    }

    last_err = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout_segundos)
            if r.status_code != 200:
                if r.status_code in (429, 500, 503):
                    time.sleep(2 ** (tentativa - 1))
                    continue
                return {"ok": False, "error": f"ERRO GOOGLE ({r.status_code}): {r.text}"}

            data = r.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {"ok": False, "error": f"Sem candidates. Retorno: {data}"}

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                return {"ok": False, "error": f"Sem texto. Retorno: {data}"}

            return {"ok": True, "text": parts[0]["text"]}

        except requests.exceptions.ReadTimeout as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))
        except Exception as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))

    return {"ok": False, "error": f"Timeout/instabilidade após {max_tentativas} tentativas: {last_err}"}

def extract_sections(raw: str):
    """
    Recorta o texto usando marcadores ###NOME###.
    Se algum marcador não vier, mantém vazio (mas nunca quebra).
    """
    raw = raw or ""
    out = {k: "" for k in SECTIONS}

    # normaliza
    text = raw.replace("\r\n", "\n")

    # encontra posições
    positions = []
    for name in SECTIONS:
        marker = f"###{name}###"
        idx = text.find(marker)
        if idx != -1:
            positions.append((idx, name, marker))
    positions.sort()

    # se não vier nenhum marcador, joga tudo no POSICIONAMENTO pra não “sumir”
    if not positions:
        out["POSICIONAMENTO"] = text.strip()
        return out

    # recorta por intervalos
    for i, (idx, name, marker) in enumerate(positions):
        start = idx + len(marker)
        end = len(text) if i == len(positions) - 1 else positions[i + 1][0]
        out[name] = text[start:end].strip()

    return out

def ensure_not_empty(sections):
    # coloca aviso nas partes vazias para você enxergar o que faltou
    for k in SECTIONS:
        if not sections.get(k, "").strip():
            sections[k] = "⚠️ Não veio conteúdo nessa parte. Clique em GERAR novamente (instabilidade)."
    return sections

# ================= PROMPT (vendável e obediente) =================
def build_prompt(nicho, tipo, preco, objetivo, semana):
    return f"""
Você é um estrategista e copywriter sênior para Instagram de nutricionistas.
Seu objetivo é entregar CONTEÚDO PRONTO (copiar e colar), sem ficar só em “ideias vagas”.

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana: {semana}

REGRAS OBRIGATÓRIAS:
- Português (Brasil).
- NÃO use tabelas.
- Você DEVE imprimir TODOS os marcadores exatamente como estão.
- Em carrosséis: entregar TEXTO PRONTO por slide (curto e postável).
- Reels: APENAS IDEIAS (não roteiro completo).
- Stories: APENAS IDEIAS em sequência curta (3 stories cada).
- Não finalize no meio. Se faltar espaço, reduza o texto, mas mantenha a estrutura.

FORMATO (OBRIGATÓRIO):
###POSICIONAMENTO###
Promessa:
Público ideal:
CTA padrão:

###BIO###
Bio 1:
Bio 2:
Frase link da bio:
Destaques:
- Nome: itens
- Nome: itens
- Nome: itens
- Nome: itens
- Nome: itens

###CALENDARIO###
Dia 1:
Dia 2:
Dia 3:
Dia 4:
Dia 5:
Dia 6:
Dia 7:

###CARROSSEL_1###
TEMA:
CAPA:
SLIDE 1:
SLIDE 2:
SLIDE 3:
SLIDE 4:
SLIDE 5:
SLIDE 6:
SLIDE 7 (CTA):
IMAGEM SLIDE 1:
IMAGEM SLIDE 2:
IMAGEM SLIDE 3:
IMAGEM SLIDE 4:
IMAGEM SLIDE 5:
IMAGEM SLIDE 6:
IMAGEM SLIDE 7:
LEGENDA (curta, copiar e colar):
CTA FINAL:
HASHTAGS (10):

###CARROSSEL_2###
(mesma estrutura do carrossel 1)

###CARROSSEL_3###
(mesma estrutura do carrossel 1)

###REELS_IDEIAS###
Reels 1 — Tema:
Hook:
O que falar (3 bullets):
O que mostrar (2 bullets):
Duração:
Reels 2 — ...
Reels 3 — ...
Reels 4 — ...
Reels 5 — ...

###STORIES_IDEIAS###
Sequência 1 — Tema:
Story 1 (texto):
Sticker:
Story 2 (texto):
Sticker:
Story 3 (texto):
Sticker:
CTA:
Sequência 2 — ...
Sequência 3 — ...
Sequência 4 — ...
Sequência 5 — ...
"""

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
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

# ================= APP =================
st.title("💎 NutriVendas Weekly")
st.write("Carrosséis PRONTOS (texto por slide) + ideias de Reels/Stories. Estável e vendável.")

if "sections" not in st.session_state:
    st.session_state.sections = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())
if "raw" not in st.session_state:
    st.session_state.raw = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        objetivo = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        gerar = st.form_submit_button("GERAR PACOTE SEMANAL")

if gerar:
    with st.spinner("Gerando pacote semanal..."):
        prompt = build_prompt(nicho, tipo, preco, objetivo, semana)
        # tokens equilibrados para caber tudo; se cortar, reduz texto mas mantém estrutura
        resp = call_gemini(prompt, modelo, max_output_tokens=2300, timeout_segundos=120, max_tentativas=3)

    if not resp["ok"]:
        st.session_state.sections = {"POSICIONAMENTO": f"ERRO: {resp['error']}"}
        st.session_state.raw = ""
    else:
        raw = limpar_texto(resp["text"])
        st.session_state.raw = raw
        secs = extract_sections(raw)
        secs = ensure_not_empty(secs)
        st.session_state.sections = secs

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

# ================= UI =================
with col2:
    rodada = st.session_state.rodada
    secs = st.session_state.sections

    tabs = ["🎯 Posicionamento", "🔗 Bio", "📅 Semana", "🖼️ Carrossel 1", "🖼️ Carrossel 2", "🖼️ Carrossel 3", "🎬 Reels (ideias)", "📲 Stories (ideias)"]
    if debug_mode:
        tabs.append("🔎 Debug")

    abas = st.tabs(tabs)

    if secs is None:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR PACOTE SEMANAL**.")
    else:
        with abas[0]:
            st.text_area("Copiar e colar:", value=secs.get("POSICIONAMENTO", ""), height=350, key=f"pos_{rodada}")
        with abas[1]:
            st.text_area("Copiar e colar:", value=secs.get("BIO", ""), height=550, key=f"bio_{rodada}")
        with abas[2]:
            st.text_area("Copiar e colar:", value=secs.get("CALENDARIO", ""), height=550, key=f"cal_{rodada}")
        with abas[3]:
            st.text_area("Copiar e colar:", value=secs.get("CARROSSEL_1", ""), height=650, key=f"c1_{rodada}")
        with abas[4]:
            st.text_area("Copiar e colar:", value=secs.get("CARROSSEL_2", ""), height=650, key=f"c2_{rodada}")
        with abas[5]:
            st.text_area("Copiar e colar:", value=secs.get("CARROSSEL_3", ""), height=650, key=f"c3_{rodada}")
        with abas[6]:
            st.text_area("Copiar e colar:", value=secs.get("REELS_IDEIAS", ""), height=650, key=f"reels_{rodada}")
        with abas[7]:
            st.text_area("Copiar e colar:", value=secs.get("STORIES_IDEIAS", ""), height=650, key=f"stories_{rodada}")

        if debug_mode:
            with abas[-1]:
                st.markdown("### Resposta bruta (pra diagnosticar quando cortar)")
                st.text_area("RAW", value=st.session_state.raw, height=650, key=f"raw_{rodada}")
