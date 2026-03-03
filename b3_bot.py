import os
import yfinance as yf
import pandas as pd
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread

# =========================
# CONFIGURAÇÕES
# =========================

TOKEN = "8759794487:AAH9Roaz5gxMw7F5lXLJ7aL2DeXWmi5gQU8"
CHAT_ID = "8352381582"

bot = Bot(token=TOKEN)

timezone = pytz.timezone("America/Sao_Paulo")
scheduler = BackgroundScheduler(timezone=timezone)

app = Flask(__name__)

# =========================
# ROTA WEB (ANTI-HIBERNAÇÃO)
# =========================

@app.route("/")
def home():
    return "Bot B3 rodando 24h"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# =========================
# ATIVOS
# =========================

ATIVOS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA",
    "BBDC4.SA", "BBAS3.SA"
]

# =========================
# INDICADORES
# =========================

def calcular_rsi(series, periodo=14):
    delta = series.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()
    rs = media_ganho / media_perda
    return 100 - (100 / (1 + rs))


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

        if mm9 > mm21:
            sinal = "🟢 Tendência Alta"
        else:
            sinal = "🔴 Tendência Baixa"

        return f"{ticker.replace('.SA','')} | R$ {preco:.2f} | RSI {rsi:.1f} | {sinal}"

    except:
        return None


# =========================
# RELATÓRIO DIÁRIO
# =========================

def enviar_relatorio():
    print("Enviando relatório...")

    mensagem = f"📊 RELATÓRIO B3\n{datetime.now(timezone).strftime('%d/%m/%Y %H:%M')}\n\n"

    for ativo in ATIVOS:
        resultado = analisar_ativo(ativo)
        if resultado:
            mensagem += resultado + "\n"

    bot.send_message(chat_id=CHAT_ID, text=mensagem)


# =========================
# INICIALIZAÇÃO
# =========================

if __name__ == "__main__":
    print("Bot + Web Server iniciando...")

    # Agenda 08:50 Brasil
    scheduler.add_job(enviar_relatorio, "cron", hour=8, minute=50)

    scheduler.start()

    # Inicia servidor web em thread separada
    Thread(target=run_web).start()
