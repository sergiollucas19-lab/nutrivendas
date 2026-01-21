import streamlit as st
import requests

st.set_page_config(page_title="Raio-X Google", layout="wide")

st.title("🕵️ Diagnóstico de Modelos do Google")
st.write("Vamos ver quais modelos estão disponíveis para a sua chave.")

# 1. Verifica se a chave existe
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("❌ Chave não encontrada nos Secrets!")
    st.stop()

api_key = st.secrets["GOOGLE_API_KEY"]
# Mostra só o começo e o fim da chave para confirmar que leu certo
st.info(f"🔑 Lendo chave: {api_key[:5]}...{api_key[-5:]}")

# 2. Pergunta pro Google: "O que você tem aí?"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    
    if response.status_code == 200:
        dados = response.json()
        modelos = dados.get('models', [])
        
        if modelos:
            st.success(f"✅ Sucesso! Encontrei {len(modelos)} modelos disponíveis.")
            st.write("Aqui estão os nomes exatos que devemos usar:")
            
            # Lista bonitinha na tela
            for m in modelos:
                nome = m['name'].replace('models/', '')
                st.code(nome, language="text")
        else:
            st.warning("⚠️ A conexão funcionou, mas a lista de modelos veio vazia!")
            st.write("Isso significa que a API Generative Language não está ativada nessa chave.")
            
    else:
        st.error(f"❌ Erro de Conexão: {response.status_code}")
        st.json(response.json())

except Exception as e:
    st.error(f"Erro grave: {e}")