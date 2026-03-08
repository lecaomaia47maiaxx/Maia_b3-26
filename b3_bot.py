import os
import yfinance as yf
from datetime import datetime
from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# =============================
# CONFIGURAÇÃO TELEGRAM
# =============================

TOKEN = "8709112968:AAHvkruRIiOuGK07-PI8RBWVgp7jrHqlox8"
CHAT_ID = "8709112968"

bot = Bot(token=TOKEN)

# =============================
# FLASK
# =============================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT ATIVO"

# =============================
# ATIVOS MONITORADOS
# =============================

ATIVOS = [
"PETR4.SA",
"VALE3.SA",
"ITUB4.SA",
"BBDC4.SA",
"BBAS3.SA"
]

# =============================
# ANALISE SIMPLES
# =============================

def analisar():

    print("Executando análise:", datetime.now())

    for ativo in ATIVOS:

        try:

            df = yf.download(
                ativo,
                period="5d",
                interval="1d",
                progress=False
            )

            preco = df["Close"].iloc[-1]

            print(ativo, preco)

        except Exception as e:

            print("Erro:", e)


# =============================
# TESTE DE VIDA
# =============================

def heartbeat():

    print("BOT ONLINE:", datetime.now())


# =============================
# SCHEDULER
# =============================

scheduler = BackgroundScheduler()

scheduler.add_job(analisar, "interval", minutes=1)
scheduler.add_job(heartbeat, "interval", minutes=2)

scheduler.start()

print("Bot rodando...")

# =============================
# START SERVER
# =============================

port = int(os.environ.get("PORT", 8080))

app.run(host="0.0.0.0", port=port)
