import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# =============================
# CONFIGURAÇÕES
# =============================

TOKEN = "8709112968:AAHvkruRIiOuGK07-PI8RBWVgp7jrHqlox8"
CHAT_ID = "8709112968"

bot = Bot(token=TOKEN)

# =============================
# FLASK SERVER (necessário para Railway)
# =============================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT ATIVO"

# =============================
# LISTA DE ATIVOS
# =============================

TOP10 = [
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

# =============================
# RSI
# =============================

def rsi(series, periodo=14):

    delta = series.diff()

    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()

    rs = media_ganho / media_perda

    return 100 - (100/(1+rs))


# =============================
# ANALISE
# =============================

def analisar(ticker):

    try:

        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        close = df["Close"]

        df["MM9"] = close.rolling(9).mean()
        df["MM21"] = close.rolling(21).mean()

        preco = close.iloc[-1]

        mm9 = df["MM9"].iloc[-1]
        mm21 = df["MM21"].iloc[-1]

        cruzamento = None

        if mm9 > mm21 and df["MM9"].iloc[-2] <= df["MM21"].iloc[-2]:
            cruzamento = "🚀 Cruzamento de ALTA"

        if mm9 < mm21 and df["MM9"].iloc[-2] >= df["MM21"].iloc[-2]:
            cruzamento = "⚠️ Cruzamento de BAIXA"

        return preco, cruzamento

    except Exception as e:

        print("Erro ao analisar", ticker, e)

        return None, None


# =============================
# ALERTAS
# =============================

def verificar_alertas():

    print("Executando verificação:", datetime.now())

    for ativo in TOP10:

        preco, cruzamento = analisar(ativo)

        if cruzamento:

            msg = f"""
🚨 ALERTA

Ativo: {ativo.replace('.SA','')}
{cruzamento}

Preço: {preco:.2f}
"""

            print(msg)

            bot.send_message(
                chat_id=CHAT_ID,
                text=msg
            )


# =============================
# TESTE DE VIDA
# =============================

def heartbeat():

    print("BOT ATIVO:", datetime.now())


# =============================
# SCHEDULER
# =============================

scheduler = BackgroundScheduler()

# verificação de mercado
scheduler.add_job(verificar_alertas, "interval", minutes=1)

# log de vida
scheduler.add_job(heartbeat, "interval", minutes=2)

scheduler.start()

print("Bot rodando...")

# =============================
# START FLASK
# =============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))

    app.run(host="0.0.0.0", port=port)
