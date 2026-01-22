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

# ================= HELPERS (robustos) =================
def ensure_dict(x):
    return x if isinstance(x, dict) else {}

def ensure_list(x):
    return x if isinstance(x, list) else []

def as_text(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x.strip()
    try:
        return str(x).strip()
    except:
        return ""

def limpar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.replace("\x00", "").replace("$", " reais ")

def extract_json_block(s: str):
    if not s:
        return None
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
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

# ================= GEMINI =================
def call_gemini_text(prompt, modelo_escolhido, max_output_tokens=2200, timeout_segundos=120, max_tentativas=3):
    if "GOOGLE_API_KEY" not in st.secrets:
        return {"ok": False, "error": "GOOGLE_API_KEY não configurada no st.secrets."}

    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_escolhido}:generateContent?key={api_key}"

    # responseMimeType ajuda MUITO quando aceito pela API
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": int(max_output_tokens),
            "responseMimeType": "application/json"
        }
    }

    last_err = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            r = requests.post(url, json=payload, timeout=timeout_segundos)

            if r.status_code != 200:
                # erros temporários -> retry
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

REGRAS OBRIGATÓRIAS:
- Responda SOMENTE com JSON válido (sem texto fora).
- Carrosséis: 3 carrosséis.
- Cada carrossel: 7 slides com texto FINAL (curto e postável).
- Cada slide: até ~120 caracteres (para caber na arte).
- "imagens": descreva o que colocar no slide (foto/ícone/ilustração).
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

def build_prompt_repair_json(bad_text, reason):
    # reason ajuda o modelo a corrigir especificamente o que faltou
    return f"""
Transforme o conteúdo abaixo em SOMENTE um JSON válido no esquema do NutriVendas.

REGRAS:
- Responder SOMENTE com JSON válido.
- Preencher tudo que faltar.
- Carrosséis: 3 carrosséis.
- Cada carrossel: 7 slides obrigatórios (texto curto e postável).
- Hashtags: 10 por carrossel.
- Reels e Stories: apenas IDEIAS.

MOTIVO DO REPARO:
{reason}

CONTEÚDO PARA CONSERTAR:
{bad_text}
"""

# ================= VALIDATOR =================
def validar_estrutura(data):
    if not isinstance(data, dict):
        return False, "JSON não é um objeto."

    pos = data.get("posicionamento")
    bio = data.get("bio")
    cal = data.get("calendario")
    cars = data.get("carrosseis")
    reels = data.get("reels_ideias")
    stories = data.get("stories_ideias")

    if not isinstance(pos, dict):
        return False, "posicionamento ausente/errado."
    if not isinstance(bio, dict):
        return False, "bio ausente/errado."
    if not isinstance(cal, list) or len(cal) < 7:
        return False, "calendario ausente/curto."
    if not isinstance(reels, list) or len(reels) < 5:
        return False, "reels_ideias ausente/curto."
    if not isinstance(stories, list) or len(stories) < 5:
        return False, "stories_ideias ausente/curto."

    if not isinstance(cars, list) or len(cars) < 3:
        return False, "carrosseis ausente/curto (precisa 3)."

    for idx, c in enumerate(cars, start=1):
        if not isinstance(c, dict):
            return False, f"Carrossel {idx} inválido."
        slides = c.get("slides")
        imgs = c.get("imagens")
        htags = c.get("hashtags")
        if not isinstance(slides, list) or len(slides) != 7:
            return False, f"Carrossel {idx} precisa ter 7 slides."
        if any((not isinstance(s, str) or not s.strip()) for s in slides):
            return False, f"Carrossel {idx} tem slide vazio."
        if not isinstance(imgs, list) or len(imgs) != 7:
            return False, f"Carrossel {idx} precisa ter 7 imagens sugeridas."
        if not isinstance(htags, list) or len(htags) != 10:
            return False, f"Carrossel {idx} precisa ter 10 hashtags."
        if not isinstance(c.get("legenda", ""), str) or not c.get("legenda", "").strip():
            return False, f"Carrossel {idx} sem legenda pronta."
        if not isinstance(c.get("capa", ""), str) or not c.get("capa", "").strip():
            return False, f"Carrossel {idx} sem capa."

    return True, "OK"

# ================= FORMATTERS (sem crash) =================
def dict_to_text_posicionamento(d):
    if isinstance(d, str):
        return d.strip()
    d = ensure_dict(d)
    return "\n".join([
        f"Promessa: {as_text(d.get('promessa',''))}",
        f"Público ideal: {as_text(d.get('publico',''))}",
        f"CTA padrão: {as_text(d.get('cta',''))}"
    ]).strip()

def dict_to_text_bio(d):
    if isinstance(d, str):
        return d.strip()
    d = ensure_dict(d)

    bios = d.get("bios", [])
    if isinstance(bios, str):
        bios = [bios]
    bios = ensure_list(bios)

    destaques = d.get("destaques", [])
    if isinstance(destaques, str):
        destaques = [destaques]
    destaques = ensure_list(destaques)

    link = as_text(d.get("link_bio", ""))

    out = []
    out.append("BIOS:")
    if bios:
        for i, b in enumerate(bios, start=1):
            out.append(f"{i}) {as_text(b)}")
    else:
        out.append("- (não retornado)")

    out.append("")
    out.append(f"Link na bio: {link if link else '(não retornado)'}")
    out.append("")
    out.append("Destaques (nome → conteúdo):")

    if not destaques:
        out.append("- (não retornado)")
    else:
        for item in destaques:
            if isinstance(item, dict):
                nome = as_text(item.get("nome", ""))
                conteudo = item.get("conteudo", [])
                if isinstance(conteudo, str):
                    conteudo = [conteudo]
                conteudo = ensure_list(conteudo)
                conteudo_txt = ", ".join([as_text(c) for c in conteudo if as_text(c)])
                out.append(f"- {nome}: {conteudo_txt}".strip())
            else:
                out.append(f"- {as_text(item)}")

    return "\n".join(out).strip()

def calendario_to_text(lst):
    if isinstance(lst, str):
        return lst.strip()
    lst = ensure_list(lst)
    if not lst:
        return "⚠️ (calendário não retornado)"
    out = []
    for it in lst:
        if isinstance(it, dict):
            out.append(
                f"{as_text(it.get('dia','Dia'))}: "
                f"{as_text(it.get('formato',''))} | "
                f"{as_text(it.get('objetivo',''))} | "
                f"CTA: {as_text(it.get('cta',''))}"
            )
        else:
            out.append(as_text(it))
    return "\n".join(out).strip()

def format_carrossel_text(car):
    car = ensure_dict(car)
    tema = as_text(car.get("tema",""))
    capa = as_text(car.get("capa",""))
    slides = ensure_list(car.get("slides", []))
    imagens = ensure_list(car.get("imagens", []))
    legenda = as_text(car.get("legenda",""))
    cta = as_text(car.get("cta",""))
    hashtags = ensure_list(car.get("hashtags", []))

    out = []
    out.append(f"TEMA: {tema}")
    out.append(f"CAPA: {capa}")
    out.append("")
    for i, txt in enumerate(slides, start=1):
        out.append(f"SLIDE {i}: {as_text(txt)}")
        if i-1 < len(imagens):
            out.append(f"  (Imagem sugerida: {as_text(imagens[i-1])})")
    out.append("")
    out.append("LEGENDA (copiar e colar):")
    out.append(legenda)
    out.append("")
    out.append(f"CTA: {cta}")
    out.append("")
    out.append("HASHTAGS:")
    out.append(" ".join([as_text(h) for h in hashtags if as_text(h)]))
    return "\n".join(out).strip()

def reels_to_text(lst):
    if isinstance(lst, str):
        return lst.strip()
    lst = ensure_list(lst)
    if not lst:
        return "⚠️ (reels_ideias não retornado)"
    out = []
    for i, it in enumerate(lst, start=1):
        if not isinstance(it, dict):
            out.append(f"REELS {i}: {as_text(it)}\n")
            continue
        out.append(f"REELS {i} — Tema: {as_text(it.get('tema',''))}")
        out.append(f"Hook: {as_text(it.get('hook',''))}")

        falar = it.get("falar", [])
        if isinstance(falar, str):
            falar = [falar]
        falar = ensure_list(falar)

        mostrar = it.get("mostrar", [])
        if isinstance(mostrar, str):
            mostrar = [mostrar]
        mostrar = ensure_list(mostrar)

        out.append("O que falar:")
        for b in falar[:6]:
            out.append(f"- {as_text(b)}")
        out.append("O que mostrar:")
        for b in mostrar[:6]:
            out.append(f"- {as_text(b)}")

        out.append(f"Duração: {as_text(it.get('duracao','15-25s'))}")
        out.append("")
    return "\n".join(out).strip()

def stories_to_text(lst):
    if isinstance(lst, str):
        return lst.strip()
    lst = ensure_list(lst)
    if not lst:
        return "⚠️ (stories_ideias não retornado)"
    out = []
    for i, it in enumerate(lst, start=1):
        if not isinstance(it, dict):
            out.append(f"SEQUÊNCIA {i}: {as_text(it)}\n")
            continue
        out.append(f"SEQUÊNCIA {i}: {as_text(it.get('tema',''))}")
        seq = it.get("sequencia", [])
        if isinstance(seq, str):
            seq = [{"texto": seq, "sticker": ""}]
        seq = ensure_list(seq)

        for j, s in enumerate(seq, start=1):
            if isinstance(s, dict):
                out.append(f"Story {j}: {as_text(s.get('texto',''))}")
                out.append(f"  Sticker: {as_text(s.get('sticker',''))}")
            else:
                out.append(f"Story {j}: {as_text(s)}")
        out.append(f"CTA: {as_text(it.get('cta',''))}")
        out.append("")
    return "\n".join(out).strip()

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
st.write("Carrosséis PRONTOS (texto por slide) + ideias de Reels/Stories. Feito pra vender.")

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

def gerar_e_parsear(prompt):
    resp = call_gemini_text(prompt, modelo, max_output_tokens=2400, timeout_segundos=120, max_tentativas=3)
    if not resp["ok"]:
        return None, resp["error"], ""

    raw = limpar_texto(resp["text"])
    block = extract_json_block(raw)
    data = safe_json_loads(block) if block else None
    return data, None, raw

if gerar:
    with st.spinner("Gerando pacote (JSON) ..."):
        data, err, raw = gerar_e_parsear(build_prompt_weekly_json(nicho, tipo, preco, objetivo, semana))

    if err:
        st.session_state.resultado = {"erro": err}
        st.session_state.raw = raw
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    st.session_state.raw = raw

    # Se não virou dict, tenta reparar
    if data is None:
        with st.spinner("Saída veio fora do formato. Reparando automaticamente..."):
            fix = call_gemini_text(
                build_prompt_repair_json(raw, "JSON inválido/ausente"),
                modelo,
                max_output_tokens=2400,
                timeout_segundos=120,
                max_tentativas=3
            )
        if not fix["ok"]:
            st.session_state.resultado = {"erro": "Não consegui reparar o JSON. Ative Debug e tente novamente."}
            st.session_state.rodada = str(uuid.uuid4())
            st.rerun()

        fixed_raw = limpar_texto(fix["text"])
        st.session_state.raw = fixed_raw
        block2 = extract_json_block(fixed_raw)
        data = safe_json_loads(block2) if block2 else None

    if data is None:
        st.session_state.resultado = {"erro": "Ainda não consegui transformar em JSON válido. Ative Debug e tente novamente."}
        st.session_state.rodada = str(uuid.uuid4())
        st.rerun()

    # Validar estrutura (garantir "pronto")
    ok, msg = validar_estrutura(data)
    if not ok:
        # tenta reparar baseado no motivo
        with st.spinner(f"Modelo devolveu incompleto ({msg}). Reparando para ficar PRONTO..."):
            fix = call_gemini_text(
                build_prompt_repair_json(json.dumps(data, ensure_ascii=False), msg),
                modelo,
                max_output_tokens=2600,
                timeout_segundos=120,
                max_tentativas=3
            )
        if fix["ok"]:
            fixed_raw = limpar_texto(fix["text"])
            st.session_state.raw = fixed_raw
            block3 = extract_json_block(fixed_raw)
            data2 = safe_json_loads(block3) if block3 else None
            if data2 is not None:
                data = data2

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
            st.text_area("Copiar e colar:", value=dict_to_text_posicionamento(res.get("posicionamento", {})), height=250, key=f"pos_{rodada}")

        # Bio
        with abas[1]:
            st.text_area("Copiar e colar:", value=dict_to_text_bio(res.get("bio", {})), height=430, key=f"bio_{rodada}")

        # Semana
        with abas[2]:
            st.text_area("Copiar e colar:", value=calendario_to_text(res.get("calendario", [])), height=430, key=f"cal_{rodada}")

        # Carrosséis
        with abas[3]:
            cars = res.get("carrosseis", [])
            cars = ensure_list(cars)
            if not cars:
                st.warning("Sem carrosséis retornados. Gere novamente.")
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
                st.markdown("### Resposta bruta / JSON (pra diagnosticar)")
                st.text_area("RAW", value=st.session_state.raw, height=650, key=f"raw_{rodada}")
