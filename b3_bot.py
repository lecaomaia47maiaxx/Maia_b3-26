import os
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

TOKEN = "8759794487:AAH9Roaz5gxMw7F5lXLJ7aL2DeXWmi5gQU8"
CHAT_ID = "8352381582"

bot = Bot(token=TOKEN)

# =========================
# CONFIGURAÇÕES
# =========================

ATIVOS_PRINCIPAIS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "BBAS3.SA"
]

TOP_10_LIQUIDAS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "BBAS3.SA",
    "WEGE3.SA",
    "ABEV3.SA",
    "RENT3.SA",
    "JBSS3.SA",
    "MGLU3.SA"
]

INDICES = {
    "🇧🇷 IBOVESPA": "^BVSP",
    "🇺🇸 S&P500": "^GSPC",
    "🇺🇸 NASDAQ": "^IXIC",
    "💵 DÓLAR": "BRL=X",
    "📉 MINI ÍNDICE": "WIN=F"
}

# Controle de alertas para não repetir
ultimos_sinais = {}

# =========================
# FUNÇÕES
# =========================

def calcular_rsi(series, periodo=14):
    delta = series.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()

    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return rsi


def analisar_ativo(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if df.empty:
            return None

        close = df["Close"].squeeze()

        df["MM9"] = close.rolling(9).mean()
        df["MM21"] = close.rolling(21).mean()
        df["RSI"] = calcular_rsi(close)

        preco = close.iloc[-1]
        mm9 = df["MM9"].iloc[-1]
        mm21 = df["MM21"].iloc[-1]
        rsi = df["RSI"].iloc[-1]

        # Detectar cruzamento
        if mm9 > mm21 and df["MM9"].iloc[-2] <= df["MM21"].iloc[-2]:
            sinal = "🚀 CRUZAMENTO DE ALTA"
        elif mm9 < mm21 and df["MM9"].iloc[-2] >= df["MM21"].iloc[-2]:
            sinal = "⚠️ CRUZAMENTO DE BAIXA"
        elif mm9 > mm21:
            sinal = "🟢 Tendência de Alta"
        else:
            sinal = "🔴 Tendência de Baixa"

        return {
            "ticker": ticker.replace(".SA", ""),
            "preco": preco,
            "rsi": rsi,
            "sinal": sinal
        }

    except:
        return None


# =========================
# RELATÓRIO DIÁRIO
# =========================

def enviar_relatorio_diario():
    mensagem = f"📊 RELATÓRIO COMPLETO B3\n{datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"

    mensagem += "🔎 ATIVOS PRINCIPAIS\n\n"

    for ativo in ATIVOS_PRINCIPAIS:
        dados = analisar_ativo(ativo)
        if dados:
            mensagem += (
                f"📈 {dados['ticker']}\n"
                f"Preço: R$ {dados['preco']:.2f}\n"
                f"RSI: {dados['rsi']:.2f}\n"
                f"Sinal: {dados['sinal']}\n\n"
            )

    mensagem += "🏆 TOP 10 MAIS LÍQUIDAS\n\n"

    for ativo in TOP_10_LIQUIDAS:
        dados = analisar_ativo(ativo)
        if dados:
            mensagem += f"{dados['ticker']} → {dados['sinal']}\n"

    mensagem += "\n🌎 MERCADO GLOBAL\n\n"

    for nome, ticker in INDICES.items():
        try:
            df = yf.download(ticker, period="5d", interval="1d", progress=False)
            close = df["Close"].squeeze()
            variacao = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100

            status = "🟢 Alta" if variacao > 0 else "🔴 Baixa"

            mensagem += f"{nome}: {variacao:.2f}% ({status})\n"
        except:
            mensagem += f"{nome}: erro\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)


# =========================
# ALERTAS AUTOMÁTICOS
# =========================

def verificar_cruzamentos():
    for ativo in TOP_10_LIQUIDAS:
        dados = analisar_ativo(ativo)
        if dados and "CRUZAMENTO" in dados["sinal"]:

            # evitar repetição
            if ultimos_sinais.get(ativo) != dados["sinal"]:
                ultimos_sinais[ativo] = dados["sinal"]

                alerta = (
                    f"🚨 ALERTA DE MERCADO\n\n"
                    f"{dados['ticker']}\n"
                    f"Sinal: {dados['sinal']}\n"
                    f"Preço: R$ {dados['preco']:.2f}"
                )

                bot.send_message(chat_id=CHAT_ID, text=alerta)


# =========================
# AGENDAMENTO
# =========================

if __name__ == "__main__":
    print("Bot profissional rodando...")

    scheduler = BlockingScheduler()

    # 08:50 Brasil = 11:50 UTC
    scheduler.add_job(enviar_relatorio_diario, "cron", hour=11, minute=50)

    # Verificação de cruzamentos a cada 15 minutos
    scheduler.add_job(verificar_cruzamentos, "interval", minutes=15)

    scheduler.start()
