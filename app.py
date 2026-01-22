import streamlit as st
import requests
import uuid
import time

# ================= CONFIG =================
APP_NAME = "NutriGrowth Studio"
APP_TAGLINE = "Conteúdo pronto e consistente para nutricionistas crescerem no Instagram."

st.set_page_config(page_title=APP_NAME, page_icon="💎", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.stApp { background-color:#000000; color:#E0E0E0; }
h1, h2, h3 { color:#D4AF37 !important; font-family:sans-serif; }
p, .stMarkdown, label { color:#CCCCCC !important; }
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.header("⚙️ Configurações")
    modelo = st.selectbox("Modelo:", ["gemini-2.5-flash", "gemini-1.5-flash"])
    debug_mode = st.toggle("🔎 Debug", value=False)
    st.divider()
    st.success("💎 Premium Ativo")

# ================= HELPERS =================
def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ").strip()

def call_gemini(prompt, modelo_escolhido, max_output_tokens=900, timeout_segundos=120, max_tentativas=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada no st.secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.65,
            "maxOutputTokens": int(max_output_tokens),
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

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts or "text" not in parts[0]:
                return {"ok": False, "error": f"Sem texto. Retorno: {data}"}

            text = parts[0]["text"]
            finish = candidates[0].get("finishReason", "")  # ex: "MAX_TOKENS"
            return {"ok": True, "text": limpar_texto(text), "finish_reason": finish}

        except requests.exceptions.ReadTimeout as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))
        except Exception as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))

    return {"ok": False, "error": f"Timeout/instabilidade após {max_tentativas} tentativas: {last_err}"}

def looks_incomplete(text: str, required_markers: list[str]) -> bool:
    if not text or len(text) < 80:
        return True
    for m in required_markers:
        if m not in text:
            return True
    # se termina “no meio” sem quebrar linha, costuma ser corte
    if len(text) > 0 and text[-1] not in [".", "!", "?", "\n"]:
        return True
    return False

def generate_with_continuation(prompt_base, modelo_escolhido, required_markers, max_tokens=900, max_steps=3):
    """
    Gera texto e, se cortar/faltar marcador, pede continuação automaticamente.
    """
    full = ""
    debug = []

    prompt = prompt_base
    for step in range(1, max_steps + 1):
        resp = call_gemini(prompt, modelo_escolhido, max_output_tokens=max_tokens, timeout_segundos=120, max_tentativas=3)
        if not resp["ok"]:
            return {"ok": False, "error": resp["error"], "text": full, "debug": "\n".join(debug)}

        piece = resp["text"].strip()
        finish = resp.get("finish_reason", "")
        debug.append(f"[step {step}] finish_reason={finish}\n{piece}\n")

        # concatena com cuidado pra não colar linhas
        if full:
            if not full.endswith("\n"):
                full += "\n"
            full += piece
        else:
            full = piece

        # valida completude
        incomplete = looks_incomplete(full, required_markers)
        if not incomplete and finish != "MAX_TOKENS":
            return {"ok": True, "text": full.strip(), "debug": "\n".join(debug)}

        # prepara continuação
        prompt = (
            "CONTINUE exatamente de onde parou.\n"
            "NÃO repita nada.\n"
            "Mantenha o mesmo formato e complete os campos restantes até o fim.\n\n"
            "CONTEÚDO ATUAL (não repita, apenas continue):\n"
            f"{full}\n"
        )

    # se chegou aqui, devolve o que conseguiu
    return {"ok": True, "text": full.strip(), "debug": "\n".join(debug)}

# ================= PROMPTS (CARROSSEL EM 2 PARTES) =================
def prompt_carrossel_p1(nicho, publico, tema_do_dia):
    return f"""
Você é um copywriter sênior de Instagram para nutricionistas.
Crie 1 CARROSSEL PRONTO para postar HOJE.

Dados:
- Nicho: {nicho}
- Público: {publico}
- Tema do dia (se houver): {tema_do_dia}

Regras:
- Português (Brasil).
- Texto curto e postável (até ~120 caracteres por slide).
- Não faça ideias vagas: escreva o texto exato.
- Entregue SOMENTE no formato abaixo:

TEMA:
CAPA:
SLIDE 1:
SLIDE 2:
SLIDE 3:
SLIDE 4:
IMAGEM SLIDE 1:
IMAGEM SLIDE 2:
IMAGEM SLIDE 3:
IMAGEM SLIDE 4:
"""

def prompt_carrossel_p2(nicho, publico, tema_do_dia, contexto_p1):
    return f"""
Você está continuando o mesmo carrossel.
NÃO repita TEMA, CAPA, SLIDES 1-4 ou IMAGENS 1-4.
Apenas complete a PARTE 2 no formato abaixo.

Contexto já feito (não repetir):
{contexto_p1}

FORMATO (SOMENTE ISSO):
SLIDE 5:
SLIDE 6:
SLIDE 7 (CTA leve):
IMAGEM SLIDE 5:
IMAGEM SLIDE 6:
IMAGEM SLIDE 7:
"""

def prompt_legenda(nicho, publico, tema_do_dia):
    return f"""
Você é um copywriter sênior.
Crie uma LEGENDA PRONTA para o carrossel de hoje (CTA leve).

Dados:
- Nicho: {nicho}
- Público: {publico}
- Tema do dia: {tema_do_dia}

Regras:
- Até ~700 caracteres.
- Inclua 10 hashtags no final (uma linha).
- Entregue SOMENTE no formato abaixo:

LEGENDA:
HASHTAGS (10): #... #... #... #... #... #... #... #... #... #...
"""

def prompt_reels_ideias(nicho, publico):
    return f"""
Você é estrategista de conteúdo.
Crie 2 IDEIAS de REELS para nutricionista (simples, executável).

Dados:
- Nicho: {nicho}
- Público: {publico}

Entregue SOMENTE no formato abaixo:

REELS 1 — Tema:
Hook:
O que mostrar (2 bullets):
- ...
- ...
O que falar (3 bullets):
- ...
- ...
- ...
Duração (sugestão):

REELS 2 — Tema:
Hook:
O que mostrar (2 bullets):
- ...
- ...
O que falar (3 bullets):
- ...
- ...
- ...
Duração (sugestão):
"""

def prompt_stories_ideias(nicho, publico):
    return f"""
Você é estrategista de conteúdo.
Crie 1 sequência de STORIES (3 telas) para nutricionista.

Dados:
- Nicho: {nicho}
- Público: {publico}

Entregue SOMENTE no formato abaixo:

STORY 1 (texto):
Sticker:
STORY 2 (texto):
Sticker:
STORY 3 (texto):
Sticker:
CTA final (1 frase):
"""

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.title("🔒 Acesso")
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

# ================= APP UI =================
st.title(f"💎 {APP_NAME}")
st.write(APP_TAGLINE)

if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())

# outputs
for k in ["out_carrossel", "out_legenda", "out_reels", "out_stories", "raw_debug"]:
    if k not in st.session_state:
        st.session_state[k] = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Gerar conteúdo de hoje")
    with st.form("form_principal"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        publico = st.text_input("Público", "Mulheres 25–40 com ansiedade e compulsão")
        tema_do_dia = st.text_input("Tema do dia (opcional)", "")
        gerar = st.form_submit_button("GERAR")

    st.caption("Quanto mais específico o público, mais profissional e menos genérico fica.")

if gerar:
    st.session_state.raw_debug = ""

    # ===== CARROSSEL (2 PARTES + continuação) =====
    with st.spinner("Gerando carrossel (parte 1)..."):
        p1 = generate_with_continuation(
            prompt_carrossel_p1(nicho, publico, tema_do_dia),
            modelo,
            required_markers=["TEMA:", "CAPA:", "SLIDE 1:", "SLIDE 4:", "IMAGEM SLIDE 4:"],
            max_tokens=800,
            max_steps=3
        )

    if not p1["ok"]:
        st.session_state.out_carrossel = "ERRO: " + p1["error"]
        st.session_state.raw_debug += "\n\n===CARROSSEL P1 ERRO===\n" + p1["error"]
    else:
        with st.spinner("Gerando carrossel (parte 2)..."):
            p2 = generate_with_continuation(
                prompt_carrossel_p2(nicho, publico, tema_do_dia, p1["text"]),
                modelo,
                required_markers=["SLIDE 5:", "SLIDE 7", "IMAGEM SLIDE 7:"],
                max_tokens=700,
                max_steps=3
            )

        carrossel_final = p1["text"].strip() + "\n\n" + (p2["text"].strip() if p2["ok"] else "")
        st.session_state.out_carrossel = carrossel_final.strip()

        st.session_state.raw_debug += "\n\n===CARROSSEL P1===\n" + p1.get("debug", "")
        st.session_state.raw_debug += "\n\n===CARROSSEL P2===\n" + (p2.get("debug", "") if isinstance(p2, dict) else "")

    # ===== LEGENDA =====
    with st.spinner("Gerando legenda..."):
        leg = generate_with_continuation(
            prompt_legenda(nicho, publico, tema_do_dia),
            modelo,
            required_markers=["LEGENDA:", "HASHTAGS (10):"],
            max_tokens=650,
            max_steps=3
        )
        st.session_state.out_legenda = leg["text"] if leg["ok"] else ("ERRO: " + leg["error"])
        st.session_state.raw_debug += "\n\n===LEGENDA===\n" + leg.get("debug", "")

    # ===== REELS =====
    with st.spinner("Gerando ideias de Reels..."):
        reels = generate_with_continuation(
            prompt_reels_ideias(nicho, publico),
            modelo,
            required_markers=["REELS 1", "REELS 2", "Duração"],
            max_tokens=750,
            max_steps=3
        )
        st.session_state.out_reels = reels["text"] if reels["ok"] else ("ERRO: " + reels["error"])
        st.session_state.raw_debug += "\n\n===REELS===\n" + reels.get("debug", "")

    # ===== STORIES =====
    with st.spinner("Gerando ideias de Stories..."):
        stories = generate_with_continuation(
            prompt_stories_ideias(nicho, publico),
            modelo,
            required_markers=["STORY 1", "STORY 2", "STORY 3", "CTA final"],
            max_tokens=550,
            max_steps=3
        )
        st.session_state.out_stories = stories["text"] if stories["ok"] else ("ERRO: " + stories["error"])
        st.session_state.raw_debug += "\n\n===STORIES===\n" + stories.get("debug", "")

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

with col2:
    rodada = st.session_state.rodada
    tabs = ["🖼️ Carrossel pronto", "✍️ Legenda + hashtags", "🎬 Reels (ideias)", "📲 Stories (ideias)"]
    if debug_mode:
        tabs.append("🔎 Debug")

    abas = st.tabs(tabs)

    with abas[0]:
        st.text_area("Copiar e colar:", value=st.session_state.out_carrossel, height=650, key=f"car_{rodada}")
    with abas[1]:
        st.text_area("Copiar e colar:", value=st.session_state.out_legenda, height=650, key=f"leg_{rodada}")
    with abas[2]:
        st.text_area("Copiar e colar:", value=st.session_state.out_reels, height=650, key=f"reels_{rodada}")
    with abas[3]:
        st.text_area("Copiar e colar:", value=st.session_state.out_stories, height=650, key=f"stories_{rodada}")

    if debug_mode:
        with abas[4]:
            st.text_area("RAW DEBUG (passo a passo do que o modelo devolveu)", value=st.session_state.raw_debug, height=650, key=f"dbg_{rodada}")
