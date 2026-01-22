import streamlit as st
import requests
import uuid
import time
import random

# =========================
# CONFIG / BRAND
# =========================
APP_NAME = "NutriContent Pro"
APP_TAGLINE = "Conteúdo profissional para nutricionistas — sem pensar, sem travar."
PRIMARY_MODEL_OPTIONS = ["gemini-2.5-flash", "gemini-1.5-flash"]

st.set_page_config(page_title=APP_NAME, page_icon="💎", layout="wide")

# Debug seguro (evita NameError)
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
debug_mode = st.session_state.debug_mode

# =========================
# CSS
# =========================
st.markdown("""
<style>
.stApp { background-color:#000000; color:#E0E0E0; }
h1, h2, h3 { color:#D4AF37 !important; font-family:sans-serif; }
p, .stMarkdown, label, div { color:#CCCCCC !important; }
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# HASHTAGS (FIXAS, PROFISSIONAIS)
# =========================
HASHTAGS = {
    "Emagrecimento": [
        "#emagrecimentosaudavel", "#reeducacaoalimentar", "#nutricaofeminina", "#nutrição",
        "#dietasemsofrer", "#habitosaudavel", "#comidadeverdade", "#deficitcalorico",
        "#ansiedadealimentar", "#vidasaudavel"
    ],
    "Hipertrofia": [
        "#hipertrofia", "#hipertrofiafeminina", "#ganhodemassa", "#nutricao",
        "#treinofeminino", "#musculacao", "#proteina", "#pretreino", "#postreino",
        "#constancia"
    ],
    "Nutrição": [
        "#nutricao", "#nutricionista", "#saude", "#alimentacaosaudavel", "#qualidadedevida",
        "#comidadeverdade", "#rotinasaudavel", "#bemestar", "#saudemental", "#habitos"
    ],
    "SOP": [
        "#sop", "#sopnaoedefrescura", "#nutricaofuncional", "#saudefeminina", "#equilibriohormonal",
        "#resistenciaainsulina", "#comidadeverdade", "#rotinasaudavel", "#emagrecimentosaudavel",
        "#nutricao"
    ]
}

def pick_hashtags(nicho: str):
    base = HASHTAGS.get(nicho, HASHTAGS["Nutrição"])
    base2 = base[:]
    random.shuffle(base2)
    return base2[:10]

# =========================
# GEMINI CALL (ROBUSTO)
# =========================
def call_gemini(prompt, model, max_output_tokens=420, timeout=60, retries=3):
    """
    Resposta curta e estruturada -> não corta.
    """
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "Configure GOOGLE_API_KEY em Settings > Secrets."}

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
                return {"ok": False, "error": f"Google {r.status_code}: {r.text}"}

            data = r.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {"ok": False, "error": f"Sem resposta: {data}"}

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                return {"ok": False, "error": f"Resposta inválida: {data}"}

            text = parts[0]["text"]
            return {"ok": True, "text": text.strip()}

        except Exception as e:
            last_err = e
            time.sleep(2 ** (attempt - 1))

    return {"ok": False, "error": f"Falha após {retries} tentativas: {last_err}"}

# =========================
# TEMPLATE FIXO (PADRÃO AGÊNCIA)
# =========================
CAROUSEL_TEMPLATE = [
    "SLIDE 1 (CAPA)\n{capa}",
    "SLIDE 2 (DOR)\n{dor}",
    "SLIDE 3 (EXPLICAÇÃO)\n{explicacao}",
    "SLIDE 4 (AUTORIDADE)\n{autoridade}",
    "SLIDE 5 (DICA 1)\n{dica1}",
    "SLIDE 6 (DICA 2)\n{dica2}",
    "SLIDE 7 (CTA)\n{cta}"
]

FIXOS = {
    "dor": "Você tenta fazer tudo certo, mas trava no emocional e perde a constância.",
    "autoridade": "Não é falta de força de vontade. É estratégia nutricional + ambiente.",
    "cta": "Salve este post e use na sua semana. Quer um plano guiado? Me chama no direct."
}

# =========================
# PROMPT CURTO (IA SÓ PREENCHE)
# =========================
def build_prompt_fill(nicho, publico, tema):
    return f"""
Você é um nutricionista e estrategista de marketing no Instagram.
Preencha os campos abaixo com respostas CURTAS, PRÁTICAS e POSTÁVEIS.

Contexto:
- Nicho: {nicho}
- Público: {publico}
- Tema do conteúdo: {tema}

Regras:
- Sem texto extra fora do formato.
- Cada linha até ~120 caracteres.
- Linguagem simples, profissional e direta.

FORMATO OBRIGATÓRIO:
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
"""

# =========================
# BUILD OUTPUTS
# =========================
def parse_kv(text):
    out = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().upper()] = v.strip()
    return out

def build_carousel(kv):
    capa = kv.get("CAPA", "3 ajustes para ganhar massa sem travar no emocional")
    explicacao = kv.get("EXPLICACAO", "Constância vem de rotina simples: proteína + fibra + sono. Sem isso, você volta pro 8 ou 80.")
    dica1 = kv.get("DICA1", "Pré-treino: proteína + carbo simples (ex: iogurte + banana). Evita queda de energia e belisco.")
    dica2 = kv.get("DICA2", "Lanche âncora: escolha 1 opção fixa p/ ansiedade (ex: fruta + castanhas). Menos decisão = mais constância.")
    dor = FIXOS["dor"]
    autoridade = FIXOS["autoridade"]
    cta = FIXOS["cta"]

    slides = "\n\n".join([
        CAROUSEL_TEMPLATE[0].format(capa=capa),
        CAROUSEL_TEMPLATE[1].format(dor=dor),
        CAROUSEL_TEMPLATE[2].format(explicacao=explicacao),
        CAROUSEL_TEMPLATE[3].format(autoridade=autoridade),
        CAROUSEL_TEMPLATE[4].format(dica1=dica1),
        CAROUSEL_TEMPLATE[5].format(dica2=dica2),
        CAROUSEL_TEMPLATE[6].format(cta=cta),
    ])

    imagens = "\n".join([
        "IMAGENS SUGERIDAS:",
        "Slide 1: fundo preto + título dourado + ícone (halter/prato)",
        "Slide 2: pessoa pensativa + fundo escuro",
        "Slide 3: ícone cérebro + prato simples",
        "Slide 4: jaleco/checklist/consultório",
        "Slide 5: prato montado (proteína+carbo+fibra)",
        "Slide 6: lanche prático (iogurte/fruta/castanhas)",
        "Slide 7: CTA com ícone 'Salvar' + Direct"
    ])

    return slides + "\n\n" + imagens

def build_caption(kv, nicho):
    mini = kv.get("MINI_EXPANSAO", "O segredo é reduzir decisões: rotina simples, comida previsível e um plano que caiba na vida.")
    hashtags = " ".join(pick_hashtags(nicho))

    caption = (
        "LEGENDA (copiar e colar)\n"
        "Se você vive no 8 ou 80 (foco total ➝ ansiedade ➝ chute o balde), esse post é pra você.\n\n"
        f"{mini}\n\n"
        "Salve e aplique hoje. Se quiser ajuda guiada, me chama no direct.\n\n"
        f"HASHTAGS: {hashtags}"
    )
    return caption

def build_reels(kv):
    hook = kv.get("REELS_HOOK", "Quando a ansiedade bate e a fome emocional aparece…")
    cenas = kv.get("REELS_CENAS", "1) close no rosto 2s | 2) prato simples | 3) texto na tela | 4) você aponta 2 dicas")
    return (
        "REELS (direção — fácil de gravar)\n"
        f"Hook (texto na tela): {hook}\n"
        f"Cenas (rápido): {cenas}\n"
        "Fala (curta): “Não é falta de disciplina. É estratégia. Salva e me chama se quiser um plano.”\n"
        "Duração: 7–12s\n"
    )

def build_stories(kv):
    s1 = kv.get("STORIES_1", "Você sente que a ansiedade estraga sua dieta?")
    s2 = kv.get("STORIES_2", "O problema não é você. É falta de estratégia + rotina caótica.")
    s3 = kv.get("STORIES_3", "Quer que eu te mostre um plano simples pra sua semana?")

    return (
        "STORIES (sequência pronta)\n"
        f"Story 1 — Imagem: rotina real / café da manhã\nTexto: {s1}\nSticker: Enquete (SIM/SEMPRE)\n\n"
        f"Story 2 — Imagem: prato simples\nTexto: {s2}\nSticker: Emoji slider (🔥)\n\n"
        f"Story 3 — Imagem: você falando\nTexto: {s3}\nSticker: Caixinha (“me fala seu maior desafio”)\n\n"
        "CTA final: Responde aqui ou me chama no direct que eu te digo o primeiro passo."
    )

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
            if "ACCESS_PASSWORD" not in st.secrets:
                st.error("ACCESS_PASSWORD não configurada em Secrets.")
            elif senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# =========================
# SIDEBAR (toggle debug com session_state)
# =========================
with st.sidebar:
    st.markdown("---")
    st.session_state.debug_mode = st.toggle("🔎 Debug", value=st.session_state.debug_mode)
    debug_mode = st.session_state.debug_mode

# =========================
# UI
# =========================
st.title(f"💎 {APP_NAME}")
st.write(APP_TAGLINE)

if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())

for k in ["out_car", "out_cap", "out_reels", "out_stories", "raw_debug"]:
    if k not in st.session_state:
        st.session_state[k] = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Gerar conteúdo")
    with st.form("form"):
        nicho = st.selectbox("Nicho", ["Emagrecimento", "Hipertrofia", "Nutrição", "SOP"])
        publico = st.text_input("Público", "Mulheres 25–40 com ansiedade e compulsão")
        tema = st.text_input("Tema do conteúdo", "Hipertrofia com ansiedade (constância)")
        modelo_escolhido = st.selectbox("Modelo (IA)", PRIMARY_MODEL_OPTIONS)
        gerar = st.form_submit_button("GERAR CONTEÚDO")

if gerar:
    prompt = build_prompt_fill(nicho, publico, tema)

    with st.spinner("Gerando conteúdo (preenchimentos curtos)…"):
        resp = call_gemini(prompt, modelo_escolhido, max_output_tokens=420, timeout=60, retries=3)

    if not resp["ok"]:
        st.session_state.out_car = "ERRO: " + resp["error"]
        st.session_state.out_cap = ""
        st.session_state.out_reels = ""
        st.session_state.out_stories = ""
        st.session_state.raw_debug = ""
    else:
        raw = resp["text"]
        kv = parse_kv(raw)

        st.session_state.out_car = build_carousel(kv)
        st.session_state.out_cap = build_caption(kv, nicho)
        st.session_state.out_reels = build_reels(kv)
        st.session_state.out_stories = build_stories(kv)
        st.session_state.raw_debug = raw

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

with col2:
    rodada = st.session_state.rodada
    tabs = ["🖼️ Carrossel", "✍️ Legenda + Hashtags", "🎬 Reels (direção)", "📲 Stories (direção)"]
    if debug_mode:
        tabs.append("🔎 Debug")

    abas = st.tabs(tabs)

    with abas[0]:
        st.text_area("Copiar e colar:", value=st.session_state.out_car, height=650, key=f"car_{rodada}")
    with abas[1]:
        st.text_area("Copiar e colar:", value=st.session_state.out_cap, height=650, key=f"cap_{rodada}")
    with abas[2]:
        st.text_area("Copiar e colar:", value=st.session_state.out_reels, height=650, key=f"reels_{rodada}")
    with abas[3]:
        st.text_area("Copiar e colar:", value=st.session_state.out_stories, height=650, key=f"stories_{rodada}")

    if debug_mode:
        with abas[4]:
            st.text_area("Resposta bruta da IA (preenchimentos):", value=st.session_state.raw_debug, height=650, key=f"dbg_{rodada}")
