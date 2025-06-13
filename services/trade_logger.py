# services/trade_logger.py
import csv
import os
from datetime import datetime
import config # Para obtener la ruta del archivo de log

def initialize_trade_log():
    """
    Inicializa el archivo de log de operaciones (CSV) con los encabezados
    si el archivo no existe.
    """
    if not os.path.exists(config.TRADE_LOG_FILE):
        # Asegúrate de que la carpeta 'data/' exista
        os.makedirs(os.path.dirname(config.TRADE_LOG_FILE), exist_ok=True)
        with open(config.TRADE_LOG_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp", "Symbol", "Action", "Side", "Quantity", "Price",
                "PNL", "BalanceAfterTrade", "OrderID", "Status"
            ])
        print(f"Archivo de log de operaciones '{config.TRADE_LOG_FILE}' inicializado.")

def log_trade(symbol, action, side, quantity, price, pnl=None, balance_after_trade=None, order_id=None, status=""):
    """
    Registra una operación de trading en el archivo CSV.
    action: Tipo de operación (ej. "OPEN_POSITION", "CLOSE_POSITION")
    side: Lado de la orden (ej. "Buy", "Sell")
    quantity: Cantidad de la criptomoneda
    price: Precio al que se ejecutó la operación
    pnl: Ganancia/Pérdida (opcional, para cierres de posición)
    balance_after_trade: Balance de la cuenta después de la operación (opcional)
    order_id: ID de la orden de Bybit (opcional)
    status: Estado de la orden/operación (ej. "EXECUTED", "SUBMITTED")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config.TRADE_LOG_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, symbol, action, side, quantity, price,
            pnl, balance_after_trade, order_id, status
        ])
    print(f"Operación registrada: {action} {side} {quantity} {symbol} @ {price:.2f} ({status})")

# Al importar este módulo, el archivo de log se inicializará si es necesario.
initialize_trade_log()