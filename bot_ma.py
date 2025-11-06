# -*- coding: utf-8 -*-
import ccxt
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# ========================
# CARGAR VARIABLES DEL .env
# ========================
load_dotenv()

api_key = os.getenv("KUCOIN_API_KEY")
api_secret = os.getenv("KUCOIN_API_SECRET")
api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")

is_sandbox = os.getenv("IS_SANDBOX", "False").lower() == "true"

symbol = "BTC/USDT"
timeframe = "1h"

# ========================
# CONEXIÓN A KUCOIN
# ========================
exchange = ccxt.kucoin({
    'apiKey': api_key,
    'secret': api_secret,
    'password': api_passphrase
})

if is_sandbox:
    exchange.urls['api'] = {
        'public': 'https://openapi-sandbox.kucoin.com',
        'private': 'https://openapi-sandbox.kucoin.com',
    }
    print("✅ Modo Sandbox activado (con URL personalizada)")
else:
    print("⚠️ Modo Real activado — cuidado con las órdenes reales")

# ========================
# VARIABLES DE SIMULACIÓN
# ========================
balance_usdt = 1000.0  # saldo inicial ficticio
balance_btc = 0.0
ultima_operacion = "SELL"
precio_ultima_compra = None
profit_total = 0.0
log_file = "operaciones.csv"

# Crear CSV si no existe
if not os.path.exists(log_file):
    df_log = pd.DataFrame(columns=[
        "fecha", "accion", "precio", "balance_usdt", 
        "balance_btc", "balance_total", "profit_loss_%", "profit_total_%"
    ])
    df_log.to_csv(log_file, index=False)

# ========================
# CONFIGURACIÓN DE GRÁFICA
# ========================
plt.ion()
fig, ax = plt.subplots()
balances = []
tiempos = []

def actualizar_grafica():
    ax.clear()
    ax.plot(tiempos, balances, marker='o', linestyle='-', label='Balance total (USDT)')
    ax.set_title("Evolución del balance simulado 💰")
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Balance total (USDT)")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.pause(0.1)

# ========================
# FUNCIONES
# ========================
def get_data():
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=150)
    df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def estrategia(df):
    df["MA_20"] = df["close"].rolling(20).mean()
    df["MA_50"] = df["close"].rolling(50).mean()

    if df["MA_20"].iloc[-2] < df["MA_50"].iloc[-2] and df["MA_20"].iloc[-1] > df["MA_50"].iloc[-1]:
        return "BUY"
    elif df["MA_20"].iloc[-2] > df["MA_50"].iloc[-2] and df["MA_20"].iloc[-1] < df["MA_50"].iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

def registrar_operacion(accion, precio, balance_usdt, balance_btc, balance_total, profit_loss, profit_total):
    data = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accion": accion,
        "precio": precio,
        "balance_usdt": round(balance_usdt, 2),
        "balance_btc": round(balance_btc, 6),
        "balance_total": round(balance_total, 2),
        "profit_loss_%": round(profit_loss, 2),
        "profit_total_%": round(profit_total, 2)
    }
    df = pd.DataFrame([data])
    df.to_csv(log_file, mode="a", header=False, index=False)

def simular_operacion(señal, precio_actual):
    global balance_usdt, balance_btc, ultima_operacion, precio_ultima_compra, profit_total

    profit_loss = 0.0

    if señal == "BUY" and ultima_operacion != "BUY":
        if balance_usdt > 0:
            balance_btc = balance_usdt / precio_actual
            balance_usdt = 0
            ultima_operacion = "BUY"
            precio_ultima_compra = precio_actual
            print(f"🟢 Compra simulada: {balance_btc:.6f} BTC a ${precio_actual:.2f}")
        else:
            print("⚠️ No hay USDT suficiente para comprar.")

    elif señal == "SELL" and ultima_operacion != "SELL":
        if balance_btc > 0:
            balance_usdt = balance_btc * precio_actual
            balance_btc = 0
            ultima_operacion = "SELL"

            if precio_ultima_compra:
                profit_loss = ((precio_actual - precio_ultima_compra) / precio_ultima_compra) * 100
                profit_total += profit_loss
                print(f"📈 Resultado de operación: {profit_loss:.2f}%")
                print(f"💹 Ganancia acumulada: {profit_total:.2f}%")

            print(f"🔴 Venta simulada: ${balance_usdt:.2f} USDT a ${precio_actual:.2f}")
        else:
            print("⚠️ No hay BTC suficiente para vender.")

    valor_total = balance_usdt + (balance_btc * precio_actual)

    # Guardar en CSV y graficar si hubo operación
    if señal in ["BUY", "SELL"]:
        registrar_operacion(señal, precio_actual, balance_usdt, balance_btc, valor_total, profit_loss, profit_total)
        tiempos.append(datetime.now().strftime("%H:%M:%S"))
        balances.append(valor_total)
        actualizar_grafica()

    return valor_total

# ========================
# LOOP PRINCIPAL
# ========================
while True:
    try:
        df = get_data()
        señal = estrategia(df)
        precio_actual = df["close"].iloc[-1]

        print(f"\n📊 Señal actual: {señal} | Precio: ${precio_actual:.2f}")

        total = simular_operacion(señal, precio_actual)
        print(f"💰 Balance total simulado: ${total:.2f} (USDT: {balance_usdt:.2f}, BTC: {balance_btc:.6f})")

        time.sleep(10)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        time.sleep(10)
