# config.py

# --- BYBIT API CONFIGURATION ---
# Set to True for Bybit Testnet, False for Bybit Production
# ¡IMPORTANTE! Empieza siempre con TESTNET = True para pruebas.
TESTNET = True

# --- TRADING PARAMETERS ---
SYMBOL = "BTCUSDT"  # El par de futuros que vas a operar (ej. BTCUSDT, ETHUSDT)
INTERVAL = "1"      # Intervalo de las velas: "1", "5", "15", "60" (horas), "240" (4 horas), "D" (días)
# Intervalo de tiempo entre cada verificación del bot (en segundos)
CHECK_INTERVAL_SECONDS = 60 # O el valor que prefieras, por ejemplo, 30, 120, etc.
TRADE_QUANTITY = 0.001 # Cantidad a operar por transacción (ej. 0.001 BTC). ¡Ajusta según tu capital en Testnet!

# --- STRATEGY PARAMETERS (Example: Simple Moving Average Crossover) ---
SMA_SHORT_PERIOD = 10 # Período para la Media Móvil Corta (ej. 10 velas)
SMA_LONG_PERIOD = 20  # Período para la Media Móvil Larga (ej. 20 velas)

# --- LOGGING & RECORDING ---
TRADE_LOG_FILE = "data/trade_log.csv" # Ruta del archivo para registrar operaciones
