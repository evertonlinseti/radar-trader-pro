# Módulo de dados. Aqui fica a "inteligência" matemática do seu radar.

import yfinance as yf
import pandas as pd
import streamlit as st  # Adicione esta linha!

# Faz o programa "lembrar" dos dados por 50 segundos. Se a página atualizar, ele não gasta internet baixando tudo de novo se o tempo não passou.
@st.cache_data(ttl=50)
def carregar_dados(lista_tickers):
    return yf.download(lista_tickers, period="5d", interval="5m", group_by='ticker', progress=False)

def processar_acao(acao, dados_brutos, total_acoes):
    try:
        df = dados_brutos[acao].copy() if total_acoes > 1 else dados_brutos.copy()
        df.dropna(inplace=True)
        if len(df) < 21: return None

        preco = df["Close"].iloc[-1]
        p_ant = df["Close"].iloc[-2]
        var = ((preco / p_ant) - 1) * 100
        
        # Calcula as Médias Móveis de 9 e 21 períodos e a Média de Volume.
        df["MA9"] = df["Close"].rolling(9).mean()
        df["MA21"] = df["Close"].rolling(21).mean()
        df["VOL_MED"] = df["Volume"].rolling(20).mean()
        df["RANGE_PCT"] = (df["High"] - df["Low"]) / df["Close"]
        vol_rec = df["RANGE_PCT"].rolling(20).mean().iloc[-1] # Calcula a volatilidade baseada no tamanho dos candles (High - Low).

        m9, m21 = df["MA9"].iloc[-1], df["MA21"].iloc[-1]
        v_at, v_m = df["Volume"].iloc[-1], df["VOL_MED"].iloc[-1]
        topo, fundo = df["High"].iloc[-21:-1].max(), df["Low"].iloc[-21:-1].min()

        # --- NOVA LÓGICA DE PONTUAÇÃO E RATING ---
        score = 0
        
        # 1. Tendência e Médias (Peso 3)
        if preco > m9 > m21: score += 3 # Tendência de Alta
        elif preco < m9 < m21: score += 3 # Tendência de Baixa
        
        # 2. Volume (Peso 4)
        if v_at > v_m: score += 2 # Volume acima da média
        if v_at > v_m * 1.5: score += 2 # Volume forte (1.5x a média)
        
        # 3. Rompimento de Extremos (Peso 3)
        if preco >= topo or preco <= fundo: score += 3 

        # Cálculo do Rating Final (Escala 0 a 10)
        # Como o score máximo possível é 10, o rating será o próprio score
        rating = min(score, 10) 

        # --- DEFINIÇÃO DO TIPO DE OPERAÇÃO ---
        tipo = "NEUTRO"
        ent, stp, alv, dif = 0, 0, 0, 0
        
        # Compra: Preço acima das médias E rompendo topo
        if preco > m9 > m21 and preco >= topo:
            tipo = "COMPRA"
            ent = topo
            stp = fundo
            alv = topo + (topo - fundo) * 0.8
            dif = ((topo + (topo - fundo) * 0.8)- preco-fundo) - (preco-fundo)
            
            
        # Venda: Preço abaixo das médias E rompendo fundo
        elif preco < m9 < m21 and preco <= fundo:
            tipo = "VENDA"
            ent = fundo
            stp = topo
            alv = fundo - (topo - fundo) * 0.8
            dif = ((topo + (topo - fundo) * 0.8)- preco-fundo) - (preco-fundo)

        return {
            "nome": acao.replace(".SA",""),
            "preco": preco, 
            "var": var, 
            "df": df.tail(40),
            "tipo": tipo, 
            "rating": int(rating), 
            "score": int(score),
            "volat": f"{vol_rec:.2%}", 
            "ent": ent, 
            "stp": stp, 
            "alv": alv,
            "dif":dif,
            "vol_m": round(v_at/v_m, 1)
        }
    except: return None