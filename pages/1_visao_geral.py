import streamlit as st
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(
    page_title="1. Visão Geral do Tempo de Espera para FAV",
    page_icon="🩺",
    layout="wide"
)

st.sidebar.header("Filtros")

# Carregar dados e opções iniciais
df, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# Filtros na sidebar
filtro_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Mostrar somente pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

anos_selecionados = st.sidebar.multiselect(
    "Ano da criação da FAV",
    options=anos_disponiveis,
    default=anos_disponiveis
)

meses_selecionados = st.sidebar.multiselect(
    "Mês da criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# Aplicar filtro nos dados, agora passando filtro_cronico corretamente
df_filtrado, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtro_acesso,
    anos_selecionados=anos_selecionados,
    meses_selecionados=meses_selecionados
)

# Verificar se df_filtrado é vazio ou falta colunas esperadas para evitar erros
if df_filtrado.empty or 'TEMPO_ESPERA_DIAS' not in df_filtrado.columns:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
    st.stop()

# Estatísticas principais
n_pacientes = len(df_filtrado)
tempo_medio = df_filtrado['TEMPO_ESPERA_DIAS'].mean()
tempo_median = df_filtrado['TEMPO_ESPERA_DIAS'].median()
std_desvio = df_filtrado['TEMPO_ESPERA_DIAS'].std()
percentil_25 = df_filtrado['TEMPO_ESPERA_DIAS'].quantile(0.25)
percentil_75 = df_filtrado['TEMPO_ESPERA_DIAS'].quantile(0.75)
prop_acima_180 = (df_filtrado['TEMPO_ESPERA_DIAS'] > 180).mean() * 100

# Título e descrição
st.title("1. Visão Geral do Tempo de Espera para FAV")
st.markdown("Análise do tempo entre o início da diálise e confecção da fístula arteriovenosa em Porto Alegre (2015-2024).")

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("Tempo Médio de Espera", f"{tempo_medio:.0f} dias")
col2.metric("Número de Pacientes", f"{n_pacientes}")
col3.metric("Unidades Hospitalares", f"{df_filtrado['COD_UNIDADE_HOSPITALAR'].nunique()}")

st.markdown("---")

# Estatísticas adicionais
st.markdown(f"""
**Desvio padrão:** {std_desvio:.1f} dias  
**Mediana:** {tempo_median:.0f} dias  
**Percentil 25:** {percentil_25:.0f} dias | **Percentil 75:** {percentil_75:.0f} dias  

**Proporção com espera > 6 meses:** {prop_acima_180:.1f}%  

---
*Nota: o histograma abaixo considera tempos entre 0 e 730 dias para melhor visualização.*
""")

# Histograma do tempo de espera
fig = px.histogram(
    df_filtrado,
    x='TEMPO_ESPERA_DIAS',
    nbins=50,
    marginal="box",
    title="Distribuição do Tempo de Espera para Confecção da FAV (dias)",
    labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'}
)
fig.update_layout(
    xaxis_title="Tempo de Espera (dias)",
    yaxis_title="Número de Pacientes",
    bargap=0.1
)
st.plotly_chart(fig, use_container_width=True)

# Boxplot comparativo por sexo
with st.expander("⏳ Comparação do Tempo de Espera por Sexo"):
    fig_sexo = px.box(
        df_filtrado,
        x='SEXO',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)', 'SEXO': 'Sexo'},
        title="Tempo de Espera para Confecção da FAV por Sexo"
    )
    st.plotly_chart(fig_sexo, use_container_width=True)

# Boxplot comparativo por raça/cor
with st.expander("⏳ Comparação do Tempo de Espera por Raça/Cor"):
    fig_raca = px.box(
        df_filtrado,
        x='RACA_COR',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)', 'RACA_COR': 'Raça/Cor'},
        title="Tempo de Espera para Confecção da FAV por Raça/Cor"
    )
    st.plotly_chart(fig_raca, use_container_width=True)

# Insights automáticos
st.markdown("---")
st.subheader("💡 Insights automáticos")

if tempo_medio > 300:
    st.warning("⚠️ O tempo médio de espera está acima de 300 dias, indicando possível atraso no acesso vascular.")
else:
    st.success("✅ O tempo médio de espera está dentro do esperado para este período.")

if prop_acima_180 > 30:
    st.warning(f"⚠️ Alta proporção ({prop_acima_180:.1f}%) de pacientes com espera superior a 6 meses.")
else:
    st.info(f"ℹ️ Proporção de pacientes com espera superior a 6 meses está em {prop_acima_180:.1f}%.")

if tempo_median > 300:
    st.info("ℹ️ A mediana do tempo de espera sugere que metade dos pacientes esperam mais de 300 dias.")

# Exportação de dados filtrados
st.markdown("---")
with st.expander("📥 Exportar dados filtrados"):
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Baixar CSV",
        data=csv,
        file_name='dados_filtrados_fav.csv',
        mime='text/csv'
    )

# Explicação final
st.markdown("---")
st.markdown("""
**Sobre esta análise:**  
Este dashboard apresenta uma análise temporal e demográfica do tempo de espera para a confecção da Fístula Arteriovenosa (FAV) em pacientes em diálise crônica em Porto Alegre entre 2015 e 2024.  
A fístula arteriovenosa é o acesso vascular recomendado para diálise, pois apresenta menor risco de infecções e complicações. O tempo de espera adequado para sua confecção impacta diretamente na qualidade do tratamento e nos resultados clínicos.  
Os filtros permitem segmentar a análise por tipo de acesso vascular, período, sexo, raça/cor e condição crônica.  
Use os gráficos para visualizar a distribuição e diferenças populacionais no tempo de espera.
""")
