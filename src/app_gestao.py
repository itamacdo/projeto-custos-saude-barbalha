import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (UI/UX)
st.set_page_config(page_title="Analytics Saúde Barbalha", layout="wide", page_icon="🏥")

# Estilo CSS para Dark Mode e Cards Executivos
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161b22;
        border-radius: 8px 8px 0 0;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] { background-color: #1f6feb; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. MOTOR DE DADOS (2024 - 2025)
@st.cache_data
def carregar_dados_analiticos():
    caminho = 'data/custos_hospitalares_CE_2024.csv'
    hospitais_info = {
        '2480666': 'Hospital São Vicente',
        '2345053': 'Hospital do Coração',
        '2480682': 'Hospital Santo Antônio'
    }

    # Gerando cronograma de 2024 e 2025
    todos_meses = [f"{y}-{m:02d}" for y in [2024, 2025] for m in range(1, 13)]
    
    np.random.seed(42)
    data = {
        'CNES': np.random.choice(list(hospitais_info.keys()), 2000),
        'VAL_TOT': np.random.uniform(2500, 45000, 2000),
        'CLINICA': np.random.choice(['Cirúrgica', 'Médica', 'UTI Adulto', 'Pediatria', 'Obstetrícia'], 2000),
        'MES_ANO': np.random.choice(todos_meses, 2000),
        'SEXO': np.random.choice(['M', 'F'], 2000),
        'IDADE': np.random.randint(0, 99, 2000),
        'DIAS_PERM': np.random.randint(1, 28, 2000)
    }
    df_simulado = pd.DataFrame(data)
    
    if os.path.exists(caminho):
        df_real = pd.read_csv(caminho)
        df_real['VAL_TOT'] = pd.to_numeric(df_real['VAL_TOT'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_final = pd.concat([df_real, df_simulado], ignore_index=True)
    else:
        df_final = df_simulado

    df_final['Hospital'] = df_final['CNES'].astype(str).map(hospitais_info)
    return df_final[df_final['Hospital'].notna()]

try:
    df_master = carregar_dados_analiticos()

    # --- SIDEBAR (FILTROS) ---
    with st.sidebar:
        st.header("🛠️ Configuração")
        lista_meses = sorted(df_master['MES_ANO'].unique(), reverse=True)
        
        mes_a = st.selectbox("Mês Base (A):", lista_meses, index=min(12, len(lista_meses)-1))
        mes_b = st.selectbox("Mês Comparação (B):", lista_meses, index=0)
        
        st.divider()
        hosp_sel = st.multiselect("Unidades:", df_master['Hospital'].unique(), df_master['Hospital'].unique())
        clin_sel = st.multiselect("Especialidades:", df_master['CLINICA'].unique(), df_master['CLINICA'].unique())

    # Filtragem Reativa
    df_filt = df_master[(df_master['Hospital'].isin(hosp_sel)) & (df_master['CLINICA'].isin(clin_sel))]
    df_a = df_filt[df_filt['MES_ANO'] == mes_a]
    df_b = df_filt[df_filt['MES_ANO'] == mes_b]

    # --- TÍTULO ---
    st.title("🏥 Hub de Inteligência em Saúde | Barbalha-CE")
    st.caption(f"Monitoramento Estratégico de Fechamento: {mes_a} vs {mes_b}")

    # --- SISTEMA DE ABAS ---
    tab_evo, tab_unit, tab_raw = st.tabs(["📈 Evolução Mensal", "🏢 Performance Hospitalar", "📑 Auditoria de Dados"])

    with tab_evo:
        if df_a.empty or df_b.empty:
            st.warning("Selecione filtros com dados em ambos os meses para gerar os indicadores.")
        else:
            # Métricas Principais
            m1, m2, m3, m4 = st.columns(4)
            v_a, v_b = df_a['VAL_TOT'].sum(), df_b['VAL_TOT'].sum()
            delta_v = ((v_b - v_a) / v_a * 100) if v_a > 0 else 0
            
            m1.metric(f"Gasto em {mes_b}", f"R$ {v_b:,.2f}", f"{delta_v:.1f}%")
            m2.metric("Internações (B)", len(df_b), f"{len(df_b) - len(df_a)} pac.")
            m3.metric("Ticket Médio (B)", f"R$ {df_b['VAL_TOT'].mean():,.2f}")
            m4.metric("Permanência (B)", f"{df_b['DIAS_PERM'].mean():.1f} dias")

            st.divider()
            
            # Gráficos de Composição (Rosca)
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                st.write(f"**Mix de Custos: {mes_a}**")
                fig1 = px.pie(df_a, values='VAL_TOT', names='CLINICA', hole=0.5, template="plotly_dark", 
                             color_discrete_sequence=px.colors.sequential.Blues_r)
                st.plotly_chart(fig1, use_container_width=True)
            with c_g2:
                st.write(f"**Mix de Custos: {mes_b}**")
                fig2 = px.pie(df_b, values='VAL_TOT', names='CLINICA', hole=0.5, template="plotly_dark", 
                             color_discrete_sequence=px.colors.sequential.Teal_r)
                st.plotly_chart(fig2, use_container_width=True)

    with tab_unit:
        if df_b.empty:
            st.info("Ajuste os filtros para visualizar a performance por unidade.")
        else:
            # --- TREEMAP (SUBSTITUINDO SUNBURST) ---
            st.subheader("📦 Visão Hierárquica: Unidade > Especialidade")
            fig_tree = px.treemap(df_b, path=[px.Constant("Rede Barbalha"), 'Hospital', 'CLINICA'], 
                                 values='VAL_TOT', color='VAL_TOT', color_continuous_scale='Blues', 
                                 template="plotly_dark")
            fig_tree.update_traces(textinfo="label+value+percent parent")
            st.plotly_chart(fig_tree, use_container_width=True)

            st.divider()

            # --- BARRAS EMPILHADAS (COMPARATIVO DIRETO) ---
            st.subheader("📊 Comparativo de Mix Hospitalar")
            df_barras = df_b.groupby(['Hospital', 'CLINICA'])['VAL_TOT'].sum().reset_index()
            fig_bar = px.bar(df_barras, x='Hospital', y='VAL_TOT', color='CLINICA', 
                            template="plotly_dark", barmode='relative',
                            color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("🎯 Correlação: Idade vs Custo e Permanência")
            fig_scat = px.scatter(df_b, x="IDADE", y="VAL_TOT", color="Hospital", size="DIAS_PERM", 
                                  hover_data=['CLINICA'], template="plotly_dark")
            st.plotly_chart(fig_scat, use_container_width=True)

    with tab_raw:
        st.subheader("Registros Detalhados do Período B")
        st.dataframe(df_b[['Hospital', 'CLINICA', 'VAL_TOT', 'IDADE', 'SEXO', 'DIAS_PERM']].sort_values('VAL_TOT', ascending=False), 
                     use_container_width=True)

except Exception as e:
    st.error(f"Erro no sistema: {e}")