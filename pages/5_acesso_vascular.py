# pages/5_acesso_vascular.py
import streamlit as st
import pandas as pd
import plotly.express as px

st.markdown("# 5. O Acesso Vascular Inicial Influencia na Espera?")
st.sidebar.header("Acesso Vascular")
@st.cache_data
def load_data():
    return pd.read_csv("dados_finais_para_dashboard.csv")

df = load_data()

st.write("Uma hipótese clínica importante é que pacientes que iniciam diálise de forma não planejada com cateteres temporários podem ter um tempo de espera diferente para a confecção da fístula definitiva. Vamos analisar.")

# Contagem de pacientes por tipo de acesso inicial
contagem_acesso = df['ACESSO_VASCULAR_INICIAL'].value_counts().reset_index()
contagem_acesso.columns = ['ACESSO_VASCULAR_INICIAL', 'N_PACIENTES']

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Nº de Pacientes por Acesso Inicial")
    fig_pie = px.pie(contagem_acesso, names='ACESSO_VASCULAR_INICIAL', values='N_PACIENTES', title="Distribuição do Tipo de Acesso Vascular Inicial", hole=0.3)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.markdown("### Tempo de Espera por Acesso Inicial")
    fig_box = px.box(df, x='ACESSO_VASCULAR_INICIAL', y='TEMPO_ESPERA_DIAS', color="ACESSO_VASCULAR_INICIAL", title="Comparativo do Tempo de Espera por Acesso Inicial")
    st.plotly_chart(fig_box, use_container_width=True)

st.markdown("#### Análise:")
st.write("O gráfico de caixa à direita nos permite comparar não apenas a mediana (a linha no meio da caixa), mas toda a distribuição do tempo de espera para cada tipo de acesso. Podemos observar se um grupo específico (como 'Cateter Duplo Lúmen') apresenta uma espera maior ou mais variável em comparação com pacientes que já iniciam com uma Fístula Arteriovenosa (FAV).")