import streamlit as st
import requests
import uuid
import time

st.set_page_config(page_title="NutriVendas • Post do Dia", page_icon="💎", layout="wide")

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
    st.header("⚙️ Painel")
    modelo = st.selectbox("Motor:", ["gemini-2.5-flash", "gemini-1.5-flash"])
    debug_mode = st.toggle("🔎 Debug", value=False)
    st.divider()
    st.success("💎 VIP Ativo")

# ================= HELPERS =================
SECTIONS = ["CARROSSEL", "LEGENDA", "REELS_IDEIAS", "STORIES"]

def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ")

def call_gemini(prompt, modelo_escolhido, max_output_tokens=1400, timeout_segundos=90, max_tentativas=3):
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
    raw = raw or ""
    out = {k: "" for k in SECTIONS}
    text = raw.replace("\r\n", "\n")

    positions = []
    for name in SECTIONS:
        marker = f"###{name}###"
        idx = text.find(marker)
        if idx != -1:
            positions.append((idx, name, marker))
    positions.sort()

    if not positions:
        out["CARROSSEL"] = text.strip()
        return out

    for i, (idx, name, marker) in enumerate(positions):
        start = idx + len(marker)
        end = len(text) if i == len(positions) - 1 else positions[i + 1][0]
        out[name] = text[start:end].strip()

    return out

def ensure_not_empty(sections):
    for k in SECTIONS:
        if not sections.get(k, "").strip():
            sections[k] = "⚠️ Não veio conteúdo nessa parte. Clique em GERAR novamente."
    return sections

# ================= PROMPT =================
def build_prompt(nicho, publico):
    return f"""
Você cria conteúdo para Instagram de nutricionistas.
Entregue UM “POST DO DIA” pronto para copiar e postar.

DADOS:
- Nicho: {nicho}
- Público: {publico}

REGRAS:
- Português (Brasil).
- Não use tabelas.
- Nada de “ideias vagas” no carrossel: tem que vir TEXTO PRONTO por slide.
- Carrossel com 7 slides. Texto curto (máx ~120 caracteres por slide).
- Além do texto, diga a “imagem sugerida” para cada slide.
- Reels e Stories podem ser apenas IDEIAS (rápido).
- Responda somente no formato abaixo (com marcadores).

FORMATO OBRIGATÓRIO:

###CARROSSEL###
TEMA:
CAPA:
SLIDE 1:
SLIDE 2:
SLIDE 3:
SLIDE 4:
SLIDE 5:
SLIDE 6:
SLIDE 7 (CTA leve):
IMAGEM SLIDE 1:
IMAGEM SLIDE 2:
IMAGEM SLIDE 3:
IMAGEM SLIDE 4:
IMAGEM SLIDE 5:
IMAGEM SLIDE 6:
IMAGEM SLIDE 7:

###LEGENDA###
(Escreva uma legenda pronta, até ~700 caracteres, com CTA leve no final)
HASHTAGS (10): #... #... #...

###REELS_IDEIAS###
Reels 1 — Tema + Hook + o que mostrar (2 bullets) + o que falar (3 bullets)
Reels 2 — Tema + Hook + o que mostrar (2 bullets) + o que falar (3 bullets)

###STORIES###
Sequência (3 stories):
Story 1 (texto curto) + sticker
Story 2 (texto curto) + sticker
Story 3 (texto curto) + sticker
CTA final (1 frase)
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
                st.error("ACCESS_PASSWORD não configurada no st.secrets.")
            elif senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# ================= APP =================
st.title("💎 NutriVendas • Post do Dia")
st.write("Um clique → um post pronto (carrossel + legenda) + ideias rápidas de Reels e Stories.")

if "sections" not in st.session_state:
    st.session_state.sections = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())
if "raw" not in st.session_state:
    st.session_state.raw = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração simples")
    with st.form("form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        publico = st.text_input("Público (pra não ficar genérico)", "Mulheres 25–40 com ansiedade e compulsão")
        gerar = st.form_submit_button("GERAR POST DO DIA")

if gerar:
    with st.spinner("Gerando conteúdo..."):
        resp = call_gemini(build_prompt(nicho, publico), modelo, max_output_tokens=1500, timeout_segundos=90, max_tentativas=3)

    if not resp["ok"]:
        st.session_state.sections = {"CARROSSEL": f"ERRO: {resp['error']}"}
        st.session_state.raw = ""
    else:
        raw = limpar_texto(resp["text"])
        st.session_state.raw = raw
        secs = extract_sections(raw)
        secs = ensure_not_empty(secs)
        st.session_state.sections = secs

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

with col2:
    rodada = st.session_state.rodada
    secs = st.session_state.sections

    tabs = ["🖼️ Carrossel (pronto)", "✍️ Legenda + Hashtags", "🎬 Reels (ideias)", "📲 Stories (ideias)"]
    if debug_mode:
        tabs.append("🔎 Debug")

    abas = st.tabs(tabs)

    if secs is None:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR POST DO DIA**.")
    else:
        with abas[0]:
            st.text_area("Copiar e colar:", value=secs.get("CARROSSEL", ""), height=650, key=f"car_{rodada}")
        with abas[1]:
            st.text_area("Copiar e colar:", value=secs.get("LEGENDA", ""), height=650, key=f"leg_{rodada}")
        with abas[2]:
            st.text_area("Copiar e colar:", value=secs.get("REELS_IDEIAS", ""), height=650, key=f"reels_{rodada}")
        with abas[3]:
            st.text_area("Copiar e colar:", value=secs.get("STORIES", ""), height=650, key=f"stories_{rodada}")

        if debug_mode:
            with abas[-1]:
                st.markdown("### Resposta bruta (quando cortar)")
                st.text_area("RAW", value=st.session_state.raw, height=650, key=f"raw_{rodada}")
