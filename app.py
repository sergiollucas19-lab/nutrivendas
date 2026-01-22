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
    debug_mode = st.toggle("🔎 Debug (mostrar bruto)", value=False)
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= HELPERS =================
PARTES = ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6"]

def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ")

def cortar(texto, max_chars=28000):
    if len(texto) > max_chars:
        return texto[:max_chars] + "\n\n[conteúdo cortado para evitar travamento]"
    return texto

def split_partes_robusto(texto):
    """
    Split robusto por tags na ordem.
    Se alguma tag não vier, deixa vazio e a UI preenche com aviso.
    """
    out = {k: "" for k in PARTES}
    if not isinstance(texto, str) or not texto.strip():
        return out

    # encontra posições das tags que existem
    tags = []
    for k in PARTES:
        tag = f"[{k}]"
        idx = texto.find(tag)
        if idx != -1:
            tags.append((idx, k, tag))
    tags.sort()

    # se não veio tag nenhuma, joga tudo na PARTE1 pra você ver e não parecer "vazio"
    if not tags:
        out["PARTE1"] = texto.strip()
        return out

    # recorta cada bloco
    for i, (idx, k, tag) in enumerate(tags):
        start = idx + len(tag)
        end = len(texto) if i == len(tags)-1 else tags[i+1][0]
        out[k] = texto[start:end].strip()

    return out

def merge_dict(a, b):
    out = {}
    out.update(a or {})
    out.update(b or {})
    return out

# ================= GEMINI =================
def chamar_gemini(prompt, modelo_escolhido, max_output_tokens=1400, timeout_segundos=120, max_tentativas=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada no st.secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": int(max_output_tokens)
        }
    }

    last_err = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout_segundos)

            if r.status_code != 200:
                # tenta de novo em erros temporários
                if r.status_code in (429, 500, 503):
                    time.sleep(2 ** (tentativa - 1))
                    continue
                return {"ok": False, "error": f"ERRO GOOGLE ({r.status_code}): {r.text}"}

            data = r.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {"ok": False, "error": f"Resposta sem candidates. Retorno: {data}"}

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                return {"ok": False, "error": f"Resposta sem texto. Retorno: {data}"}

            return {"ok": True, "text": parts[0]["text"]}

        except requests.exceptions.ReadTimeout as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))
        except Exception as e:
            last_err = e
            time.sleep(2 ** (tentativa - 1))

    return {"ok": False, "error": f"Timeout/instabilidade após {max_tentativas} tentativas: {last_err}"}

# ================= PROMPTS (2 CHAMADAS LEVES) =================
def prompt_parte1_3(nicho, tipo, preco, objetivo, semana):
    return f"""
Você é um estrategista de marketing para nutricionistas.
Gere um PACOTE SEMANAL PRONTO PARA POSTAR (curto, direto, sem enrolação).

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana: {semana}

REGRAS IMPORTANTES:
- Português (Brasil).
- SEM tabelas.
- Seção curta: no máximo 8 linhas por seção.
- Você DEVE imprimir TODAS as tags [PARTE1], [PARTE2], [PARTE3] mesmo que alguma fique breve.
- Não pare no meio da resposta.

FORMATO OBRIGATÓRIO:

[PARTE1]
(POSICIONAMENTO) Promessa clara (1 frase) + Público ideal (1 frase) + CTA padrão (1 frase)

[PARTE2]
(BIO) 2 bios prontas (até 150 caracteres) + 1 frase para link da bio + 5 destaques (nome + 3 itens do que vai dentro)

[PARTE3]
(CALENDÁRIO 7 DIAS) Dia 1 a Dia 7: formato (Carrossel/Reels/Stories), objetivo e CTA
"""

def prompt_parte4_6(nicho, tipo, preco, objetivo, semana):
    return f"""
Você é um estrategista de conteúdo para Instagram de nutricionistas.
Gere um PACOTE SEMANAL PRONTO PARA POSTAR com foco em POSTS DE IMAGEM (carrossel).
Reels e Stories devem ser APENAS IDEIAS (rápidas).

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana: {semana}

REGRAS IMPORTANTES:
- Português (Brasil).
- SEM tabelas.
- Você DEVE imprimir TODAS as tags [PARTE4], [PARTE5], [PARTE6].
- Não faça Reels prontos (só ideias).
- Não faça Stories prontos longos (só sequência curta).
- Carrosséis: 3 carrosséis por semana (mais rápido e sempre entrega).
- Cada carrossel com 7 slides (texto exato). Slides curtos.

FORMATO OBRIGATÓRIO:

[PARTE4]
(3 CARROSSÉIS PRONTOS)
Carrossel 1:
- Capa:
- Slide 2:
- Slide 3:
- Slide 4:
- Slide 5:
- Slide 6:
- Slide 7 (CTA):
- Sugestão de imagem por slide (1 linha)
- Legenda pronta (curta)
- CTA final (1 frase)
- 10 hashtags

Carrossel 2: (mesma estrutura)
Carrossel 3: (mesma estrutura)

[PARTE5]
(IDEIAS DE REELS – 5)
Para cada ideia: Tema + Hook + O que falar (3 bullets) + O que mostrar (2 bullets) + Duração sugerida

[PARTE6]
(IDEIAS DE STORIES – 5 sequências)
Para cada sequência: Story 1/2/3 (texto curto) + sticker sugerido + CTA
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
st.write("Conteúdo profissional para nutricionistas (rápido, estável e vendável).")

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())
if "raw1" not in st.session_state:
    st.session_state.raw1 = ""
if "raw2" not in st.session_state:
    st.session_state.raw2 = ""

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
    # Chamada 1 (leve)
    with st.spinner("Gerando (1/2) Posicionamento, Bio e Semana..."):
        resp1 = chamar_gemini(
            prompt_parte1_3(nicho, tipo, preco, objetivo, semana),
            modelo_escolhido=modelo,
            max_output_tokens=1100,
            timeout_segundos=120,
            max_tentativas=3
        )

    if not resp1["ok"]:
        st.session_state.resultado = {"erro": resp1["error"]}
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    # Chamada 2 (leve)
    with st.spinner("Gerando (2/2) Carrosséis + Ideias de Reels/Stories..."):
        resp2 = chamar_gemini(
            prompt_parte4_6(nicho, tipo, preco, objetivo, semana),
            modelo_escolhido=modelo,
            max_output_tokens=1600,
            timeout_segundos=120,
            max_tentativas=3
        )

    if not resp2["ok"]:
        st.session_state.resultado = {"erro": resp2["error"]}
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    raw1 = cortar(limpar_texto(resp1["text"]), 26000)
    raw2 = cortar(limpar_texto(resp2["text"]), 26000)

    st.session_state.raw1 = raw1
    st.session_state.raw2 = raw2

    p13 = split_partes_robusto(raw1)  # pega PARTE1..3 (mas robusto se vier sem tags)
    p46 = split_partes_robusto(raw2)  # pega PARTE4..6

    resultado = merge_dict(p13, p46)

    # garante todas as partes existirem (pra não ficar abas vazias)
    for k in PARTES:
        if not resultado.get(k, "").strip():
            resultado[k] = "⚠️ O Gemini não retornou esta parte. Clique em GERAR novamente (instabilidade)."

    st.session_state.resultado = resultado
    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

# ================= UI =================
with col2:
    res = st.session_state.resultado
    rodada = st.session_state.rodada

    nomes_abas = ["🎯 Posicionamento","🔗 Bio","📅 Semana","🖼️ Carrosséis","🎬 Reels (ideias)","📲 Stories (ideias)"]
    if debug_mode:
        nomes_abas.append("🔎 Debug")

    abas = st.tabs(nomes_abas)

    if res is None:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR PACOTE SEMANAL**.")
    elif "erro" in res:
        with abas[0]:
            st.error(res["erro"])
    else:
        mapa = [
            ("PARTE1",0),
            ("PARTE2",1),
            ("PARTE3",2),
            ("PARTE4",3),
            ("PARTE5",4),
            ("PARTE6",5),
        ]
        for k,i in mapa:
            with abas[i]:
                st.text_area("Copiar e colar:", value=res.get(k,""), height=650, key=f"{k}_{rodada}")

        if debug_mode:
            with abas[-1]:
                st.markdown("### Resposta bruta 1 (PARTE1–3)")
                st.text_area("RAW1", value=st.session_state.raw1, height=260, key=f"raw1_{rodada}")
                st.markdown("### Resposta bruta 2 (PARTE4–6)")
                st.text_area("RAW2", value=st.session_state.raw2, height=260, key=f"raw2_{rodada}")
