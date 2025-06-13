# main.py
import time
import pandas as pd
from datetime import datetime

# Importa los módulos de tu proyecto
import config # Para acceder a los parámetros de configuración
from services.bybit_client import BybitClient # Tu clase para interactuar con Bybit
from strategies.simple_ma_strategy import generate_signal # Tu función de estrategia
from services.trade_logger import log_trade # Tu función para registrar operaciones

def main_bot_loop():
    print("Iniciando Bot de Trading de Bybit...")

    # 1. Inicializa el cliente de la API de Bybit
    # Usa config.TESTNET para determinar si se conecta a Testnet o a la red principal
    api_client = BybitClient(testnet=config.TESTNET)

    # Bucle principal del bot: se ejecuta continuamente
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] Obteniendo datos para {config.SYMBOL} con intervalo {config.INTERVAL}...")

            # 2. Obtener datos de mercado (Klines)
            # Obtenemos suficientes velas para que la SMA_LONG_PERIOD de la estrategia tenga datos completos
            klines_data = api_client.get_klines(config.SYMBOL, config.INTERVAL, limit=config.SMA_LONG_PERIOD + 5) 
            
            if not klines_data:
                print("No se pudieron obtener klines. Reintentando en 1 minuto...")
                time.sleep(60) # Espera 1 minuto antes de reintentar
                continue # Vuelve al inicio del bucle

            # Convertir los datos de klines a un DataFrame de Pandas
            # Formato de Bybit: [timestamp, open, high, low, close, volume, turnover]
            df_klines = pd.DataFrame(klines_data, columns=[
                'start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            # Asegurar que las columnas numéricas sean de tipo float
            df_klines[['open', 'high', 'low', 'close', 'volume']] = \
                df_klines[['open', 'high', 'low', 'close', 'volume']].astype(float)
            # Convertir timestamp a datetime y establecer como índice, luego ordenar por tiempo
            df_klines['start_time'] = pd.to_datetime(df_klines['start_time'].astype(int), unit='ms')
            df_klines = df_klines.set_index('start_time').sort_index()

            # 3. Generar la señal de trading usando la estrategia
            # Pasamos una copia del DataFrame para que la estrategia no modifique el original
            signal = generate_signal(df_klines.copy()) 
            current_price = df_klines['close'].iloc[-1] # Precio de cierre de la última vela
            print(f"Precio actual de {config.SYMBOL}: {current_price:.2f}, Señal de estrategia: {signal}")

            # 4. Obtener información de la posición actual en Bybit
            position_info = api_client.get_position_info(config.SYMBOL)
            current_position_size = float(position_info['size']) if position_info else 0.0
            current_position_side = position_info['side'] if position_info else None # "Long" o "Short"
            current_avg_entry_price = float(position_info['avgPrice']) if position_info else None

            # 5. Obtener el balance actual de la cuenta (en USDT, o la moneda base)
            current_balance = api_client.get_wallet_balance("USDT")
            print(f"Balance actual (USDT): {current_balance:.2f}, Tamaño de posición actual: {current_position_size}, Lado: {current_position_side}")

            # 6. Ejecutar operaciones según la señal y la posición actual
            if signal == "BUY":
                if current_position_size == 0:
                    # No hay posición abierta, se abre una posición Long
                    print(f"Señal de COMPRA: Abriendo posición Long por {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Short":
                    # Hay una posición Short abierta, se cierra y luego se abre un Long
                    print(f"Señal de COMPRA: Hay posición Short. Cerrando Short y abriendo Long...")
                    # Cerrar la posición Short existente
                    close_qty = current_position_size
                    # PNL aproximado al cerrar la posición Short (simple, puede variar en la práctica)
                    pnl_on_close = (current_avg_entry_price - current_price) * close_qty
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty) # Cierra el Short
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Buy", close_qty, current_price, # La acción de cerrar un short es Buy
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED SHORT")
                    
                    # Espera un momento para que se procese el cierre antes de abrir la nueva posición
                    time.sleep(5) 
                    
                    # Abrir nueva posición Long
                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Long
                    print("Señal de COMPRA: Ya en posición Long. Manteniendo.")
            
            elif signal == "SELL":
                if current_position_size == 0:
                    # No hay posición abierta, se abre una posición Short
                    print(f"Señal de VENTA: Abriendo posición Short por {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Long":
                    # Hay una posición Long abierta, se cierra y luego se abre un Short
                    print(f"Señal de VENTA: Hay posición Long. Cerrando Long y abriendo Short...")
                    # Cerrar la posición Long existente
                    close_qty = current_position_size
                    # PNL aproximado al cerrar la posición Long (simple, puede variar en la práctica)
                    pnl_on_close = (current_price - current_avg_entry_price) * close_qty
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty) # Cierra el Long
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Sell", close_qty, current_price, # La acción de cerrar un long es Sell
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED LONG")
                    
                    # Espera un momento para que se procese el cierre antes de abrir la nueva posición
                    time.sleep(5) 
                    
                    # Abrir nueva posición Short
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Short
                    print("Señal de VENTA: Ya en posición Short. Manteniendo.")
            
            elif signal == "HOLD" or signal == "WAIT":
                print("Señal de HOLD/WAIT: No se toma ninguna acción.")

            # 7. Esperar el intervalo de tiempo antes de la siguiente iteración
            # Para INTERVAL="1" (1 minuto), esperar 60 segundos
            # Ajusta este tiempo de espera según el 'INTERVAL' que uses en config.py
            # Por ejemplo, si INTERVAL fuera "5" (5 minutos), podrías esperar 300 segundos.
            print(f"Esperando {60} segundos hasta la próxima verificación...")
            time.sleep(60) 

        except Exception as e:
            print(f"¡Un error inesperado ocurrió en el bucle principal! Error: {e}")
            print("Reintentando en 5 minutos para evitar saturar la API o la CPU...")
            time.sleep(300) # Esperar más tiempo en caso de errores graves

# Esto asegura que main_bot_loop() se ejecute solo cuando el script es el principal
if __name__ == "__main__":
    main_bot_loop()