import streamlit as st
import pandas as pd
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(
    page_title="3. Análise Temporal e Perfis Clínicos do Tempo de Espera para FAV",
    page_icon="📈",
    layout="wide"
)

st.title("3. Análise Temporal e Perfis Clínicos do Tempo de Espera para FAV")

# --- Filtros Globais na Sidebar ---
st.sidebar.header("Filtros Globais")

# Carregar opções para os filtros
df_base, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Mostrar somente pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
ano_inicial, ano_final = st.sidebar.slider(
    "Intervalo de anos da criação da FAV",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1
)

meses_selecionados = st.sidebar.multiselect(
    "Meses da criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# Aplicar filtros globais
df, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtros_acesso,
    anos_selecionados=list(range(ano_inicial, ano_final + 1)),
    meses_selecionados=meses_selecionados
)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# --- Resumo Filtros Globais (coluna à direita) ---
with st.sidebar.expander("📌 Resumo dos Filtros Aplicados"):
    st.markdown(f"**Acesso Vascular:** {', '.join(filtros_acesso) if filtros_acesso else 'Nenhum'}")
    st.markdown(f"**Crônicos:** {'Sim' if filtro_cronico else 'Não'}")
    st.markdown(f"**Anos:** {ano_inicial}–{ano_final}")
    st.markdown(f"**Meses:** {', '.join([f'{m:02d}' for m in meses_selecionados])}")

# Mostrar número pacientes após filtro global
st.markdown(f"**Pacientes após filtros globais:** {len(df)}")

# --- Filtros adicionais da página ---
hospital_options = sorted(df['COD_UNIDADE_HOSPITALAR'].astype(str).unique())
faixa_etaria_options = sorted(df['FAIXA_ETARIA'].astype(str).unique())
sexo_options = sorted(df['SEXO'].astype(str).unique())
raca_options = sorted(df['RACA_COR'].astype(str).unique())

st.sidebar.header("Filtros adicionais")

hospital_selec = st.sidebar.multiselect("Hospital", options=hospital_options, default=hospital_options)
faixa_etaria_selec = st.sidebar.multiselect("Faixa Etária", options=faixa_etaria_options, default=faixa_etaria_options)
sexo_selec = st.sidebar.multiselect("Sexo", options=sexo_options, default=sexo_options)
raca_selec = st.sidebar.multiselect("Raça/Cor", options=raca_options, default=raca_options)

# Aplicar filtros adicionais
df_filt = df[
    (df['COD_UNIDADE_HOSPITALAR'].astype(str).isin(hospital_selec)) &
    (df['FAIXA_ETARIA'].astype(str).isin(faixa_etaria_selec)) &
    (df['SEXO'].astype(str).isin(sexo_selec)) &
    (df['RACA_COR'].astype(str).isin(raca_selec))
].copy()

if df_filt.empty:
    st.warning("⚠️ Nenhum dado após os filtros adicionais.")
    st.stop()

# Ajustes para Plotly
df_filt['DATA_CRIACAO_FAV'] = pd.to_datetime(df_filt['DATA_CRIACAO_FAV'], errors='coerce')
df_filt = df_filt.dropna(subset=['DATA_CRIACAO_FAV'])

df_filt['MES_ANO'] = df_filt['DATA_CRIACAO_FAV'].dt.to_period('M').dt.to_timestamp()

# Mostrar quantidade final
st.markdown(f"**Pacientes após filtros da página:** {len(df_filt)}")

# --- Parâmetros para destacar pandemia ---
inicio_pandemia = pd.to_datetime("2020-03-01")
fim_pandemia = pd.to_datetime("2022-03-31")

# --- Gráfico 1: Tempo médio mensal geral ---
st.markdown("---")
st.subheader("📅 Tempo Médio Geral (Mensal)")

df_tempo_mes = df_filt.groupby('MES_ANO')['TEMPO_ESPERA_DIAS'].mean().reset_index()

fig_tempo = px.line(
    df_tempo_mes,
    x='MES_ANO',
    y='TEMPO_ESPERA_DIAS',
    title="Tempo Médio Mensal para Confecção da FAV",
    labels={'MES_ANO': 'Mês/Ano', 'TEMPO_ESPERA_DIAS': 'Tempo Médio (dias)'},
    markers=True
)

# Anotar pico
pico_idx = df_tempo_mes['TEMPO_ESPERA_DIAS'].idxmax()
pico = df_tempo_mes.loc[pico_idx]
fig_tempo.add_scatter(
    x=[pico['MES_ANO']], y=[pico['TEMPO_ESPERA_DIAS']],
    mode='markers+text',
    marker=dict(size=12, color='green'),
    text=[f"Pico: {pico['TEMPO_ESPERA_DIAS']:.0f}d"],
    textposition="top center",
    name="Pico"
)

# Pandemia
fig_tempo.add_vrect(
    x0=inicio_pandemia, x1=fim_pandemia,
    fillcolor="red", opacity=0.2,
    layer="below", line_width=0,
    annotation_text="Pandemia COVID-19", annotation_position="top left"
)

fig_tempo.update_layout(showlegend=False)
st.plotly_chart(fig_tempo, use_container_width=True)

# --- Gráficos por grupos demográficos ---
def grafico_temporal(df_grupo, grupo, titulo, cor_map=None):
    fig = px.line(
        df_grupo,
        x='MES_ANO',
        y='TEMPO_ESPERA_DIAS',
        color=grupo,
        markers=True,
        title=titulo,
        labels={'MES_ANO': 'Mês/Ano', 'TEMPO_ESPERA_DIAS': 'Tempo Médio (dias)', grupo: grupo}
    )

    for categoria in df_grupo[grupo].unique():
        df_c = df_grupo[df_grupo[grupo] == categoria]
        if not df_c.empty:
            idx = df_c['TEMPO_ESPERA_DIAS'].idxmax()
            ponto = df_c.loc[idx]
            fig.add_scatter(
                x=[ponto['MES_ANO']],
                y=[ponto['TEMPO_ESPERA_DIAS']],
                mode='markers+text',
                marker=dict(size=10),
                text=[f"{categoria} Pico: {ponto['TEMPO_ESPERA_DIAS']:.0f}d"],
                textposition="top center",
                name=f"Pico {categoria}"
            )

    fig.add_vrect(
        x0=inicio_pandemia, x1=fim_pandemia,
        fillcolor="red", opacity=0.2,
        layer="below", line_width=0,
        annotation_text="Pandemia COVID-19", annotation_position="top left"
    )

    return fig

# Sexo
st.markdown("---")
st.subheader("👥 Tempo Médio por Sexo")
df_sexo = df_filt.groupby(['MES_ANO', 'SEXO'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_sexo, 'SEXO', "Tempo Médio por Sexo"), use_container_width=True)

# Raça
st.subheader("🌎 Tempo Médio por Raça/Cor")
df_raca = df_filt.groupby(['MES_ANO', 'RACA_COR'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_raca, 'RACA_COR', "Tempo Médio por Raça/Cor"), use_container_width=True)

# Faixa etária
st.subheader("📊 Tempo Médio por Faixa Etária")
df_faixa = df_filt.groupby(['MES_ANO', 'FAIXA_ETARIA'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_faixa, 'FAIXA_ETARIA', "Tempo Médio por Faixa Etária"), use_container_width=True)
