# services/bybit_client.py
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

# Carga las variables de entorno del archivo .env al inicio de la ejecución
load_dotenv()

class BybitClient:
    def __init__(self, testnet=False):
        # Obtiene las claves API de las variables de entorno
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY o BYBIT_API_SECRET no se encontraron en el archivo .env. Asegúrate de configurarlos.")

        # Inicializa la sesión HTTP con la API unificada de Bybit
        self.session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret
        )
        print(f"Bybit API Client inicializado (Testnet: {testnet})")

    def get_klines(self, symbol, interval, limit=200):
        """
        Obtiene datos de velas (candlesticks) de Bybit.
        symbol: El par de trading (ej. "BTCUSDT")
        interval: La temporalidad de las velas (ej. "1", "5", "60", "D")
        limit: Número de velas a obtener (máximo 1000 por solicitud).
        """
        try:
            response = self.session.get_kline(
                category="linear", # Para futuros perpetuos (USD-M)
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            if response and 'result' in response and 'list' in response['result']:
                # Las klines se devuelven en orden descendente (las más nuevas primero).
                # Las invertimos para que las más antiguas estén al principio, que es útil para análisis.
                return response['result']['list'][::-1]
            else:
                print(f"Error al obtener klines para {symbol} ({interval}): {response}")
                return []
        except Exception as e:
            print(f"Excepción en get_klines para {symbol} ({interval}): {e}")
            return []

    def place_order(self, symbol, side, qty, order_type="Market"):
        """
        Coloca una orden de trading en Bybit.
        symbol: El par de trading (ej. "BTCUSDT")
        side: "Buy" (compra) o "Sell" (venta)
        qty: Cantidad de la orden (como string para la API)
        order_type: "Market" (mercado) o "Limit" (límite). Por defecto "Market".
        """
        try:
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty), # La cantidad debe ser un string para la API
                "isLeverage": 1, # Generalmente 1 para futuros perpetuos (apalancamiento habilitado)
                "timeInForce": "GTC" # Good Till Cancel (la orden permanece hasta que se ejecuta o se cancela)
            }
            
            response = self.session.place_order(**order_params)
            print(f"Respuesta de orden enviada: {response}")
            if response and 'result' in response and 'orderId' in response['result']:
                return response['result'] # Retorna el ID de la orden y otros detalles
            return None
        except Exception as e:
            print(f"Excepción al enviar orden para {symbol} ({side} {qty}): {e}")
            return None

    def get_wallet_balance(self, coin="USDT"):
        """
        Obtiene el balance de la billetera para una moneda específica.
        coin: La moneda a consultar (ej. "USDT", "BTC")
        """
        try:
            response = self.session.get_wallet_balance(
                accountType="UNIFIED", # Tipo de cuenta (Unified Trading Account, SPOT, CONTRACT)
                coin=coin
            )
            if response and 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                # La respuesta puede contener balances de varias cuentas. Buscamos la de 'UNIFIED' y el 'coin' específico.
                for account in response['result']['list']:
                    for c in account['coin']:
                        if c['coin'] == coin:
                            return float(c['walletBalance'])
            return 0.0 # Retorna 0.0 si no se encuentra el balance o hay un error
        except Exception as e:
            print(f"Excepción al obtener balance para {coin}: {e}")
            return 0.0

    def get_current_position(self, symbol):
        """
        Obtiene el tamaño, el lado y el precio de entrada promedio de la posición actual para un símbolo dado.
        Retorna (tamaño, lado_de_la_posicion, avg_entry_price)
        lado_de_la_posicion puede ser "Buy", "Sell" o "None".
        avg_entry_price será float o None si no hay posición.
        """
        try:
            response = self.session.get_positions(category="linear", symbol=symbol)
            
            if response and response['retCode'] == 0 and 'list' in response['result']:
                positions = response['result']['list']
                
                if positions:
                    position = positions[0] 
                    size = float(position['size'])
                    side = position['side'].capitalize() 
                    avg_entry_price = float(position['avgPrice']) # <-- ¡Esta línea es la clave!
                    
                    if size > 0:
                        return size, side, avg_entry_price # <-- Ahora devuelve 3 valores
                    else:
                        return 0.0, "None", None # <-- Si no hay posición, avg_price es None
                else:
                    return 0.0, "None", None # <-- Si no hay posiciones, avg_price es None
            else:
                print(f"Error al obtener posiciones (Bybit API): {response}")
                return 0.0, "None", None # <-- Si hay error, avg_price es None
        except Exception as e:
            print(f"Excepción al obtener información de la posición para {symbol}: {e}")
            return 0.0, "None", None # <-- En caso de excepción, avg_price es None


    def close_position(self, symbol, current_position_side, qty):
        """
        Cierra una posición abierta.
        symbol: El par de trading
        current_position_side: El lado de la posición actualmente ABIERTA ("Buy" o "Sell").
                               Este es el valor que devuelve get_current_position.
        qty: El tamaño de la posición a cerrar.
        """
        # Para cerrar una posición, la orden debe ser del lado OPUESTO a la posición actual.
        # Si tienes un Buy (Long), para cerrarlo, colocas una orden Sell.
        # Si tienes un Sell (Short), para cerrarlo, colocas una orden Buy.
        
        close_order_side = None
        if current_position_side == "Buy": # Si la posición actual es LONG ("Buy")
            close_order_side = "Sell" # Necesitamos una orden de VENTA para cerrar
        elif current_position_side == "Sell": # Si la posición actual es SHORT ("Sell")
            close_order_side = "Buy" # Necesitamos una orden de COMPRA para cerrar
        else:
            print(f"Error: Lado de posición desconocido o no válido para cerrar: {current_position_side}")
            return None

        if close_order_side:
            print(f"Cerrando posición: Símbolo={symbol}, Lado de cierre={close_order_side}, Cantidad={qty}")
            return self.place_order(symbol, close_order_side, qty, order_type="Market")
        return None