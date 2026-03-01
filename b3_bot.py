import os
import yfinance as yf
import ta

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TOKEN = "8759794487:AAH9Roaz5gxMw7F5lXLJ7aL2DeXWmi5gQU8"


def analisar_ativo(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if df.empty:
            return "Sem dados"

        close = df["Close"]

        rsi = ta.momentum.RSIIndicator(close=close, window=14).rsi().dropna()

        if rsi.empty:
            return "RSI indisponível"

        rsi_atual = float(rsi.iloc[-1])

        if rsi_atual < 30:
            sinal = "🟢 COMPRA"
        elif rsi_atual > 70:
            sinal = "🔴 VENDA"
        else:
            sinal = "⚪ NEUTRO"

        return f"{sinal} (RSI {rsi_atual:.2f})"

    except Exception as e:
        return f"Erro: {str(e)}"


def gerar_relatorio():
    ativos = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA"]

    texto = "📊 RELATÓRIO B3\n\n"

    for ativo in ativos:
        texto += f"{ativo} → {analisar_ativo(ativo)}\n"

    return texto


def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Robô B3 ativo!\nDigite /relatorio")


def relatorio(update: Update, context: CallbackContext):
    update.message.reply_text(gerar_relatorio())


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("relatorio", relatorio))

    print("Bot rodando...")
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == "__main__":
    main()
