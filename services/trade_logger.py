import csv
from datetime import datetime
import os

# Define la carpeta donde se guardarán los logs
LOG_FOLDER = "data" 

# Variable global para el nombre del archivo de log de la sesión actual.
session_log_filename = None

def log_trade(symbol, action, side, quantity, price, pnl=0.0, balance_after_trade=0.0, order_id='', status=''):
    """
    Registra la información de la operación en un archivo CSV dentro de la carpeta LOG_FOLDER.
    Cada vez que el bot arranca, se genera un nuevo archivo de log con un timestamp.
    Los valores numéricos son formateados para una mejor legibilidad.
    """
    global session_log_filename 

    # Asegurarse de que la carpeta de logs exista
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
        print(f"DEBUG: Carpeta '{LOG_FOLDER}/' creada para logs.")

    # Genera el nombre completo del archivo de log para esta sesión si aún no se ha hecho
    if session_log_filename is None:
        timestamp_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Combina la carpeta con el nombre del archivo
        session_log_filename = os.path.join(LOG_FOLDER, f'trade_log_{timestamp_file_name}.csv')
        
        # Crea el nuevo archivo y escribe el encabezado
        with open(session_log_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header = ['Timestamp', 'Symbol', 'Action', 'Side', 'Quantity', 'Price', 'PNL', 'BalanceAfterTrade', 'OrderID', 'Status']
            writer.writerow(header)
        print(f"Nuevo archivo de log creado para esta sesión: {session_log_filename}")

    # Timestamp para la entrada individual del log
    timestamp_log_entry = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Formateo de los valores numéricos para mejor legibilidad ---
    formatted_quantity = f"{quantity:.8f}" if isinstance(quantity, (int, float)) else str(quantity)
    formatted_price = f"{price:.2f}" if isinstance(price, (int, float)) else str(price)
    formatted_pnl = f"{pnl:.2f}" if isinstance(pnl, (int, float)) else str(pnl)
    formatted_balance_after_trade = f"{balance_after_trade:.2f}" if isinstance(balance_after_trade, (int, float)) else str(balance_after_trade)
    # -------------------------------------------------------------------

    # Abre el archivo en modo 'a' (append) para añadir la nueva fila de datos
    with open(session_log_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            timestamp_log_entry,
            symbol,
            action,
            side,
            formatted_quantity,
            formatted_price,
            formatted_pnl,
            formatted_balance_after_trade,
            order_id,
            status
        ])

    print(f"Operación registrada en {session_log_filename}")