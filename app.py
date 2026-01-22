import streamlit as st
import requests
import uuid
import time
import random

# =========================
# CONFIG / BRAND
# =========================
APP_NAME = "Nutri Social Studio"
APP_TAGLINE = "Posts profissionais no padrão agência para nutricionistas — em 1 clique."
PRIMARY_MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-1.5-flash"]

st.set_page_config(page_title=APP_NAME, page_icon="💎", layout="wide")

# Debug seguro
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
debug_mode = st.session_state.debug_mode

# =========================
# CSS (CORRIGIDO)
# =========================
st.markdown("""
<style>
.stApp { background-color:#000000; color:#E0E0E0; }
h1, h2, h3 { color:#D4AF37 !important; font-family:sans-serif; }
p, .stMarkdown { color:#CCCCCC !important; }

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background-color: #0f0f0f !important;
    color: #eaeaea !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}

/* Select */
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #0f0f0f !important;
    color: #eaeaea !important;
    border: 1px solid #2a2a2a !important;
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
    color: #d4af37 !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HASHTAGS FIXAS (PROFISSIONAL)
# =========================
HASHTAGS = {
    "Emagrecimento": [
        "#emagrecimentosaudavel", "#reeducacaoalimentar", "#nutricaofeminina",
        "#dietasemsofrer", "#ansiedadealimentar", "#habitosaudavel",
        "#deficitcalorico", "#nutricionista", "#vidasaudavel", "#comidadeverdade"
    ],
    "Hipertrofia": [
        "#hipertrofia", "#hipertrofiafeminina", "#ganhodemassa", "#treinofeminino",
        "#musculacao", "#nutricao", "#proteina", "#postreino", "#constancia", "#forca"
    ],
    "Nutrição": [
        "#nutricao", "#nutricionista", "#alimentacaosaudavel", "#qualidadedevida",
        "#bemestar", "#rotinasaudavel", "#habitos", "#comidadeverdade", "#saude", "#vidaativa"
    ],
    "SOP": [
        "#sop", "#saudefeminina", "#equilibriohormonal", "#nutricaofuncional",
        "#resistenciaainsulina", "#emagrecimentosaudavel", "#nutricao", "#comidadeverdade",
        "#rotinasaudavel", "#saude"
    ]
}

def pick_hashtags(nicho):
    base = HASHTAGS.get(nicho, HASHTAGS["Nutrição"])
    random.shuffle(base)
    return base[:10]

# =========================
# GEMINI CALL (CURTO = NÃO CORTA)
# =========================
def call_gemini(prompt, model, max_output_tokens=420, timeout=60, retries=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "Configure GOOGLE_API_KEY em Secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.55,
            "maxOutputTokens": int(max_output_tokens)
        }
    }

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code != 200:
                if r.status_code in (429, 500, 503):
                    time.sleep(2 ** (attempt - 1))
                    continue
                return {"ok": False, "error": r.text}

            data = r.json()
            parts = data["candidates"][0]["content"]["parts"]
            return {"ok": True, "text": parts[0]["text"].strip()}

        except Exception as e:
            last_err = e
            time.sleep(2 ** (attempt - 1))

    return {"ok": False, "error": str(last_err)}

# =========================
# TEMPLATE FIXO (AGÊNCIA)
# =========================
FIXOS = {
    "dor": "Você tenta fazer tudo certo, mas trava no emocional e perde a constância.",
    "autoridade": "Não é falta de força de vontade. É estratégia nutricional.",
    "cta": "Salve este post e use na sua semana."
}

# =========================
# PROMPT CURTO (SEGURO)
# =========================
def build_prompt_fill(nicho, publico, tema):
    return f"""
Preencha os campos abaixo com frases curtas e profissionais:

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
Nicho: {nicho}
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
    slides = f"""
SLIDE 1 (CAPA)
{kv.get("CAPA", "3 ajustes simples para emagrecer sem travar")}

SLIDE 2 (DOR)
{FIXOS["dor"]}

SLIDE 3 (EXPLICAÇÃO)
{kv.get("EXPLICACAO", "Constância vem de rotina simples e previsível.")}

SLIDE 4 (AUTORIDADE)
{FIXOS["autoridade"]}

SLIDE 5 (DICA 1)
{kv.get("DICA1", "Monte um prato base: proteína + fibra + carbo simples.")}

SLIDE 6 (DICA 2)
{kv.get("DICA2", "Tenha um lanche âncora para momentos de ansiedade.")}

SLIDE 7 (CTA)
{FIXOS["cta"]}

IMAGENS SUGERIDAS:
1) fundo escuro + título grande
2) pessoa pensativa
3) ícone cérebro + prato
4) jaleco / checklist
5) prato equilibrado
6) lanche simples
7) botão “salvar”
"""
    return slides.strip()

def build_caption(kv, nicho):
    hashtags = " ".join(pick_hashtags(nicho))
    return f"""
LEGENDA

Se você vive no 8 ou 80, esse post é pra você.

{kv.get("MINI_EXPANSAO", "O segredo é reduzir decisões e simplificar a rotina alimentar.")}

Salve e aplique hoje.

HASHTAGS: {hashtags}
""".strip()

def build_reels(kv):
    return f"""
REELS (direção)

Hook: {kv.get("REELS_HOOK", "Quando a ansiedade bate e a fome emocional aparece…")}
Cenas: {kv.get("REELS_CENAS", "1) close no rosto 2s | 2) prato simples | 3) texto na tela")}
Duração: 7–12s
""".strip()

def build_stories(kv):
    return f"""
STORIES (sequência)

Story 1 — {kv.get("STORIES_1", "Ansiedade e dieta brigam todo dia")}
Sticker: enquete

Story 2 — {kv.get("STORIES_2", "O problema não é você")}
Sticker: emoji

Story 3 — {kv.get("STORIES_3", "Quer um plano simples pra sua semana?")}
Sticker: caixinha

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
        st.title("🔒 Acesso")
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
st.title(f"💎 {APP_NAME}")
st.write(APP_TAGLINE)

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form"):
        nicho = st.selectbox("Nicho", ["Emagrecimento", "Hipertrofia", "Nutrição", "SOP"])
        publico = st.text_input("Público", value="Mulheres 25–40 com ansiedade", placeholder="Ex: homens 30–45 com pouco tempo")
        st.caption("Dica: 1 frase curta. Quem é + dor principal.")
        tema = st.text_input("Tema do post", value="Constância alimentar", placeholder="Ex: lanche âncora à noite")
        st.caption("Dica: 1 problema por post.")
        modelo = st.selectbox("Modelo", PRIMARY_MODEL_OPTIONS)
        gerar = st.form_submit_button("GERAR POST")

if gerar:
    resp = call_gemini(build_prompt_fill(nicho, publico, tema), modelo)
    if resp["ok"]:
        kv = parse_kv(resp["text"])
        st.session_state.car = build_carousel(kv)
        st.session_state.cap = build_caption(kv, nicho)
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
        abas[1].text_area("Copiar e colar:", st.session_state.cap, height=600)
        abas[2].text_area("Copiar e colar:", st.session_state.reels, height=400)
        abas[3].text_area("Copiar e colar:", st.session_state.stories, height=400)
        if debug_mode:
            abas[4].text_area("RAW IA", st.session_state.raw, height=400)
