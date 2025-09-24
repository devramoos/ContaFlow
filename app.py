import streamlit as st
import pandas as pd
import os
import sys

# Adiciona a pasta do projeto ao path para que possamos importar o classificador
PASTA_APP = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PASTA_APP)

# Importa a função diretamente do script de backend
from modelo_ia.classificador_sqlite import classificar_com_db

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="MayperFlow",
    page_icon="favicon-32x32.png",
    layout="wide"
)

# --- Título e Descrição ---
st.title("Bem-vindo ao MayperFlow! 📊")
st.write(
    "Faça o upload do seu fluxo de caixa em formato CSV para que a nossa "
    "Inteligência Artificial possa classificá-lo automaticamente."
)

# --- Upload do Ficheiro ---
uploaded_file = st.file_uploader(
    "Selecione o ficheiro CSV",
    type=['csv']
)

if uploaded_file is not None:
    PASTA_ENTRADA = os.path.join(PASTA_APP, "arquivos_para_classificar")
    os.makedirs(PASTA_ENTRADA, exist_ok=True)

    input_path = os.path.join(PASTA_ENTRADA, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Ficheiro '{uploaded_file.name}' carregado com sucesso!")

    # --- Botão para Iniciar a Classificação ---
    if st.button("CLASSIFICAR FICHEIRO"):
        with st.spinner("Aguarde, a IA está a trabalhar... 🤖"):
            try:
                # --- CHAMADA DIRETA DA FUNÇÃO ---
                # Removemos o subprocess e chamamos a função importada
                output_path = classificar_com_db(uploaded_file.name)

                if output_path and os.path.exists(output_path):
                    st.success("Ficheiro classificado com sucesso!")

                    df_resultado = pd.read_csv(output_path, sep=';', decimal=',')
                    st.dataframe(df_resultado)

                    st.download_button(
                        label="Baixar CSV Classificado",
                        data=df_resultado.to_csv(sep=';', decimal=',', index=False).encode('utf-8-sig'),
                        file_name=os.path.basename(output_path),
                        mime='text/csv',
                    )
                else:
                    st.error("Ocorreu um erro durante a classificação. O ficheiro de resultado não foi gerado.")

            except Exception as e:
                st.error(f"Ocorreu um erro inesperado durante a integração: {e}")
                st.exception(e)  # Mostra o traceback completo do erro para depuração

# --- Rodapé (Opcional) ---
st.markdown("---")
st.write("Desenvolvido para o projeto MayperFlow.")