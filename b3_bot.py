import os
import yfinance as yf
import pandas as pd
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask

TOKEN = "8709112968:AAHvkruRIiOuGK07-PI8RBWVgp7jrHqlox8"
CHAT_ID = "8709112968"

bot = Bot(token=TOKEN)

app = Flask(__name__)

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

GLOBAL = {
"S&P500": "^GSPC",
"NASDAQ": "^IXIC",
"DOW": "^DJI",
"NIKKEI": "^N225",
"DAX": "^GDAXI"
}

INDICES = {
"IBOVESPA": "^BVSP",
"DOLAR": "BRL=X",
"MINI INDICE": "WIN=F"
}

alertas_enviados = {}

def rsi(series, periodo=14):

    delta = series.diff()

    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()

    rs = media_ganho / media_perda

    return 100 - (100/(1+rs))


def analisar(ticker):

    try:

        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        close = df["Close"].squeeze()

        df["MM9"] = close.rolling(9).mean()
        df["MM21"] = close.rolling(21).mean()
        df["RSI"] = rsi(close)

        preco = close.iloc[-1]
        mm9 = df["MM9"].iloc[-1]
        mm21 = df["MM21"].iloc[-1]
        rsi_valor = df["RSI"].iloc[-1]

        cruzamento = None

        if mm9 > mm21 and df["MM9"].iloc[-2] <= df["MM21"].iloc[-2]:
            cruzamento = "🚀 CRUZAMENTO DE ALTA"

        if mm9 < mm21 and df["MM9"].iloc[-2] >= df["MM21"].iloc[-2]:
            cruzamento = "⚠️ CRUZAMENTO DE BAIXA"

        return {
            "preco": preco,
            "rsi": rsi_valor,
            "cruzamento": cruzamento
        }

    except:

        return None


def relatorio():

    mensagem = f"📊 RELATÓRIO B3\n{datetime.now().strftime('%d/%m %H:%M')}\n\n"

    mensagem += "🌎 MERCADO GLOBAL\n\n"

    for nome,ticker in GLOBAL.items():

        try:

            df = yf.download(ticker, period="5d", interval="1d", progress=False)

            close = df["Close"].squeeze()

            variacao = ((close.iloc[-1]-close.iloc[-2])/close.iloc[-2])*100

            mensagem += f"{nome}: {variacao:.2f}%\n"

        except:

            mensagem += f"{nome}: erro\n"


    mensagem += "\n📈 INDICES\n\n"

    for nome,ticker in INDICES.items():

        try:

            df = yf.download(ticker, period="5d", interval="1d", progress=False)

            close = df["Close"].squeeze()

            variacao = ((close.iloc[-1]-close.iloc[-2])/close.iloc[-2])*100

            mensagem += f"{nome}: {variacao:.2f}%\n"

        except:

            mensagem += f"{nome}: erro\n"


    mensagem += "\n🏆 TOP10 B3\n\n"

    for ativo in TOP10:

        dados = analisar(ativo)

        if dados:

            mensagem += f"{ativo.replace('.SA','')} RSI {dados['rsi']:.1f}\n"


    bot.send_message(chat_id=CHAT_ID,text=mensagem)


def alertas():

    for ativo in TOP10:

        dados = analisar(ativo)

        if dados and dados["cruzamento"]:

            if alertas_enviados.get(ativo) != dados["cruzamento"]:

                alertas_enviados[ativo] = dados["cruzamento"]

                alerta = f"""

🚨 ALERTA

{ativo.replace('.SA','')}

{dados['cruzamento']}

Preço {dados['preco']:.2f}

"""

                bot.send_message(chat_id=CHAT_ID,text=alerta)


scheduler = BackgroundScheduler()

scheduler.add_job(relatorio,'cron',hour=11,minute=50)

scheduler.add_job(alertas,'interval',minutes=15)

scheduler.start()

print("Bot rodando...")

@app.route("/")
def home():

    return "BOT ATIVO"


if __name__ == "__main__":

    port = int(os.environ.get("PORT",8080))

    app.run(host="0.0.0.0",port=port)
