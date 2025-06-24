import streamlit as st
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(
    page_title="1. Visão Geral do Tempo de Espera para FAV",
    page_icon="🩺",
    layout="wide"
)

st.sidebar.header("🎛️ Filtros")

# Carregar dados e opções iniciais
df, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# Filtros interativos
filtro_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Mostrar apenas pacientes crônicos (≥ 3 meses em diálise)",
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

# Aplicar filtros nos dados
df_filtrado, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtro_acesso,
    anos_selecionados=anos_selecionados,
    meses_selecionados=meses_selecionados
)

# Segurança: evitar erros com dataframe vazio
if df_filtrado.empty or 'TEMPO_ESPERA_DIAS' not in df_filtrado.columns:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# Estatísticas principais
n_pacientes = len(df_filtrado)
tempo_medio = df_filtrado['TEMPO_ESPERA_DIAS'].mean()
tempo_median = df_filtrado['TEMPO_ESPERA_DIAS'].median()
std_desvio = df_filtrado['TEMPO_ESPERA_DIAS'].std()
percentil_25 = df_filtrado['TEMPO_ESPERA_DIAS'].quantile(0.25)
percentil_75 = df_filtrado['TEMPO_ESPERA_DIAS'].quantile(0.75)
prop_acima_180 = (df_filtrado['TEMPO_ESPERA_DIAS'] > 180).mean() * 100

# Título e introdução
st.title("1. Visão Geral do Tempo de Espera para Fístula Arteriovenosa (FAV)")
st.markdown(
    """
    Esta seção apresenta uma visão geral do **tempo entre o início da diálise e a confecção da fístula arteriovenosa (FAV)**, 
    principal acesso vascular para tratamento dialítico crônico, em pacientes atendidos em Porto Alegre entre 2015 e 2024.
    """
)

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("⏱️ Tempo Médio de Espera", f"{tempo_medio:.0f} dias")
col2.metric("👥 Pacientes Incluídos", f"{n_pacientes}")
col3.metric("🏥 Unidades Hospitalares", f"{df_filtrado['COD_UNIDADE_HOSPITALAR'].nunique()}")

st.markdown("----")

# Estatísticas complementares
st.markdown(
    f"""
    **Medidas de dispersão e distribuição:**

    - **Desvio padrão:** {std_desvio:.1f} dias  
    - **Mediana:** {tempo_median:.0f} dias  
    - **Percentil 25:** {percentil_25:.0f} dias  
    - **Percentil 75:** {percentil_75:.0f} dias  
    - **Proporção com espera > 6 meses (180 dias):** {prop_acima_180:.1f}%

    ---
    *Observação: os gráficos consideram apenas valores entre 0 e 730 dias para melhor visualização.*
    """
)

# Histograma com boxplot
fig = px.histogram(
    df_filtrado,
    x='TEMPO_ESPERA_DIAS',
    nbins=50,
    marginal="box",
    title="Distribuição do Tempo de Espera para Confecção da FAV",
    labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'}
)
fig.update_layout(
    xaxis_title="Tempo de Espera (dias)",
    yaxis_title="Número de Pacientes",
    bargap=0.1
)
st.plotly_chart(fig, use_container_width=True)

# Boxplot por Sexo
with st.expander("📊 Tempo de Espera por Sexo"):
    st.markdown(
        """
        O boxplot abaixo mostra a distribuição do tempo de espera entre os sexos.  
        Avalia se há variação ou desigualdade na linha de cuidado entre homens e mulheres.
        """
    )
    fig_sexo = px.box(
        df_filtrado,
        x='SEXO',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)', 'SEXO': 'Sexo'},
        title="Tempo de Espera por Sexo"
    )
    st.plotly_chart(fig_sexo, use_container_width=True)

# Boxplot por Raça/Cor
with st.expander("📊 Tempo de Espera por Raça/Cor"):
    st.markdown(
        """
        Este gráfico permite verificar diferenças no tempo de espera por categorias de raça/cor informadas no sistema.  
        Pode ser útil na análise de equidade no acesso ao procedimento.
        """
    )
    fig_raca = px.box(
        df_filtrado,
        x='RACA_COR',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)', 'RACA_COR': 'Raça/Cor'},
        title="Tempo de Espera por Raça/Cor"
    )
    st.plotly_chart(fig_raca, use_container_width=True)

# Insights automáticos
st.markdown("----")
st.subheader("📌 Insights Automáticos")

if tempo_medio > 300:
    st.warning("⚠️ Tempo médio de espera superior a 300 dias pode indicar atraso relevante na realização da FAV.")
else:
    st.success("✅ Tempo médio de espera dentro de parâmetros razoáveis.")

if prop_acima_180 > 30:
    st.warning(f"⚠️ {prop_acima_180:.1f}% dos pacientes aguardam mais de 6 meses — atenção à gestão da fila cirúrgica.")
else:
    st.info(f"ℹ️ Apenas {prop_acima_180:.1f}% dos pacientes esperam mais de 6 meses.")

if tempo_median > 300:
    st.info("📊 A mediana indica que pelo menos metade dos pacientes esperam mais de 300 dias.")

# Exportação de dados
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
st.markdown(
    """
    ### ℹ️ Sobre esta Análise

    Este painel fornece uma visão descritiva e exploratória do tempo de espera para confecção da Fístula Arteriovenosa (FAV),
    que é o acesso vascular preferencial para pacientes em diálise crônica. O atraso na realização da FAV pode comprometer
    a segurança do tratamento, aumentar o uso de cateteres e afetar negativamente os desfechos clínicos.

    Os dados apresentados são extraídos de registros administrativos (APAC-SIA/SUS) e filtrados por características clínicas, temporais e sociodemográficas.

    Use os filtros laterais para refinar a análise e explorar padrões por ano, mês, condição clínica e perfil populacional.
    """
)
