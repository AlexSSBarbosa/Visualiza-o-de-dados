import streamlit as st
import pandas as pd
import plotly.express as px

@st.cache_data
def load_data():
    return pd.read_csv("dados_finais_para_dashboard.csv")

df = load_data()

st.title("4. Origem dos Pacientes")

contagem = df['MUN_RESIDENCIA_COD'].value_counts().reset_index()
contagem.columns = ['MUN_COD', 'Qtde']

fig_tree = px.treemap(
    contagem, path=['MUN_COD'], values='Qtde',
    title="Distribuição de Pacientes por Município de Residência",
    color='Qtde', color_continuous_scale='Blues'
)
st.plotly_chart(fig_tree, use_container_width=True)
