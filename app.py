import streamlit as st
import requests
import uuid
import time

# ================= CONFIG =================
APP_NAME = "NutriGrowth Studio"  # <- nome do SaaS (mude se quiser)
APP_TAGLINE = "Conteúdo pronto para nutricionistas crescerem no Instagram."

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
    return texto.replace("\x00", "").replace("$", " reais ")

def call_gemini(prompt, modelo_escolhido, max_output_tokens=900, timeout_segundos=90, max_tentativas=3):
    """
    Chamada robusta com retry/backoff.
    Mantém respostas curtas para evitar corte.
    """
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
                # retry em erros temporários
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

def gerar_com_reforco(prompt_base, modelo, tokens, tentativas_conteudo=2):
    """
    Se vier vazio/cortado demais, tenta novamente com reforço de instrução.
    """
    resp = call_gemini(prompt_base, modelo, max_output_tokens=tokens, timeout_segundos=90, max_tentativas=3)
    if not resp["ok"]:
        return resp

    txt = limpar_texto(resp["text"]).strip()
    if len(txt) < 120 and tentativas_conteudo > 1:
        # reforço
        reforco = prompt_base + "\n\nIMPORTANTE: NÃO RESPONDA EM UMA FRASE. ENTREGUE COMPLETO no formato pedido."
        resp2 = call_gemini(reforco, modelo, max_output_tokens=tokens, timeout_segundos=90, max_tentativas=3)
        if resp2["ok"]:
            return {"ok": True, "text": limpar_texto(resp2["text"]).strip()}
        return resp
    return {"ok": True, "text": txt}

# ================= PROMPTS (separados por aba para NÃO CORTAR) =================
def prompt_carrossel(nicho, publico, tema_do_dia):
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
- 7 slides.
- NÃO dê ideias vagas: escreva o texto exato.
- Entregue no formato abaixo, sem texto fora:

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
"""

def prompt_legenda(nicho, publico, tema_do_dia):
    return f"""
Você é um copywriter sênior.
Crie uma LEGENDA PRONTA para o carrossel de hoje (com CTA leve).

Dados:
- Nicho: {nicho}
- Público: {publico}
- Tema do dia: {tema_do_dia}

Regras:
- Até ~700 caracteres.
- Sem promessas milagrosas.
- Inclua 10 hashtags no final (em uma linha).
- Entregue no formato abaixo, sem texto fora:

LEGENDA:
HASHTAGS (10): #... #... #... #... #... #... #... #... #... #...
"""

def prompt_reels_ideias(nicho, publico):
    return f"""
Você é estrategista de conteúdo para Instagram.
Crie 2 IDEIAS de REELS para nutricionista (rápido, simples de executar).

Dados:
- Nicho: {nicho}
- Público: {publico}

Regras:
- Não escreva roteiro completo.
- Entregue no formato abaixo, sem texto fora:

REELS 1 — Tema:
Hook:
O que mostrar (2 bullets):
O que falar (3 bullets):
Duração (sugestão):

REELS 2 — Tema:
Hook:
O que mostrar (2 bullets):
O que falar (3 bullets):
Duração (sugestão):
"""

def prompt_stories_ideias(nicho, publico):
    return f"""
Você é estrategista de conteúdo para Instagram.
Crie 1 sequência de STORIES (3 telas) para nutricionista, só IDEIAS (curto).

Dados:
- Nicho: {nicho}
- Público: {publico}

Regras:
- 3 stories curtos.
- Cada story com: texto + sticker sugerido.
- Entregue no formato abaixo, sem texto fora:

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
for key in ["out_carrossel", "out_legenda", "out_reels", "out_stories", "raw_log"]:
    if key not in st.session_state:
        st.session_state[key] = ""

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Gerar conteúdo")
    with st.form("form_principal"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        publico = st.text_input("Público", "Mulheres 25–40 com ansiedade e compulsão")
        tema_do_dia = st.text_input("Tema do dia (opcional)", "")
        gerar = st.form_submit_button("GERAR CONTEÚDO DE HOJE")

    st.markdown("---")
    st.caption("Dica: quanto mais específico o público, mais “profissional” e menos genérico fica.")

if gerar:
    st.session_state.raw_log = ""

    with st.spinner("Gerando Carrossel..."):
        r1 = gerar_com_reforco(prompt_carrossel(nicho, publico, tema_do_dia), modelo, tokens=950)
        if r1["ok"]:
            st.session_state.out_carrossel = r1["text"]
            st.session_state.raw_log += "\n\n===CARROSSEL===\n" + r1["text"]
        else:
            st.session_state.out_carrossel = "ERRO: " + r1["error"]

    with st.spinner("Gerando Legenda..."):
        r2 = gerar_com_reforco(prompt_legenda(nicho, publico, tema_do_dia), modelo, tokens=650)
        if r2["ok"]:
            st.session_state.out_legenda = r2["text"]
            st.session_state.raw_log += "\n\n===LEGENDA===\n" + r2["text"]
        else:
            st.session_state.out_legenda = "ERRO: " + r2["error"]

    with st.spinner("Gerando ideias de Reels..."):
        r3 = gerar_com_reforco(prompt_reels_ideias(nicho, publico), modelo, tokens=650)
        if r3["ok"]:
            st.session_state.out_reels = r3["text"]
            st.session_state.raw_log += "\n\n===REELS===\n" + r3["text"]
        else:
            st.session_state.out_reels = "ERRO: " + r3["error"]

    with st.spinner("Gerando ideias de Stories..."):
        r4 = gerar_com_reforco(prompt_stories_ideias(nicho, publico), modelo, tokens=500)
        if r4["ok"]:
            st.session_state.out_stories = r4["text"]
            st.session_state.raw_log += "\n\n===STORIES===\n" + r4["text"]
        else:
            st.session_state.out_stories = "ERRO: " + r4["error"]

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

with col2:
    rodada = st.session_state.rodada
    abas = st.tabs(["🖼️ Carrossel pronto", "✍️ Legenda + hashtags", "🎬 Reels (ideias)", "📲 Stories (ideias)"] + (["🔎 Debug"] if debug_mode else []))

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
            st.text_area("RAW LOG", value=st.session_state.raw_log, height=650, key=f"raw_{rodada}")
