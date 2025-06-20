# 🤖 Bot de Trading con Medias Móviles para Bybit (Python)

Este es un bot de trading automatizado desarrollado en Python que opera en la plataforma Bybit capaz de usar distintos tipos de estrategias.

## 🚀 Características Principales

* **Integración con Bybit:** Se conecta a la API unificada de Bybit para obtener datos de mercado (velas), gestionar posiciones y ejecutar órdenes de compra/venta/cierre.
* **Registro Detallado (Logging):** Registra cada operación (apertura, cierre) en un archivo CSV fácil de leer. Se genera un nuevo archivo de log por cada sesión del bot, organizado en una carpeta `data/`.
* **Gestión de Posiciones:** Monitorea tu posición actual en Bybit y ajusta las operaciones (abrir Long/Short, cerrar y revertir) según la señal de la estrategia.
* **Configuración Flexible:** Todos los parámetros clave (símbolo, temporalidad, cantidad de trading, periodos SMA, modo Testnet) son fácilmente configurables en un archivo `config.py`.
* **Manejo de Errores:** Incluye un manejo básico de excepciones para reintentar operaciones y evitar fallos críticos.

## ⚙️ Requisitos

Antes de ejecutar el bot, asegúrate de tener lo siguiente:

* **Python 3.x** instalado.
* **Cuenta en Bybit:** Puedes usar una cuenta de Testnet para pruebas (recomendado inicialmente) o una cuenta real.
* **API Keys de Bybit:** Genera tus API keys en la configuración de tu cuenta de Bybit con los permisos necesarios (Lectura de mercado, Órdenes, Posiciones, Balance). **¡Guárdalas de forma segura y NO las compartas!**

## 📦 Instalación

1.  **Clona este repositorio (o descarga los archivos):**
    ```bash
    git clone [https://github.com/tu-usuario/tu-repositorio-del-bot.git](https://github.com/tu-usuario/tu-repositorio-del-bot.git)
    cd tu-repositorio-del-bot
    ```
    (Si no usas Git, simplemente descarga el proyecto como un ZIP y extráelo).

2.  **Instala las dependencias de Python:**
    ```bash
    pip install -r requirements.txt
    ```
    (Si no tienes un `requirements.txt`, puedes crearlo con `pip freeze > requirements.txt` después de instalar las librerías, o instalarlas manualmente: `pip install pybit-unified-trading pandas`)

3.  **Estructura de Archivos:** Asegúrate de que tus archivos estén organizados de la siguiente manera:

    ```
    tu_bot_trading/
    ├── main.py
    ├── config.py
    ├── requirements.txt (opcional, pero recomendado)
    ├── services/
    │   ├── __init__.py
    │   ├── bybit_client.py
    │   └── trade_logger.py
    └── strategies/
        ├── __init__.py
        └── simple_ma_strategy.py
    ```

## 🛠️ Configuración

Para configurar el bot, necesitarás establecer variables de entorno y ajustar el archivo `config.py`.

### 1. Configurar Variables de Entorno (¡CRÍTICO para la seguridad!)

Por motivos de seguridad, tus API Keys de Bybit **NO deben estar directamente en el código**. Debes configurarlas como variables de entorno en tu sistema operativo.

* **`BYBIT_API_KEY`**: Tu clave API de Bybit.
* **`BYBIT_API_SECRET`**: Tu clave secreta API de Bybit.

**Cómo configurarlas (ejemplos):**

* **En Linux/macOS (para la sesión actual de terminal):**
    ```bash
    export BYBIT_API_KEY="tu_clave_api_aqui"
    export BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```
    (Para hacerlas persistentes después de cerrar la terminal, añádelas a tu archivo de configuración de shell como `.bashrc`, `.zshrc` o `.profile`.)

* **En Windows (CMD - para la sesión actual):**
    ```cmd
    set BYBIT_API_KEY="tu_clave_api_aqui"
    set BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```

* **En Windows (PowerShell - para la sesión actual):**
    ```powershell
    $env:BYBIT_API_KEY="tu_clave_api_aqui"
    $env:BYBIT_API_SECRET="tu_secreto_api_aqui"
    ```
    (Para hacerlas persistentes, puedes buscarlas en las "Propiedades del Sistema" -> "Variables de entorno" y agregarlas de forma permanente, o usar métodos de PowerShell para setearlas en tu perfil de usuario).

**¡IMPORTANTE!** Después de configurar las variables de entorno, es posible que necesites **reiniciar tu terminal** o el IDE desde donde ejecutas el bot para que los cambios surtan efecto.

### 2. Ajustar `config.py`

Abre el archivo `config.py` y ajusta los siguientes parámetros. **Las API Keys serán cargadas automáticamente desde las variables de entorno, por lo que NO las pondrás directamente aquí.**

* **`TESTNET`**: Establece `True` para operar en la red de prueba (¡ALTAMENTE RECOMENDADO para probar!) o `False` para operar con dinero real.
* **`SYMBOL`**: El par de trading que deseas operar (ej. `"BTCUSDT"`, `"ETHUSDT"`).
* **`INTERVAL`**: La temporalidad de las velas que usará la estrategia (ej. `"1"` para 1 minuto, `"5"` para 5 minutos, `"60"` para 1 hora). Ten en cuenta que la API de Bybit generalmente no soporta intervalos menores a 1 minuto.
* **`TRADE_QUANTITY`**: La cantidad de la moneda base a operar en cada transacción (ej. `0.001` para BTC).
* **`CHECK_INTERVAL_SECONDS`**: El tiempo en segundos que el bot esperará entre cada ciclo de verificación y ejecución. Esto es independiente del `INTERVAL` de las velas.
* **`SMA_SHORT_PERIOD` y `SMA_LONG_PERIOD`**: Los periodos para el cálculo de las medias móviles simples.

**Ejemplo de `config.py` (ahora sin las claves API directamente):**

```python
# config.py

# --- Configuración del Bot ---
TESTNET = True
SYMBOL = "BTCUSDT"
INTERVAL = "1"
TRADE_QUANTITY = 0.001
CHECK_INTERVAL_SECONDS = 60

# --- Configuración de la Estrategia Simple MA ---
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
