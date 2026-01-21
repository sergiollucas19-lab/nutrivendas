import streamlit as st
import requests
import json

# 1. Configuração Básica
st.set_page_config(page_title="NutriVendas Debug", page_icon="🔧", layout="wide")

st.title("🔧 NutriVendas: Modo Diagnóstico")
st.info("Sistema carregado. Pronto para teste.")

# 2. Verifica Chaves
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Falta GOOGLE_API_KEY")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("Falta ACCESS_PASSWORD")
    st.stop()

# 3. Função de IA (Nome correto: consultar_ia)
def consultar_ia(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # Usando modelo 1.5 Flash para garantir estabilidade no teste
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Crie uma estratégia de marketing para Nutricionista.
    Nicho: {nicho}. Atendimento: {tipo}. Preço: {preco}. Meta: {objetivo}.
    
    IMPORTANTE: Retorne APENAS texto simples, sem formatação complexa.
    
    SEÇÃO 1: 3 Ideias de Posts.
    SEÇÃO 2: Script de Vendas.
    SEÇÃO 3: Bio do Instagram.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        st.write(f"📡 Status da Conexão: {response.status_code}") # Debug visual
        
        if response.status_code == 200:
            dados = response.json()
            if "candidates" in dados and len(dados["candidates"]) > 0:
                return dados["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"⚠️ Resposta vazia do Google: {dados}"
        else:
            return f"❌ Erro HTTP: {response.text}"
            
    except Exception as e:
        return f"❌ Erro Crítico Python: {str(e)}"

# 4. Login
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha == st.secrets["ACCESS_PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Senha errada")
    st.stop()

# 5. O Formulário
with st.form("debug_form"):
    st.write("### Teste de Geração")
    nicho = st.text_input("Nicho", "Emagrecimento")
    tipo = st.selectbox("Tipo", ["Online", "Presencial"])
    preco = st.text_input("Preço", "R$ 200")
    obj = st.selectbox("Objetivo", ["Agenda", "Vendas"])
    
    btn = st.form_submit_button("RODAR TESTE")

if btn:
    st.warning("🔄 Enviando...")
    # AQUI ESTAVA O ERRO: Agora o nome está completo
    resultado = consultar_ia(nicho, tipo, preco, obj)
    
    st.success("✅ Concluído!")
    st.text_area("Resultado Bruto:", value=resultado, height=500)