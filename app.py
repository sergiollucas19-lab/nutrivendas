import streamlit as st
import requests
import uuid
import time
import json

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
    debug_mode = st.toggle("🔎 Debug (ver bruto/JSON)", value=False)
    st.divider()
    st.success("💎 Status: VIP Ativo")

# ================= HELPERS =================
def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ")

def call_gemini_text(prompt, modelo_escolhido, max_output_tokens=2000, timeout_segundos=120, max_tentativas=3):
    """Chama Gemini e retorna texto. Com retry/backoff."""
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada no st.secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": int(max_output_tokens)
        }
    }

    last_err = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout_segundos)
            if r.status_code != 200:
                # erros temporários
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

def extract_json_block(s: str):
    """Extrai o primeiro bloco JSON { ... } do texto (se o modelo embrulhar com texto)."""
    if not s:
        return None
    s = s.strip()

    # se já é json puro
    if s.startswith("{") and s.endswith("}"):
        return s

    # tenta achar o primeiro { e o último }
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        return s[first:last+1]
    return None

def safe_json_loads(maybe_json: str):
    try:
        return json.loads(maybe_json)
    except:
        return None

def format_carrossel_text(car):
    """Transforma um carrossel (dict) em texto pronto pra copiar."""
    tema = car.get("tema","").strip()
    capa = car.get("capa","").strip()
    slides = car.get("slides", []) or []
    imagens = car.get("imagens", []) or []
    legenda = car.get("legenda","").strip()
    cta = car.get("cta","").strip()
    hashtags = car.get("hashtags", []) or []

    out = []
    out.append(f"TEMA: {tema}")
    out.append(f"CAPA: {capa}")
    out.append("")
    for i, txt in enumerate(slides, start=1):
        out.append(f"SLIDE {i}: {txt}")
        if i-1 < len(imagens):
            out.append(f"  (Imagem sugerida: {imagens[i-1]})")
    out.append("")
    out.append("LEGENDA (copiar e colar):")
    out.append(legenda)
    out.append("")
    out.append(f"CTA: {cta}")
    out.append("")
    out.append("HASHTAGS:")
    out.append(" ".join(hashtags))
    return "\n".join(out).strip()

def dict_to_text_posicionamento(d):
    return "\n".join([
        f"Promessa: {d.get('promessa','')}",
        f"Público ideal: {d.get('publico','')}",
        f"CTA padrão: {d.get('cta','')}"
    ]).strip()

def dict_to_text_bio(d):
    bios = d.get("bios", []) or []
    destaques = d.get("destaques", []) or []
    link = d.get("link_bio","")
    out = []
    out.append("BIOS:")
    for i,b in enumerate(bios, start=1):
        out.append(f"{i}) {b}")
    out.append("")
    out.append(f"Link na bio: {link}")
    out.append("")
    out.append("Destaques (nome → conteúdo):")
    for item in destaques:
        # item pode vir como dict ou string
        if isinstance(item, dict):
            out.append(f"- {item.get('nome','')}: {', '.join(item.get('conteudo',[]) or [])}")
        else:
            out.append(f"- {item}")
    return "\n".join(out).strip()

def calendario_to_text(lst):
    out = []
    for it in lst or []:
        # it esperado: {dia, formato, objetivo, cta}
        out.append(f"{it.get('dia','Dia')}: {it.get('formato','')} | {it.get('objetivo','')} | CTA: {it.get('cta','')}")
    return "\n".join(out).strip()

def reels_to_text(lst):
    out = []
    for i,it in enumerate(lst or [], start=1):
        out.append(f"REELS {i} — Tema: {it.get('tema','')}")
        out.append(f"Hook: {it.get('hook','')}")
        falar = it.get("falar", []) or []
        mostrar = it.get("mostrar", []) or []
        out.append("O que falar:")
        for b in falar:
            out.append(f"- {b}")
        out.append("O que mostrar:")
        for b in mostrar:
            out.append(f"- {b}")
        out.append(f"Duração: {it.get('duracao','')}")
        out.append("")
    return "\n".join(out).strip()

def stories_to_text(lst):
    out = []
    for i,it in enumerate(lst or [], start=1):
        out.append(f"SEQUÊNCIA {i}: {it.get('tema','')}")
        seq = it.get("sequencia", []) or []
        for j,s in enumerate(seq, start=1):
            out.append(f"Story {j}: {s.get('texto','')}")
            out.append(f"  Sticker: {s.get('sticker','')}")
        out.append(f"CTA: {it.get('cta','')}")
        out.append("")
    return "\n".join(out).strip()

# ================= PROMPTS =================
def build_prompt_weekly_json(nicho, tipo, preco, objetivo, semana):
    return f"""
Você é um especialista em marketing para nutricionistas.

Gere UM PACOTE SEMANAL para Instagram com foco em "COPIAR E POSTAR" (texto pronto).
Reels e Stories devem ser APENAS IDEIAS (não roteiros completos).

DADOS:
- Nicho: {nicho}
- Atendimento: {tipo}
- Preço: {preco}
- Objetivo: {objetivo}
- Semana: {semana}

REGRAS IMPORTANTES (OBRIGATÓRIAS):
- Responda SOMENTE com JSON válido. Sem markdown. Sem texto fora do JSON.
- Use exatamente as chaves abaixo.
- Carrosséis: 3 carrosséis.
- Cada carrossel: 7 slides com texto FINAL (curto, direto, pronto).
- Cada slide: máximo ~120 caracteres (para caber em arte).
- Sugira "imagens" como descrição do que colocar no slide (foto/ícone/ilustração).
- Legenda: pronta para copiar e colar (curta, até ~700 caracteres).
- Hashtags: 10 hashtags.

ESQUEMA JSON (use exatamente):
{{
  "posicionamento": {{
    "promessa": "…",
    "publico": "…",
    "cta": "…"
  }},
  "bio": {{
    "bios": ["…", "…"],
    "link_bio": "…",
    "destaques": [
      {{"nome":"…","conteudo":["…","…","…"]}},
      {{"nome":"…","conteudo":["…","…","…"]}},
      {{"nome":"…","conteudo":["…","…","…"]}},
      {{"nome":"…","conteudo":["…","…","…"]}},
      {{"nome":"…","conteudo":["…","…","…"]}}
    ]
  }},
  "calendario": [
    {{"dia":"Dia 1","formato":"Carrossel","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 2","formato":"Stories","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 3","formato":"Reels","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 4","formato":"Carrossel","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 5","formato":"Stories","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 6","formato":"Carrossel","objetivo":"…","cta":"…"}},
    {{"dia":"Dia 7","formato":"Stories","objetivo":"…","cta":"…"}}
  ],
  "carrosseis": [
    {{
      "tema":"…",
      "capa":"…",
      "slides":["…","…","…","…","…","…","…"],
      "imagens":["…","…","…","…","…","…","…"],
      "legenda":"…",
      "cta":"…",
      "hashtags":["#…","#…","#…","#…","#…","#…","#…","#…","#…","#…"]
    }},
    {{
      "tema":"…",
      "capa":"…",
      "slides":["…","…","…","…","…","…","…"],
      "imagens":["…","…","…","…","…","…","…"],
      "legenda":"…",
      "cta":"…",
      "hashtags":["#…","#…","#…","#…","#…","#…","#…","#…","#…","#…"]
    }},
    {{
      "tema":"…",
      "capa":"…",
      "slides":["…","…","…","…","…","…","…"],
      "imagens":["…","…","…","…","…","…","…"],
      "legenda":"…",
      "cta":"…",
      "hashtags":["#…","#…","#…","#…","#…","#…","#…","#…","#…","#…"]
    }}
  ],
  "reels_ideias": [
    {{"tema":"…","hook":"…","falar":["…","…","…"],"mostrar":["…","…"],"duracao":"15-25s"}},
    {{"tema":"…","hook":"…","falar":["…","…","…"],"mostrar":["…","…"],"duracao":"15-25s"}},
    {{"tema":"…","hook":"…","falar":["…","…","…"],"mostrar":["…","…"],"duracao":"15-25s"}},
    {{"tema":"…","hook":"…","falar":["…","…","…"],"mostrar":["…","…"],"duracao":"15-25s"}},
    {{"tema":"…","hook":"…","falar":["…","…","…"],"mostrar":["…","…"],"duracao":"15-25s"}}
  ],
  "stories_ideias": [
    {{
      "tema":"…",
      "sequencia":[
        {{"texto":"…","sticker":"Enquete"}},
        {{"texto":"…","sticker":"Caixinha"}},
        {{"texto":"…","sticker":"Pergunta"}}
      ],
      "cta":"…"
    }},
    {{
      "tema":"…",
      "sequencia":[
        {{"texto":"…","sticker":"Quiz"}},
        {{"texto":"…","sticker":"Enquete"}},
        {{"texto":"…","sticker":"Caixinha"}}
      ],
      "cta":"…"
    }},
    {{
      "tema":"…",
      "sequencia":[
        {{"texto":"…","sticker":"Enquete"}},
        {{"texto":"…","sticker":"Quiz"}},
        {{"texto":"…","sticker":"Caixinha"}}
      ],
      "cta":"…"
    }},
    {{
      "tema":"…",
      "sequencia":[
        {{"texto":"…","sticker":"Enquete"}},
        {{"texto":"…","sticker":"Pergunta"}},
        {{"texto":"…","sticker":"Caixinha"}}
      ],
      "cta":"…"
    }},
    {{
      "tema":"…",
      "sequencia":[
        {{"texto":"…","sticker":"Quiz"}},
        {{"texto":"…","sticker":"Enquete"}},
        {{"texto":"…","sticker":"Pergunta"}}
      ],
      "cta":"…"
    }}
  ]
}}
"""

def build_prompt_repair_json(bad_text):
    return f"""
Conserte o conteúdo abaixo para virar SOMENTE um JSON válido, seguindo este esquema:
- Deve conter: posicionamento, bio, calendario, carrosseis (3), reels_ideias (5), stories_ideias (5).
- Não invente texto fora do JSON.
- Se faltar algo, complete.

CONTEÚDO PARA CONSERTAR:
{bad_text}
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
st.write("Pacote semanal: carrosséis prontos (texto por slide) + ideias de Reels/Stories.")

if "resultado" not in st.session_state:
    st.session_state.resultado = None
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
    with st.spinner("Gerando pacote semanal (JSON)..."):
        prompt = build_prompt_weekly_json(nicho, tipo, preco, objetivo, semana)
        resp = call_gemini_text(prompt, modelo, max_output_tokens=2300, timeout_segundos=120, max_tentativas=3)

    if not resp["ok"]:
        st.session_state.resultado = {"erro": resp["error"]}
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    raw = limpar_texto(resp["text"])
    st.session_state.raw = raw

    # tenta extrair/parsear JSON
    block = extract_json_block(raw)
    data = safe_json_loads(block) if block else None

    # se falhar, tenta "reparar" automaticamente
    if data is None:
        with st.spinner("Consertando formato (JSON inválido)..."):
            fix = call_gemini_text(build_prompt_repair_json(raw), modelo, max_output_tokens=2300, timeout_segundos=120, max_tentativas=3)
        if not fix["ok"]:
            st.session_state.resultado = {"erro": "JSON inválido e não foi possível corrigir. Veja Debug."}
            st.session_state.rodada = str(uuid.uuid4())
            st.rerun()
        fixed_raw = limpar_texto(fix["text"])
        st.session_state.raw = fixed_raw
        block2 = extract_json_block(fixed_raw)
        data = safe_json_loads(block2) if block2 else None

    if data is None:
        st.session_state.resultado = {"erro": "Ainda não consegui transformar em JSON válido. Ative Debug pra ver o bruto."}
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    st.session_state.resultado = data
    st.session_state.rodada = str(uuid.uuid4())
    st.rerun()

# ================= UI =================
with col2:
    rodada = st.session_state.rodada
    res = st.session_state.resultado

    tabs_names = ["🎯 Posicionamento", "🔗 Bio", "📅 Semana", "🖼️ Carrosséis", "🎬 Reels (ideias)", "📲 Stories (ideias)"]
    if debug_mode:
        tabs_names.append("🔎 Debug")

    abas = st.tabs(tabs_names)

    if res is None:
        with abas[0]:
            st.info("Preencha à esquerda e clique em **GERAR PACOTE SEMANAL**.")
    elif isinstance(res, dict) and "erro" in res:
        with abas[0]:
            st.error(res["erro"])
    else:
        # Posicionamento
        with abas[0]:
            st.text_area("Copiar e colar:", value=dict_to_text_posicionamento(res.get("posicionamento", {})), height=280, key=f"pos_{rodada}")

        # Bio
        with abas[1]:
            st.text_area("Copiar e colar:", value=dict_to_text_bio(res.get("bio", {})), height=430, key=f"bio_{rodada}")

        # Semana
        with abas[2]:
            st.text_area("Copiar e colar:", value=calendario_to_text(res.get("calendario", [])), height=430, key=f"cal_{rodada}")

        # Carrosséis
        with abas[3]:
            cars = res.get("carrosseis", []) or []
            if not cars:
                st.warning("Sem carrosséis retornados.")
            else:
                for idx, car in enumerate(cars, start=1):
                    st.subheader(f"Carrossel {idx}")
                    st.text_area("Copiar e colar:", value=format_carrossel_text(car), height=520, key=f"car_{idx}_{rodada}")
                    st.divider()

        # Reels (ideias)
        with abas[4]:
            st.text_area("Copiar e colar:", value=reels_to_text(res.get("reels_ideias", [])), height=650, key=f"reels_{rodada}")

        # Stories (ideias)
        with abas[5]:
            st.text_area("Copiar e colar:", value=stories_to_text(res.get("stories_ideias", [])), height=650, key=f"stories_{rodada}")

        if debug_mode:
            with abas[-1]:
                st.markdown("### Texto bruto retornado / JSON")
                st.text_area("RAW", value=st.session_state.raw, height=650, key=f"raw_{rodada}")
