import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import platform 
from streamlit_autorefresh import st_autorefresh

# --- AJUSTE PARA COMPATIBILIDADE COM NUVEM (LINUX) ---
if platform.system() == "Windows":
    import winsound
else:
    winsound = None 

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

st.title("🚀 Radar Profissional")

# 4. CARREGAR TICKERS
try:
    with open("acoes_b3.txt") as f:
        acoes = [l.strip() + ".SA" for l in f if l.strip()]
except:
    st.error("Arquivo 'acoes_b3.txt' não encontrado."); st.stop()

# 5. PROCESSAMENTO DE DADOS
dados_brutos = carregar_dados(acoes)

# AJUSTE MOBILE: No celular as colunas empilham automaticamente
col_precos, col_relatorio = st.columns([1, 3.5])

analises = []
oportunidades = []

for acao in acoes:
    res = processar_acao(acao, dados_brutos, len(acoes))
    if res:
        analises.append(res)
        if res['tipo'] != "NEUTRO" and res['rating'] >= 5: 
            oportunidades.append(res)

# --- COLUNA DE MONITORAMENTO (OTIMIZADA PARA MOBILE) ---
with col_precos:
    # Usamos um expander que vem fechado no celular para não ocupar a tela toda
    with st.expander("📊 Monitoramento de Preços", expanded=True):
        for a in analises:
            cor_seta = "🟢" if a['var'] >= 0 else "🔴"
            seta = "▲" if a['var'] >= 0 else "▼"
            # Label simplificado para caber melhor em telas estreitas
            label = f"{cor_seta} {a['nome']} | R$ {a['preco']:.2f} | {seta} {abs(a['var']):.2f}%"
            if st.button(label, key=f"btn_{a['nome']}", use_container_width=True):
                st.session_state.acao_selecionada = a['nome']

# --- COLUNA PRINCIPAL ---
with col_relatorio:
    tab_radar, tab_diario = st.tabs(["🎯 Radar", "📝 Diário"])

    with tab_radar:
        if st.session_state.acao_selecionada:
            sel = st.session_state.acao_selecionada
            info = next((x for x in analises if x['nome'] == sel), None)
            if info:
                st.markdown(f"### 📈 {sel} (5 Min)")
                fig = go.Figure(data=[go.Candlestick(x=info['df'].index, open=info['df']['Open'], high=info['df']['High'], low=info['df']['Low'], close=info['df']['Close'], name=sel)])
                fig.add_trace(go.Scatter(x=info['df'].index, y=info['df']['MA9'], line=dict(color='#2962ff', width=1.5), name='MA9'))
                fig.add_trace(go.Scatter(x=info['df'].index, y=info['df']['MA21'], line=dict(color='#ff9800', width=1.5), name='MA21'))
                # Margens zeradas para o gráfico ocupar toda a largura no celular
                fig.update_layout(xaxis_rangeslider_visible=False, height=380, margin=dict(l=0, r=0, t=10, b=0), template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                st.divider()

        if oportunidades:
            st.markdown(f"#### 🎯 Oportunidades ({len(oportunidades)})")
            df_opt = pd.DataFrame(oportunidades).sort_values(by="rating", ascending=False)
            
            # Tabela completa (pode exigir scroll horizontal no celular)
            st.dataframe(df_opt[["nome", "tipo", "rating", "score", "volat", "preco", "ent", "stp", "alv", "vol_m", "dif"]], use_container_width=True, hide_index=True)
            
            # No celular, o 'columns(3)' vira uma lista vertical
            cols_graf = st.columns(3)
            for i, row in enumerate(oportunidades):
                with cols_graf[i % 3]:
                    cor_titulo = "#00c853" if row['tipo'] == "COMPRA" else "#ff1744"
                    st.markdown(f"<div style='border-bottom: 2px solid {cor_titulo}; padding-top:10px;'><b>{row['nome']}</b> <span style='color:gray; font-size:12px;'>| R:{row['rating']}</span></div>", unsafe_allow_html=True)
                    
                    fig_opt = go.Figure(data=[go.Candlestick(x=row['df'].index, open=row['df']['Open'], high=row['df']['High'], low=row['df']['Low'], close=row['df']['Close'], name=row['nome'])])
                    fig_opt.add_trace(go.Scatter(x=row['df'].index, y=row['df']['MA9'], line=dict(color='#2962ff', width=1), name='MA9'))
                    fig_opt.add_trace(go.Scatter(x=row['df'].index, y=row['df']['MA21'], line=dict(color='#ff9800', width=1), name='MA21'))
                    
                    fig_opt.update_layout(
                        xaxis_rangeslider_visible=False, height=250, showlegend=True, 
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9)),
                        margin=dict(l=0, r=0, t=25, b=0), template="plotly_white"
                    )
                    st.plotly_chart(fig_opt, use_container_width=True)

                    if st.button(f"📝 Log {row['nome']}", key=f"log_{row['nome']}", use_container_width=True):
                        registrar_trade({
                            "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                            "Ativo": row['nome'], "Tipo": row['tipo'], "Rating": row['rating'],
                            "Entrada": round(row['ent'], 2), "Stop": round(row['stp'], 2), "Alvo": round(row['alv'], 2)
                        })
                    
                    if row['rating'] >= 8 and row['nome'] not in st.session_state.alertados:
                        st.session_state.alertados.add(row['nome'])
                        msg = (f"🔥 *SINAL DE TRADE PRO*\n\nAtivo: {row['nome']}\nOperação: {row['tipo']}\nScore: {row['score']}/10\n\n📍 Entrada: {row['ent']:.2f}\n🛡️ Stop: {row['stp']:.2f}\n🎯 Alvo: {row['alv']:.2f}")
                        enviar_alerta(msg)
                        if winsound:
                            try: winsound.Beep(1500, 600)
                            except: pass
        else:
            st.info("🔎 Monitorando...")

    with tab_diario:
        st.markdown("### 📖 Performance")
        if os.path.exists("diario_trades.csv"):
            df_diario = pd.read_csv("diario_trades.csv")
            m1, m2, m3 = st.columns(3)
            m1.metric("Trades", len(df_diario))
            m2.metric("Rating Médio", f"{df_diario['Rating'].mean():.1f}")
            m3.metric("Top Ativo", df_diario['Ativo'].mode()[0] if not df_diario.empty else "-")
            st.dataframe(df_diario.sort_index(ascending=False), use_container_width=True, hide_index=True)
            if st.button("🗑️ Limpar Histórico", use_container_width=True):
                os.remove("diario_trades.csv")
                st.rerun()