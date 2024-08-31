import os
import yfinance as yf
import ta
import pandas as pd
from datetime import datetime, timedelta
from telegram import Bot
from telegram.error import TimedOut, InvalidToken
import asyncio

# Verkrijg de Telegram token en chat ID van omgevingsvariabelen
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Verkrijg de token uit omgevingsvariabelen
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Verkrijg de chat ID uit omgevingsvariabelen

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN en TELEGRAM_CHAT_ID moeten worden ingesteld als omgevingsvariabelen.")

bot = Bot(token=TELEGRAM_TOKEN)

# Functie om data op te halen
def fetch_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if len(data) < 200:
            print(f"Not enough data for {ticker}. Skipping.")
            return pd.DataFrame()
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

# Functie om indicatoren te berekenen
def calculate_indicators(data):
    if data.empty or len(data) < 200:
        return {}

    results = {
        'SMA_200': ta.trend.SMAIndicator(data['Close'], window=200).sma_indicator(),
        'EMA_20': ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
    }
    return results

# Functie om de EMA boven SMA crossover te controleren in de laatste 30 dagen
def check_ema_sma_crossover_recent(data, days=30):
    if data.empty or len(data) < 200:
        return False

    indicators = calculate_indicators(data)
    sma_200 = indicators.get('SMA_200')
    ema_20 = indicators.get('EMA_20')

    if sma_200 is None or ema_20 is None:
        return False

    # Controleer of de EMA 20 boven de SMA 200 is in de laatste 'days' dagen
    for i in range(len(data) - days, len(data)):
        if ema_20.iloc[i-1] < sma_200.iloc[i-1] and ema_20.iloc[i] > sma_200.iloc[i]:
            return True
    
    return False

# Functie om alle crypto's te vinden met een EMA boven SMA crossover in de laatste 30 dagen
def find_crossovers_recent(cryptos, start_date, end_date):
    crossovers = []
    
    for crypto in cryptos:
        data = fetch_data(crypto, start_date, end_date)
        if check_ema_sma_crossover_recent(data):
            crossovers.append(crypto)
    
    return crossovers

# Asynchrone functie om een bericht naar Telegram te sturen met foutafhandeling
async def send_telegram_message(crossovers):
    crypto_list = "\n".join(crossovers)
    message = f"""\
Hi Han!

Hier is de update van cryptocurrencies waar de EMA 20 boven de SMA 200 is uitgekomen in de laatste 30 dagen:

{crypto_list}

Klik hier voor meer details en grafieken: https://cryptochart.streamlit.app/

Met vriendelijke groet,
CryptoChart"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            print("Bericht succesvol verzonden naar Telegram.")
            break
        except TimedOut:
            print(f"Verzoek time-out, poging {attempt + 1} van {max_retries}...")
            await asyncio.sleep(5)
        except InvalidToken:
            print("Ongeldige token, controleer je bot-token en probeer het opnieuw.")
            break
    else:
        print("Het verzenden van het bericht is mislukt na meerdere pogingen.")

# Hoofdfunctie om het script uit te voeren
async def main():
    default_cryptos = sorted(list(set([
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 'XRP-USD', 'DOT-USD', 'DOGE-USD', 'UNI-USD', 
        'LINK-USD', 'LTC-USD', 'BCH-USD', 'XLM-USD', 'VET-USD', 'FIL-USD', 'TRX-USD', 'AVAX-USD', 'MATIC-USD', 
        'ATOM-USD', 'FTT-USD', 'ALGO-USD', 'ICP-USD', 'AXS-USD', 'XTZ-USD', 'AAVE-USD', 'EGLD-USD', 'SAND-USD', 
        'MANA-USD', 'THETA-USD', 'FTM-USD', 'GRT-USD', 'NEAR-USD', 'KSM-USD', 'CAKE-USD', 'RUNE-USD', 'CELO-USD', 
        'HNT-USD', 'ONE-USD', 'BTT-USD', 'ENJ-USD', 'CHZ-USD', 'YFI-USD', 'SUSHI-USD', 'CRV-USD', 'ZIL-USD', 
        'DGB-USD', 'WAVES-USD', 'OMG-USD', 'QTUM-USD', 'ONT-USD', 'ZRX-USD', 'ICX-USD', 'HOT-USD', 'BNT-USD', 
        'ZEN-USD', 'RSR-USD', 'KAVA-USD', 'LRC-USD', 'SNX-USD', 'STMX-USD', 'SKL-USD', 'OCEAN-USD', 'ANKR-USD', 
        'CEL-USD', 'AR-USD', 'TWT-USD', 'REN-USD', '1INCH-USD', 'GALA-USD', 'PERP-USD', 'BAL-USD', 'COMP-USD', 
        'STORJ-USD', 'COTI-USD', 'RNDR-USD', 'IMX-USD', 'DENT-USD', 'BAND-USD', 'C98-USD', 'XYO-USD', 'MDX-USD', 
        'REQ-USD', 'HIVE-USD', 'SYS-USD', 'ALICE-USD', 'KLAY-USD', 'CVC-USD', 'CTSI-USD', 'RLC-USD', 'MKR-USD', 
        'SXP-USD', 'FET-USD', 'NKN-USD', 'STRAX-USD', 'LPT-USD', 'NMR-USD', 'DIA-USD', 'MTL-USD', 'XVG-USD', 
        'BTS-USD', 'WIN-USD', 'XVS-USD', 'PAXG-USD', 'MASK-USD', 'BADGER-USD', 'PHA-USD', 'POLY-USD', 'MLN-USD', 
        'SLP-USD', 'FORTH-USD', 'CTK-USD', 'LINA-USD', 'ANT-USD', 'DOCK-USD', 'NULS-USD', 'SUN-USD', 'TROY-USD', 
        'XED-USD', 'BOND-USD', 'DODO-USD', 'ROSE-USD', 'AUCTION-USD', 'MDT-USD', 'BUSD-USD', 'AKRO-USD', 'TRIBE-USD', 
        'CTXC-USD', 'FARM-USD', 'DF-USD', 'OM-USD', 'UBT-USD', 'PSG-USD', 'ATM-USD', 'PORTO-USD', 'CITY-USD', 
        'JUV-USD', 'OG-USD', 'ACM-USD', 'ASR-USD', 'BAR-USD', 'AFC-USD', 'INTER-USD', 'GAL-USD', 'SAUBER-USD', 
        'TPT-USD', 'REI-USD', 'ALPINE-USD', 'TLM-USD', 'ARDR-USD', 'OXT-USD', 'POWR-USD', 'GLM-USD', 'LIT-USD', 
        'AVA-USD', 'XNO-USD', 'VIDT-USD', 'DEXE-USD', 'POND-USD', 'UNFI-USD', 'UBX-USD', 'FIDA-USD', 'NBS-USD', 
        'SUPER-USD', 'RIF-USD', 'STPT-USD', 'WTC-USD', 'PNT-USD', 'BLZ-USD', 'MBOX-USD', 'IDEX-USD', 'JASMY-USD', 
        'TVK-USD', 'KP3R-USD', 'QNT-USD', 'DUSK-USD', 'CFG-USD', 'AKT-USD', 'LTO-USD', 'ARK-USD', 'TOMOE-USD', 
        'KEEP-USD', 'KNC-USD', 'MIR-USD', 'BIFI-USD', 'BMI-USD', 'DNT-USD', 'RGT-USD', 'RAY-USD', 'BOR-USD', 
        'ALPHA-USD', 'POLS-USD', 'MDA-USD', 'SWFTC-USD', 'KAI-USD', 'MFT-USD', 'MITH-USD', 'SOLO-USD', 'AMPL-USD', 
        'WNXM-USD', 'MHC-USD', 'AION-USD', 'CND-USD', 'XWC-USD', 'SOUL-USD', 'IOTX-USD', 'TOMO-USD', 'PEAK-USD', 
        'XEM-USD', 'WICC-USD'
    ])))

    start_date = pd.to_datetime("2020-01-01")
    end_date = pd.to_datetime(datetime.today())

    # Vind crypto's met EMA boven SMA crossover
    crossovers_recent = find_crossovers_recent(default_cryptos, start_date, end_date)

    if crossovers_recent:
        await send_telegram_message(crossovers_recent)
    else:
        print("Geen crypto's gevonden met een EMA 20 boven de SMA 200 in de laatste 30 dagen.")

# Voer de hoofdfunctie uit wanneer het script wordt gestart
if __name__ == "__main__":
    asyncio.run(main())
