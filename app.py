import streamlit as st
import requests
import uuid
import time
import random

# =========================
# CONFIG / BRAND
# =========================
APP_NAME = "Nutri Social Studio"
APP_TAGLINE = "Conteúdo profissional para nutricionistas — simples, constante e clínico."
PRIMARY_MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-1.5-flash"]

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🍎",
    layout="wide"
)

# Debug seguro
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
debug_mode = st.session_state.debug_mode

# =========================
# CSS (VINHO PROFISSIONAL)
# =========================
st.markdown("""
<style>
.stApp {
    background-color: #0b0b0b;
    color: #E0E0E0;
}

h1, h2, h3 {
    color: #7B1E3A !important;
    font-family: sans-serif;
}

p, .stMarkdown {
    color: #CCCCCC !important;
}

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background-color: #141414 !important;
    color: #f0f0f0 !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 10px !important;
}

/* Select */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #141414 !important;
    color: #f0f0f0 !important;
    border: 1px solid #2e2e2e !important;
    border-radius: 10px !important;
}

/* Placeholder */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #8a8a8a !important;
    opacity: 1 !important;
}

/* Tabs */
div[role="tablist"] button {
    color: #7B1E3A !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HASHTAGS (FIXO NUTRIÇÃO)
# =========================
HASHTAGS = [
    "#nutricionista", "#nutricao", "#alimentacaosaudavel", "#reeducacaoalimentar",
    "#comidadeverdade", "#rotinasaudavel", "#habitos", "#saude", "#bemestar", "#qualidadedevida"
]

def pick_hashtags():
    base = HASHTAGS[:]
    random.shuffle(base)
    return base[:10]

# =========================
# GEMINI CALL (CURTO = ESTÁVEL)
# =========================
def call_gemini(prompt, model, max_output_tokens=420, timeout=60, retries=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "Configure GOOGLE_API_KEY em Secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": int(max_output_tokens)
        }
    }

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                return {"ok": True, "text": data["candidates"][0]["content"]["parts"][0]["text"].strip()}
            time.sleep(2 ** (attempt - 1))
        except Exception as e:
            last_err = e

    return {"ok": False, "error": str(last_err)}

# =========================
# PROMPT (NUTRIÇÃO FIXA)
# =========================
def build_prompt_fill(publico, tema):
    return f"""
Você é um nutricionista e estrategista de conteúdo clínico para Instagram.

Preencha os campos abaixo com frases curtas e claras:

CAPA:
EXPLICACAO:
DICA1:
DICA2:
MINI_EXPANSAO:
REELS_HOOK:
REELS_CENAS:
STORIES_1:
STORIES_2:
STORIES_3:

Contexto:
Nicho: Nutrição
Público: {publico}
Tema: {tema}
"""

# =========================
# PARSE
# =========================
def parse_kv(text):
    out = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().upper()] = v.strip()
    return out

# =========================
# BUILD OUTPUTS
# =========================
def build_carousel(kv):
    return f"""
SLIDE 1 (CAPA)
{kv.get("CAPA", "3 ajustes simples para melhorar sua alimentação")}

SLIDE 2 (DOR)
Você tenta fazer tudo certo, mas não consegue manter constância.

SLIDE 3 (EXPLICAÇÃO)
{kv.get("EXPLICACAO", "Rotina simples vence motivação. Quanto menos decisões, mais constância.")}

SLIDE 4 (AUTORIDADE)
Não é falta de disciplina. É estratégia nutricional.

SLIDE 5 (DICA 1)
{kv.get("DICA1", "Monte refeições previsíveis: proteína + fibra + carbo simples.")}

SLIDE 6 (DICA 2)
{kv.get("DICA2", "Tenha um lanche âncora para evitar escolhas impulsivas.")}

SLIDE 7 (CTA)
Salve este post e use na sua semana.

IMAGENS SUGERIDAS:
1) fundo escuro + texto grande
2) pessoa pensativa
3) ícones simples
4) jaleco / consultório
5) prato equilibrado
6) lanche simples
7) botão salvar
""".strip()

def build_caption(kv):
    return f"""
LEGENDA

Se você sente que começa bem e depois perde constância, esse post é pra você.

{kv.get("MINI_EXPANSAO", "Simplificar a rotina alimentar reduz ansiedade e melhora adesão.")}

Salve para aplicar hoje.

HASHTAGS: {" ".join(pick_hashtags())}
""".strip()

def build_reels(kv):
    return f"""
REELS (direção)

Hook: {kv.get("REELS_HOOK", "Quando a dieta vira um peso…")}
Cenas: {kv.get("REELS_CENAS", "1) close 2s | 2) prato simples | 3) texto na tela")}
Duração: 7–12s
""".strip()

def build_stories(kv):
    return f"""
STORIES (sequência)

Story 1 — {kv.get("STORIES_1", "Você sente que sua alimentação não é constante?")}
Story 2 — {kv.get("STORIES_2", "O problema não é você. É excesso de decisões.")}
Story 3 — {kv.get("STORIES_3", "Quer um plano simples pra sua semana?")}
CTA: me chama no direct
""".strip()

# =========================
# LOGIN
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.title("🍎 Acesso")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta")
    st.stop()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.session_state.debug_mode = st.toggle("🔎 Debug", value=st.session_state.debug_mode)
    debug_mode = st.session_state.debug_mode

# =========================
# UI
# =========================
st.title(f"🍎 {APP_NAME}")
st.write(APP_TAGLINE)

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form"):
        publico = st.text_input(
            "Público",
            value="Mulheres 25–40 com dificuldade de constância",
            placeholder="Ex: homens 30–45 com rotina corrida"
        )
        st.caption("Quem é + principal dificuldade")
        tema = st.text_input(
            "Tema do post",
            value="Constância alimentar",
            placeholder="Ex: lanche âncora, pré-treino, fome noturna"
        )
        st.caption("1 tema por post")
        modelo = st.selectbox("Modelo de IA", PRIMARY_MODEL_OPTIONS)
        gerar = st.form_submit_button("GERAR POST")

if gerar:
    resp = call_gemini(build_prompt_fill(publico, tema), modelo)
    if resp["ok"]:
        kv = parse_kv(resp["text"])
        st.session_state.car = build_carousel(kv)
        st.session_state.cap = build_caption(kv)
        st.session_state.reels = build_reels(kv)
        st.session_state.stories = build_stories(kv)
        st.session_state.raw = resp["text"]
    else:
        st.error(resp["error"])

with col2:
    tabs = ["🖼️ Carrossel", "✍️ Legenda", "🎬 Reels", "📲 Stories"] + (["🔎 Debug"] if debug_mode else [])
    abas = st.tabs(tabs)

    if "car" in st.session_state:
        abas[0].text_area("Copiar e colar:", st.session_state.car, height=600)
        abas[1].text_area("Copiar e colar:", st.session_state.cap, height=500)
        abas[2].text_area("Copiar e colar:", st.session_state.reels, height=300)
        abas[3].text_area("Copiar e colar:", st.session_state.stories, height=300)
        if debug_mode:
            abas[4].text_area("RAW IA", st.session_state.raw, height=400)
