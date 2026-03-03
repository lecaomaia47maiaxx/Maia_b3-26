import os
import yfinance as yf
import pandas as pd
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, time
import pytz

# =========================
# CONFIGURAÇÕES
# =========================

TOKEN = "8759794487:AAH9Roaz5gxMw7F5lXLJ7aL2DeXWmi5gQU8"
CHAT_ID = "8352381582"

bot = Bot(token=TOKEN)

timezone = pytz.timezone("America/Sao_Paulo")
scheduler = BlockingScheduler(timezone=timezone)

ATIVOS_PRINCIPAIS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA",
    "BBDC4.SA", "BBAS3.SA"
]

TOP_10_LIQUIDAS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA",
    "BBDC4.SA", "BBAS3.SA", "WEGE3.SA",
    "ABEV3.SA", "RENT3.SA", "JBSS3.SA",
    "MGLU3.SA"
]

INDICES = {
    "🇧🇷 IBOVESPA": "^BVSP",
    "🇺🇸 S&P500": "^GSPC",
    "🇺🇸 NASDAQ": "^IXIC",
    "💵 DÓLAR": "BRL=X",
    "📉 MINI ÍNDICE": "WIN=F"
}

ultimos_sinais = {}
relatorio_enviado_hoje = False

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
            "preco": float(preco),
            "rsi": float(rsi),
            "sinal": sinal
        }

    except Exception as e:
        print(f"Erro em {ticker}: {e}")
        return None


# =========================
# RELATÓRIO
# =========================

def enviar_relatorio_diario():
    global relatorio_enviado_hoje

    if relatorio_enviado_hoje:
        return

    print("Enviando relatório diário...")

    mensagem = f"📊 RELATÓRIO COMPLETO B3\n{datetime.now(timezone).strftime('%d/%m/%Y %H:%M')}\n\n"
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
    relatorio_enviado_hoje = True


# =========================
# ALERTAS 15 MIN
# =========================

def verificar_cruzamentos():
    print("Verificando cruzamentos...")

    for ativo in TOP_10_LIQUIDAS:
        dados = analisar_ativo(ativo)

        if dados and "CRUZAMENTO" in dados["sinal"]:
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
# INICIALIZAÇÃO INTELIGENTE
# =========================

def checar_envio_automatico():
    agora = datetime.now(timezone).time()
    horario_disparo = time(8, 50)

    if agora >= horario_disparo:
        enviar_relatorio_diario()


if __name__ == "__main__":
    print("Bot profissional rodando...")

    # Se reiniciar depois das 08:50, envia automaticamente
    checar_envio_automatico()

    # Agenda para 08:50 todos os dias
    scheduler.add_job(enviar_relatorio_diario, "cron", hour=8, minute=50)

    # Cruzamentos a cada 15 minutos
    scheduler.add_job(verificar_cruzamentos, "interval", minutes=15)

    scheduler.start()
