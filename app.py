import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import platform # Necessário para verificar o sistema operacional
from streamlit_autorefresh import st_autorefresh

# --- AJUSTE PARA COMPATIBILIDADE COM NUVEM (LINUX) ---
if platform.system() == "Windows":
    import winsound
else:
    winsound = None # Desativa o som se não estiver no Windows

# Importações dos seus módulos locais
from modules.alerts import enviar_alerta
from modules.data_engine import carregar_dados, processar_acao

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar Trader Pro V2.2", layout="wide")

# 1. CARREGAR CSS
try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except: 
    pass

# 2. FUNÇÃO DIÁRIO DE TRADE (LOG)
def registrar_trade(dados):
    """Salva a operação em um arquivo CSV para acompanhamento posterior."""
    arquivo = "diario_trades.csv"
    df_log = pd.DataFrame([dados])
    if os.path.exists(arquivo):
        df_existente = pd.read_csv(arquivo)
        df_final = pd.concat([df_existente, df_log], ignore_index=True)
    else:
        df_final = df_log
    df_final.to_csv(arquivo, index=False)
    st.toast(f"✅ Trade de {dados['Ativo']} registrado!")

# 3. ESTADOS E REFRESH
if "alertados" not in st.session_state: st.session_state.alertados = set()
if "acao_selecionada" not in st.session_state: st.session_state.acao_selecionada = None

st_autorefresh(interval=60000, key="refresh")

st.title("🚀 Radar Profissional - Rating, Pontuação e Volatilidade")

# 4. CARREGAR TICKERS
try:
    with open("acoes_b3.txt") as f:
        acoes = [l.strip() + ".SA" for l in f if l.strip()]
except:
    st.error("Arquivo 'acoes_b3.txt' não encontrado."); st.stop()

# 5. PROCESSAMENTO DE DADOS
dados_brutos = carregar_dados(acoes)
col_precos, col_relatorio = st.columns([1.2, 4])

analises = []
oportunidades = []

for acao in acoes:
    res = processar_acao(acao, dados_brutos, len(acoes))
    if res:
        analises.append(res)
        if res['tipo'] != "NEUTRO" and res['rating'] >= 5: 
            oportunidades.append(res)

# --- COLUNA LATERAL ---
with col_precos:
    st.markdown("### 📊 Monitoramento")
    st.caption("Tempo Gráfico: 5 Minutos")
    
    for a in analises:
        cor_seta = "🟢" if a['var'] >= 0 else "🔴"
        seta = "▲" if a['var'] >= 0 else "▼"
        label = f"{cor_seta} {a['nome']} | R$ {a['preco']:.2f} | {seta} {abs(a['var']):.2f}%"
        if st.button(label, key=f"btn_{a['nome']}"):
            st.session_state.acao_selecionada = a['nome']

# --- COLUNA PRINCIPAL ---
with col_relatorio:
    tab_radar, tab_diario = st.tabs(["🎯 Radar de Oportunidades", "📝 Diário de Trade"])

    with tab_radar:
        # A. Gráfico em Foco
        if st.session_state.acao_selecionada:
            sel = st.session_state.acao_selecionada
            info = next((x for x in analises if x['nome'] == sel), None)
            if info:
                st.markdown(f"### 📈 Gráfico em Foco: {sel} <span style='font-size: 14px; color: gray;'>(5 Min)</span>", unsafe_allow_html=True)
                fig = go.Figure(data=[go.Candlestick(x=info['df'].index, open=info['df']['Open'], high=info['df']['High'], low=info['df']['Low'], close=info['df']['Close'], name=sel)])
                fig.add_trace(go.Scatter(x=info['df'].index, y=info['df']['MA9'], line=dict(color='#2962ff', width=1.5), name='MA9'))
                fig.add_trace(go.Scatter(x=info['df'].index, y=info['df']['MA21'], line=dict(color='#ff9800', width=1.5), name='MA21'))
                fig.update_layout(xaxis_rangeslider_visible=False, height=350, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                st.divider()

        # B. Oportunidades
        if oportunidades:
            st.markdown(f"#### 🎯 Oportunidades Detectadas ({len(oportunidades)})")
            df_opt = pd.DataFrame(oportunidades).sort_values(by="rating", ascending=False)
            
            # Utilizando o modelo de tabela mais completo (inferior) com vol_m e dif
            st.dataframe(df_opt[["nome", "tipo", "rating", "score", "volat", "preco", "ent", "stp", "alv", "vol_m", "dif"]], use_container_width=True, hide_index=True)
            
            cols_graf = st.columns(3)
            for i, row in enumerate(oportunidades):
                with cols_graf[i % 3]:
                    cor_titulo = "#00c853" if row['tipo'] == "COMPRA" else "#ff1744"
                    st.markdown(f"<div style='border-bottom: 2px solid {cor_titulo};'><b>{row['nome']}</b> <span style='color:gray; font-size:12px;'>| R:{row['rating']}</span></div>", unsafe_allow_html=True)
                    
                    # Mini gráfico com MA9, MA21 e legenda
                    fig_opt = go.Figure(data=[go.Candlestick(x=row['df'].index, open=row['df']['Open'], high=row['df']['High'], low=row['df']['Low'], close=row['df']['Close'], name=row['nome'])])
                    fig_opt.add_trace(go.Scatter(x=row['df'].index, y=row['df']['MA9'], line=dict(color='#2962ff', width=1), name='MA9'))
                    fig_opt.add_trace(go.Scatter(x=row['df'].index, y=row['df']['MA21'], line=dict(color='#ff9800', width=1), name='MA21'))
                    
                    fig_opt.update_layout(
                        xaxis_rangeslider_visible=False, 
                        height=250, 
                        showlegend=True, 
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                        margin=dict(l=5, r=5, t=25, b=5), 
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_opt, use_container_width=True)

                    if st.button(f"📝 Log {row['nome']}", key=f"log_{row['nome']}"):
                        registrar_trade({
                            "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                            "Ativo": row['nome'], "Tipo": row['tipo'], "Rating": row['rating'],
                            "Entrada": round(row['ent'], 2), "Stop": round(row['stp'], 2), "Alvo": round(row['alv'], 2)
                        })
                    
                    # Mensagem profissional com 2 casas decimais
                    if row['rating'] >= 8 and row['nome'] not in st.session_state.alertados:
                        st.session_state.alertados.add(row['nome'])
                        msg = (
                            f"🔥 *SINAL DE TRADE PRO*\n\n"
                            f"Ação: {row['nome']}\n"
                            f"Operação: {row['tipo']}\n"
                            f"Score: {row['score']}/10\n\n"
                            f"📍 Entrada: {row['ent']:.2f}\n"
                            f"🛡️ Stop: {row['stp']:.2f}\n"
                            f"🎯 Alvo: {row['alv']:.2f}"
                        )
                        enviar_alerta(msg)
                        if winsound: # Só toca o bip se estiver no Windows
                            try: winsound.Beep(1500, 600)
                            except: pass
        else:
            st.info("🔎 Monitorando mercado...")

    with tab_diario:
        st.markdown("### 📖 Histórico e Performance")
        if os.path.exists("diario_trades.csv"):
            df_diario = pd.read_csv("diario_trades.csv")
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total de Trades", len(df_diario))
            m2.metric("Média de Rating", f"{df_diario['Rating'].mean():.1f}/10")
            m3.metric("Ativo mais Operado", df_diario['Ativo'].mode()[0] if not df_diario.empty else "-")

            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                fig_pizza = px.pie(df_diario, names='Tipo', title='Distribuição Compra/Venda', color='Tipo',
                                  color_discrete_map={'COMPRA':'#00c853', 'VENDA':'#ff1744'})
                st.plotly_chart(fig_pizza, use_container_width=True)
            
            with col_chart2:
                fig_bar = px.bar(df_diario['Ativo'].value_counts(), title='Frequência por Ativo')
                st.plotly_chart(fig_bar, use_container_width=True)

            st.dataframe(df_diario.sort_index(ascending=False), use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Limpar Histórico"):
                os.remove("diario_trades.csv")
                st.rerun()
        else:
            st.info("Registre trades para ver sua performance aqui.")