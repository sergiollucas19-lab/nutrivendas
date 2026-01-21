import streamlit as st
import requests
import uuid
import time

st.set_page_config(page_title="NutriVendas Weekly", page_icon="💎", layout="wide")

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
    semana = st.selectbox("Pacote:", ["Semana 1", "Semana 2", "Semana 3", "Semana 4"])
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= HELPERS =================
def chamar_gemini(prompt, modelo_escolhido, max_output_tokens=1600):
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_output_tokens}
    }

    r = requests.post(url, json=payload, timeout=90)
    if r.status_code != 200:
        return {"ok": False, "error": r.text}

    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"ok": True, "text": text}
    except:
        return {"ok": False, "error": "Resposta inválida do modelo"}

def split_partes(texto):
    partes = {}
    for k in ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6"]:
        tag = f"[{k}]"
        if tag in texto:
            start = texto.index(tag) + len(tag)
            end = len(texto)
            for k2 in ["PARTE1","PARTE2","PARTE3","PARTE4","PARTE5","PARTE6"]:
                if k2 != k and f"[{k2}]" in texto:
                    pos = texto.index(f"[{k2}]")
                    if pos > start:
                        end = min(end, pos)
            partes[k] = texto[start:end].strip()
    return partes

# ================= PROMPT SEMANAL =================
def montar_prompt(nicho, tipo, preco, objetivo, semana):
    return f"""
Você é um(a) estrategista de marketing para nutricionistas.

Crie um PACOTE SEMANAL PRONTO PARA POSTAR (simples, claro, sem exagero).

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana: {semana}

REGRAS:
- Não faça nada complexo.
- Não crie Reels prontos.
- Foque em posts de imagem (carrossel).
- Stories e Reels devem ser apenas IDEIAS.
- Tudo deve ser fácil de copiar e colar.
- Use as tags abaixo exatamente.

ENTREGUE:

[PARTE1] POSICIONAMENTO
- Promessa clara
- Público ideal
- CTA padrão

[PARTE2] BIO
- 2 bios prontas (até 150 caracteres)
- 1 frase para link da bio

[PARTE3] CALENDÁRIO SEMANAL
- Dia 1 a Dia 7 com tipo de post + objetivo

[PARTE4] 4 CARROSSÉIS PRONTOS
Para cada um:
- Tema
- Headline de capa
- Texto de cada slide (7 slides)
- Sugestão de imagem por slide
- Legenda pronta
- CTA
- Hashtags

[PARTE5] IDEIAS DE REELS (5 ideias)
- Tema
- O que falar
- O que mostrar
- Duração sugerida

[PARTE6] IDEIAS DE STORIES (5 sequências)
- Sequência de 3 stories
- Texto sugerido
- Sticker indicado
"""

# ================= LOGIN =================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🔒 Login")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            if senha == st.secrets["ACCESS_PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# ================= APP =================
st.title("💎 NutriVendas Weekly")
st.write("Conteúdo profissional para nutricionistas (rápido e estável).")

if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "rodada" not in st.session_state:
    st.session_state.rodada = str(uuid.uuid4())

col1, col2 = st.columns([1, 2])

with col1:
    with st.form("form"):
        nicho = st.text_input("Nicho", "Emagrecimento")
        tipo = st.selectbox("Atendimento", ["Online", "Presencial"])
        preco = st.text_input("Preço", "R$ 200")
        objetivo = st.selectbox("Objetivo", ["Agenda Cheia", "Vendas"])
        gerar = st.form_submit_button("GERAR PACOTE SEMANAL")

if gerar:
    with st.spinner("Gerando pacote..."):
        prompt = montar_prompt(nicho, tipo, preco, objetivo, semana)
        resp = chamar_gemini(prompt, modelo)

    if resp["ok"]:
        partes = split_partes(resp["text"])
        st.session_state.resultado = partes
    else:
        st.session_state.resultado = {"erro": resp["error"]}

    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

with col2:
    res = st.session_state.resultado
    rodada = st.session_state.rodada

    abas = st.tabs(["🎯 Posicionamento","🔗 Bio","📅 Semana","🖼️ Carrosséis","🎬 Reels","📲 Stories"])

    if res is None:
        st.info("Preencha à esquerda e clique em **GERAR PACOTE SEMANAL**.")
    elif "erro" in res:
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
