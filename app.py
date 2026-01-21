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
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= HELPERS =================
def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.replace("\x00", "")
    texto = texto.replace("$", " reais ")
    return texto

def cortar(texto, max_chars=30000):
    if len(texto) > max_chars:
        return texto[:max_chars] + "\n\n[conteúdo cortado para evitar travamento no navegador]"
    return texto

def split_partes(texto):
    """Extrai blocos [PARTE1]..[PARTE6] do texto"""
    partes = {}
    chaves = ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6"]
    for i, chave in enumerate(chaves):
        tag = f"[{chave}]"
        if tag in texto:
            start = texto.index(tag) + len(tag)
            end = len(texto)
            for prox in chaves[i+1:]:
                tag2 = f"[{prox}]"
                if tag2 in texto:
                    end = texto.index(tag2)
                    break
            partes[chave] = texto[start:end].strip()
    return partes

def chamar_gemini(prompt, modelo_escolhido, max_output_tokens=1800, timeout_segundos=120, max_tentativas=3):
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

def montar_prompt_semanal(nicho, tipo, preco, objetivo, semana, tom, diferencial):
    return f"""
Você é um(a) Diretor(a) Criativo(a) e Copywriter sênior especializado(a) em marketing para nutricionistas.
Gere um PACOTE SEMANAL "COPIAR E POSTAR" para Instagram, sem ideias vagas.

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana do pacote: {semana}
- Tom de voz: {tom}
- Diferencial: {diferencial}

REGRAS:
- Português (Brasil).
- Conteúdo pronto para copiar e colar.
- Foco em conversão com ética (sem promessas milagrosas).
- Não use tabelas.
- Use as tags EXATAS abaixo.

ENTREGUE:

[PARTE1] POSICIONAMENTO RÁPIDO (1 tela)
- Promessa central (1 frase)
- 5 pilares de conteúdo (bullets)
- CTA padrão (1 frase)

[PARTE2] BIO + DESTAQUES (pronto)
- 2 bios (até 150 caracteres)
- 2 opções de frase para link na bio
- 5 destaques: nome + o que colocar dentro

[PARTE3] CALENDÁRIO 7 DIAS
- Dia 1 a Dia 7: formato (Reels/Carrossel/Stories), objetivo e CTA.

[PARTE4] 3 CARROSSÉIS PRONTOS
Para cada carrossel:
- Headline de capa
- Texto por slide (7 a 9 slides) (escreva o texto exato)
- Sugestão de visual por slide
- Legenda curta + longa
- CTA
- 12 hashtags

[PARTE5] 2 REELS PRONTOS
Para cada Reels:
- Hook (texto na tela 0–2s)
- Roteiro de fala (20–35s) frase a frase
- Cenas/B-roll
- Texto na tela por cena
- Legenda curta + longa
- CTA
- 12 hashtags

[PARTE6] STORIES (sequência pronta)
- 5 stories em sequência para vender o acompanhamento:
  Texto exato + sticker sugerido + CTA
- + Script DM rápido (para “quero saber mais”): 6 mensagens curtas (alternando você/cliente)
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
st.write("Pacote semanal pronto para copiar e postar.")

# Estado
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎯 Configuração")
    with st.form("form_nutri"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        objetivo = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        tom = st.selectbox("Tom de voz", ["Clínico/Profissional", "Leve/Motivacional", "Direto/Sem enrolação"])
        diferencial = st.text_input("Diferencial (1 frase)", "Emagrecimento sem terrorismo nutricional")
        gerar = st.form_submit_button("GERAR PACOTE SEMANAL")

if gerar:
    with st.spinner(f"💎 Gerando pacote {semana}..."):
        prompt = montar_prompt_semanal(nicho, tipo, preco, objetivo, semana, tom, diferencial)
        resp = chamar_gemini(
            prompt,
            modelo_escolhido=modelo,
            max_output_tokens=1900,   # semanal = mais rápido
            timeout_segundos=120,
            max_tentativas=3
        )

    if not resp["ok"]:
        st.session_state.resultado = {"erro": resp["error"]}
    else:
        texto = cortar(limpar_texto(resp["text"]), max_chars=30000)
        partes = split_partes(texto)

        # garante todas as partes
        for chave in ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6"]:
            if chave not in partes:
                partes[chave] = "⚠️ Esta parte não foi retornada. Clique em GERAR novamente."

        st.session_state.resultado = partes

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

# Render sempre
with col2:
    res = st.session_state.resultado
    rodada = st.session_state.rodada

    abas = st.tabs([
        "🎯 Posicionamento",
        "🔗 Bio",
        "📅 Semana",
        "🖼️ Carrosséis",
        "🎬 Reels",
        "📲 Stories + DM"
    ])

    if res is None:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR PACOTE SEMANAL**.")
    elif "erro" in res:
        with abas[0]:
            st.error(res["erro"])
    else:
        mapa = [
            ("PARTE1", 0),
            ("PARTE2", 1),
            ("PARTE3", 2),
            ("PARTE4", 3),
            ("PARTE5", 4),
            ("PARTE6", 5),
        ]
        for chave, idx in mapa:
            with abas[idx]:
                st.text_area(
                    "Copiar e colar:",
                    value=res.get(chave, ""),
                    height=650,
                    key=f"{chave}_{rodada}"
                )
