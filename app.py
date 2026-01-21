import streamlit as st
import requests
import json

# 1. Configuração Básica (Sem CSS pesado para não esconder erros)
st.set_page_config(page_title="NutriVendas Debug", page_icon="🔧", layout="wide")

st.title("🔧 NutriVendas: Modo Diagnóstico")
st.info("Se você está lendo isso, o site carregou.")

# 2. Verifica Chaves
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Falta GOOGLE_API_KEY")
    st.stop()
if "ACCESS_PASSWORD" not in st.secrets:
    st.error("Falta ACCESS_PASSWORD")
    st.stop()

# 3. Função de IA (Com tratamento de Segurança do Google)
def consultar_ia(nicho, tipo, preco, objetivo):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # Vamos usar o modelo padrão 1.5 Flash que é mais estável para testes
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Crie uma estratégia de marketing para Nutricionista.
    Nicho: {nicho}. Atendimento: {tipo}. Preço: {preco}. Meta: {objetivo}.
    
    IMPORTANTE: Retorne APENAS texto simples.
    
    SEÇÃO 1: 3 Ideias de Posts (Título e Legenda).
    SEÇÃO 2: Script de Vendas para Direct.
    SEÇÃO 3: Bio do Instagram.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        
        # DEBUG: Mostra o status da conexão na tela
        st.write(f"📡 Status da Conexão: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verifica se o Google bloqueou por segurança
            if "promptFeedback" in dados and "blockReason" in dados["promptFeedback"]:
                return "⚠️ ERRO: O Google bloqueou este pedido (Safety Filter)."
                
            if "candidates" in dados and len(dados["candidates"]) > 0:
                candidato = dados["candidates"][0]
                if "content" in candidato:
                    return candidato["content"]["parts"][0]["text"]
                elif "finishReason" in candidato:
                    return f"⚠️ A IA parou de gerar. Motivo: {candidato['finishReason']}"
            
            return f"⚠️ Resposta vazia ou estranha: {json.dumps(dados)}"
        else:
            return f"❌ Erro HTTP: {response.text}"
            
    except Exception as e:
        return f"❌ Erro Crítico no Python: {str(e)}"

# 4. Login Simples
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
    st.write("### Preencha para Testar")
    nicho = st.text_input("Nicho", "Emagrecimento")
    tipo = st.selectbox("Tipo", ["Online", "Presencial"])
    preco = st.text_input("Preço", "R$ 200")
    obj = st.selectbox("Objetivo", ["Agenda", "Vendas"])
    
    btn = st.form_submit_button("RODAR TESTE")

if btn:
    st.write("---")
    st.warning("🔄 Enviando para o Google... aguarde.")
    
    resultado = consultar_