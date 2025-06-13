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
            # Si se usara una orden límite, aquí iría el precio
            # if order_type == "Limit" and price is not None:
            #     order_params["price"] = str(price)

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

    def get_position_info(self, symbol):
        """
        Obtiene información de la posición actual para un símbolo dado.
        symbol: El par de trading (ej. "BTCUSDT")
        """
        try:
            response = self.session.get_positions(
                category="linear", # Para futuros perpetuos (USD-M)
                symbol=symbol
            )
            if response and 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                # En futuros, normalmente solo hay una posición activa por símbolo (long o short)
                # Buscamos la primera posición con tamaño > 0
                for pos in response['result']['list']:
                    if float(pos['size']) > 0: 
                        return pos # Retorna el diccionario con los detalles de la posición
            return None # No hay posición activa para este símbolo
        except Exception as e:
            print(f"Excepción al obtener información de la posición para {symbol}: {e}")
            return None

    def close_position(self, symbol, side, qty):
        """
        Cierra una posición abierta.
        symbol: El par de trading
        side: El lado de la posición a CERRAR ("Buy" para cerrar un Short, "Sell" para cerrar un Long)
        qty: El tamaño de la posición a cerrar.
        """
        # Para cerrar una posición, la orden debe ser del lado OPUESTO a la posición actual.
        # Si tienes un Long (Buy), para cerrarlo, colocas una orden Sell.
        # Si tienes un Short (Sell), para cerrarlo, colocas una orden Buy.
        if side == "Long": # Si la posición actual es Long, cerramos con una orden Sell
            close_side = "Sell"
        elif side == "Short": # Si la posición actual es Short, cerramos con una orden Buy
            close_side = "Buy"
        else:
            print(f"Error: Lado de posición desconocido para cerrar: {side}")
            return None

        print(f"Cerrando posición: Símbolo={symbol}, Lado de cierre={close_side}, Cantidad={qty}")
        return self.place_order(symbol, close_side, qty, order_type="Market")