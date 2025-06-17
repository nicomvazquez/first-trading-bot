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
    api_client = BybitClient(testnet=config.TESTNET)

    # Bucle principal del bot: se ejecuta continuamente
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] Obteniendo datos para {config.SYMBOL} con intervalo {config.INTERVAL}...")

            # 2. Obtener datos de mercado (Klines)
            klines_data = api_client.get_klines(config.SYMBOL, config.INTERVAL, limit=config.SMA_LONG_PERIOD + 5) 
            
            if not klines_data:
                print("No se pudieron obtener klines. Reintentando en 1 minuto...")
                time.sleep(60)
                continue

            # Convertir los datos de klines a un DataFrame de Pandas
            df_klines = pd.DataFrame(klines_data, columns=[
                'start_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            df_klines[['open', 'high', 'low', 'close', 'volume']] = \
                df_klines[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df_klines['start_time'] = pd.to_datetime(df_klines['start_time'].astype(int), unit='ms')
            df_klines = df_klines.set_index('start_time').sort_index()

            # 3. Generar la señal de trading usando la estrategia
            signal = generate_signal(df_klines.copy()) 
            current_price = df_klines['close'].iloc[-1]
            print(f"DEBUG: Señal detectada: {signal} (en {current_price:.2f})")
            print(f"Precio actual de {config.SYMBOL}: {current_price:.2f}, Señal de estrategia: {signal}")

            # 4. Obtener información de la posición actual en Bybit
            # --- ¡AQUÍ ES DONDE CAPTURAMOS LOS TRES VALORES, INCLUIDO avg_entry_price! ---
            current_position_size, current_position_side, current_avg_entry_price = api_client.get_current_position(config.SYMBOL)
            # -----------------------------------------------------------------------------
            
            print(f"DEBUG: Variable current_position_side (dentro de main.py, ANTES DE LA LÓGICA DE SEÑAL): '{current_position_side}' (Tipo: {type(current_position_side)})")

            # 5. Obtener el balance actual de la cuenta (en USDT, o la moneda base)
            current_balance = api_client.get_wallet_balance("USDT")
            print(f"Balance actual (USDT): {current_balance:.2f}, Tamaño de posición actual: {current_position_size}, Lado: {current_position_side}")
            # Este print es útil para depuración, muestra el avgPrice si hay una posición abierta
            if current_avg_entry_price is not None:
                print(f"Precio de Entrada Promedio de la posición actual: {current_avg_entry_price:.2f}")


            # 6. Ejecutar operaciones según la señal y la posición actual
            if signal == "BUY":
                if current_position_size == 0:
                    print(f"Señal de COMPRA: Abriendo posición Long por {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Sell": 
                    print(f"Señal de COMPRA: Hay posición Short. Cerrando Short y abriendo Long...")
                    close_qty = current_position_size
                    
                    # --- CÁLCULO DE PNL ACTUALIZADO UTILIZANDO current_avg_entry_price ---
                    pnl_on_close = 0.0 # Inicializar por defecto
                    if current_avg_entry_price is not None:
                        # PNL para cerrar un SHORT: (precio_entrada - precio_cierre) * cantidad
                        pnl_on_close = (current_avg_entry_price - current_price) * close_qty
                    # -------------------------------------------------------------------
                    
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty)
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Buy", close_qty, current_price, 
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED SHORT")
                    
                    time.sleep(5) # Esperar un momento para asegurar que la orden de cierre se procese

                    # Abrir la nueva posición Long
                    order_response = api_client.place_order(config.SYMBOL, "Buy", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Buy", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Long (current_position_side == "Buy")
                    print("Señal de COMPRA: Ya en posición Long. Manteniendo.")
            
            elif signal == "SELL":
                if current_position_size == 0:
                    print(f"Señal de VENTA: Abriendo posición Short por {config.TRADE_QUANTITY} {config.SYMBOL}...")
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                elif current_position_side == "Buy": 
                    print(f"Señal de VENTA: Hay posición Long. Cerrando Long y abriendo Short...")
                    close_qty = current_position_size
                    
                    # --- CÁLCULO DE PNL ACTUALIZADO UTILIZANDO current_avg_entry_price ---
                    pnl_on_close = 0.0 # Inicializar por defecto
                    if current_avg_entry_price is not None:
                        # PNL para cerrar un LONG: (precio_cierre - precio_entrada) * cantidad
                        pnl_on_close = (current_price - current_avg_entry_price) * close_qty
                    # -------------------------------------------------------------------
                    
                    api_client.close_position(config.SYMBOL, current_position_side, close_qty)
                    log_trade(config.SYMBOL, "CLOSE_POSITION", "Sell", close_qty, current_price, 
                              pnl=pnl_on_close, balance_after_trade=current_balance, status="CLOSED LONG")
                    
                    time.sleep(5) # Esperar un momento para asegurar que la orden de cierre se procese
                    
                    # Abrir la nueva posición Short
                    order_response = api_client.place_order(config.SYMBOL, "Sell", config.TRADE_QUANTITY)
                    if order_response:
                        log_trade(config.SYMBOL, "OPEN_POSITION", "Sell", config.TRADE_QUANTITY, current_price,
                                  balance_after_trade=current_balance, order_id=order_response.get('orderId'), status="SUBMITTED")
                else: # Ya en posición Short (current_position_side == "Sell")
                    print("Señal de VENTA: Ya en posición Short. Manteniendo.")
            
            elif signal == "HOLD" or signal == "WAIT":
                print("Señal de HOLD/WAIT: No se toma ninguna acción.")

            print(f"Esperando {config.CHECK_INTERVAL_SECONDS} segundos hasta la próxima verificación...")
            time.sleep(config.CHECK_INTERVAL_SECONDS) 

        except Exception as e:
            print(f"¡Un error inesperado ocurrió en el bucle principal! Error: {e}")
            print("Reintentando en 5 minutos para evitar saturar la API o la CPU...")
            time.sleep(300)

if __name__ == "__main__":
    main_bot_loop()