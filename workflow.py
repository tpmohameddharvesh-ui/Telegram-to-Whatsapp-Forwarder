import asyncio
import os
import sys
import time
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram-to-WhatsApp Trading Bridge Core (Green API) is active!", 200

# =======================================================
#               SIMULATOR & TEST WEBHOOK
# =======================================================

@app.route('/sim-test', methods=['GET', 'POST'])
def simulate_channel_message():
    from flask import request
    import asyncio
    
    # Extract text from the URL parameter
    test_text = request.args.get('text', 'Volatility(25) BUY entry now!')
    print(f"\n[SIMULATOR] Manual testing injection triggered: '{test_text}'")
    
    # Create a mock Telegram event object structure so your real handler can read it
    class MockEvent:
        def __init__(self, text):
            self.text = text
            self.message = self
            self.media = None
    
    mock_event = MockEvent(test_text)
    
    # Safely dispatch it into your existing async pipeline logic
    try:
        # We fetch or create an event loop to handle the async call safely inside Flask
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        print("[SIMULATOR] Routing mock event into live parsing pipeline...")
        loop.run_until_complete(telegram_message_handler(mock_event))
        return f"Successfully processed mock trade simulation for text: '{test_text}'", 200
    except Exception as e:
        print(f"[SIMULATOR Error]: Failed to run simulation injection: {e}")
        return f"Simulation route hit, but processing error occurred: {e}", 500

# =======================================================
#               1. LIVE SYSTEM CONFIGURATION
# =======================================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RENDER_APP_URL = os.environ.get("RENDER_APP_URL")

TG_SOURCE_CHANNEL = int(os.environ.get("TELEGRAM_SOURCE_CHANNEL", 0))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# Green API Credentials
GREEN_API_ID = os.environ.get("GREEN_API_ID_INSTANCE")       # Your Green API Instance ID
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN")            # Your Green API Instance Token
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID")        # Format: 1234567890@g.us

TG_API_ID = int(os.environ.get("TG_API_ID", 0))
TG_API_HASH = os.environ.get("TG_API_HASH")
TG_STRING = os.environ.get("TELEGRAM_STRING_SESSION", "")

# In-memory database tracking state of active trades
ACTIVE_TRADES = {}

# =======================================================
#               2. TELEGRAM & AI PROCESSING CORE
# =======================================================

def analyze_signal_via_ai(text_content):
    """
    Asks Llama to parse the trade status. 
    Returns original message text if relevant; otherwise returns 'IGNORE'.
    """
def analyze_signal_via_ai(text_content):
    """
    Asks Llama to parse the trade status. 
    Returns original message text if relevant; otherwise returns 'IGNORE'.
    """
def analyze_signal_via_ai(text_content):
    """
    Asks Llama to parse the trade status using a multi-variant few-shot Malayalam/English dataset.
    """
    system_prompt = (
        "You are an expert financial signal routing filter analyzing mixed-language trading streams.\n"
        "The channel blends traditional trading terms (BUY, SELL, SL, TP, Target) with conversational Malayalam "
        "slang directives, technical observations, and emotional expressions.\n\n"
        
        "CRITICAL COMPLIANCE RULES:\n"
        "1. If the input contains live trade entries, market execution orders, specific pricing predictions, "
        "layering instructions ('layer pidicho', 'gap itt layer'), risk updates ('over risk edukkalletto'), status changes, "
        "or exit calls ('CLOSING PROFITS', 'CLOSING LOSSES'), you MUST return the ORIGINAL text EXACTLY as received. "
        "Do not strip newlines, do not translate, and do not add comments.\n"
        "2. If the text is an advertisement for a premium course, student testimonials/reviews, casual general greetings "
        "(e.g., 'Good morning team'), or promotional enrollment codes, reply with exactly the single word 'IGNORE'.\n\n"
        
        "--- LIVE SIGNAL REFERENCE DATASET (VALID SCENARIOS) ---\n\n"
        
        "Example 1 (Multi-Stage Execution & Risk Warnings):\n"
        "Input: IAM SELLING GOLD (XAUUSD) Now or while pushing upside.\nTarget around $4040\nOver risk edukkalletto oru reversal vannitte irangulloo. High kittumbol layer\nCLOSING GOLD PROFITS🤑🤑\n"
        "Output: IAM SELLING GOLD (XAUUSD) Now or while pushing upside.\nTarget around $4040\nOver risk edukkalletto oru reversal vannitte irangulloo. High kittumbol layer\nCLOSING GOLD PROFITS🤑🤑\n\n"
        
        "Example 2 (Synthetic Volatility Multi-line Slang):\n"
        "Input: IAM SELLING Volatility25(1s) now or while pushing upside..\nGap itt layer cheytho.\nSL 3000/4000 points\nCheriya time frame gap kittumbol aggressive SELL SIDE scalping.\n"
        "Output: IAM SELLING Volatility25(1s) now or while pushing upside..\nGap itt layer cheytho.\nSL 3000/4000 points\nCheriya time frame gap kittumbol aggressive SELL SIDE scalping.\n\n"
        
        "Example 3 (Volume Alerts & Quick Exit Changes):\n"
        "Input: IAM BUYING GOLD NOW.\nTarget $4132\nClose it on small profits there is no buyers volume\n"
        "Output: IAM BUYING GOLD NOW.\nTarget $4132\nClose it on small profits there is no buyers volume\n\n"
        
        "Example 4 (Market Projections & Local Celebration Slang):\n"
        "Input: GOLD IS GOING TO EXPLODE SOON UNTIL $4165\nAdich minneda\nMASHALLAH 🥰\nENJOY THE FREE MONEY 💰\nAkoshikki\n"
        "Output: GOLD IS GOING TO EXPLODE SOON UNTIL $4165\nAdich minneda\nMASHALLAH 🥰\nENJOY THE FREE MONEY 💰\nAkoshikki\n\n"
        
        "Example 5 (High Volatility Event & News Warnings):\n"
        "Input: Always get ready for NFP NEWS TRADE…\nIf you can’t take risk then don’t trade on news\nKuttikal noki irikki ♦️♦️♦️♦️\nIAM BUYING GOLD (XAUUSD) NOW\nMASHALLAH NFP ON FIRE 🔥\n"
        "Output: Always get ready for NFP NEWS TRADE…\nIf you can’t take risk then don’t trade on news\nKuttikal noki irikki ♦️♦️♦️♦️\nIAM BUYING GOLD (XAUUSD) NOW\nMASHALLAH NFP ON FIRE 🔥\n\n"
        
        "Example 6 (Index Management & Operational Humor):\n"
        "Input: IAM SELLING USTECH100 NOW OR WHILE PUSHING UPSIDE…\nMore SELLS ON THE RALLIES…\nUSTECH100 Njanippol thazhek varuthi tharaam Athyavashyam profitayal close okey.\n15 minutes candle njanaan undakkunnath\nCLOSING LOSSES\n"
        "Output: IAM SELLING USTECH100 NOW OR WHILE PUSHING UPSIDE…\nMore SELLS ON THE RALLIES…\nUSTECH100 Njanippol thazhek varuthi tharaam Athyavashyam profitayal close okey.\n15 minutes candle njanaan undakkunnath\nCLOSING LOSSES\n\n"
        
        "--- LIVE REFERENCE DATASET (NOISE / SPAM TO IGNORE) ---\n\n"
        
        "Example 7 (Standard Chat Greeting):\n"
        "Input: Good morning everyone! Let's watch the charts closely today and maintain risk management strategies.\n"
        "Output: IGNORE\n\n"
        
        "Example 8 (Mentorship Course Advertisement):\n"
        "Input: Admissions are now open for our Advanced Trading Course! Join today using discount code VIP50 to learn private market strategies.\n"
        "Output: IGNORE\n\n"
        
        "Evaluate the user input strictly according to these explicit structural alignments. Output ONLY the original string or 'IGNORE'."
    )

    try:
        openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free", 
            "messages": [
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": text_content}
            ],
            "temperature": 0.1
        }

        response = requests.post(openrouter_url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[AI Engine Error]: {e}")
    
    return "IGNORE"

    try:
        openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free", 
            "messages": [
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": text_content}
            ],
            "temperature": 0.1
        }

        response = requests.post(openrouter_url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[AI Engine Error]: {e}")
    
    return "IGNORE"

    

def dispatch_to_whatsapp(message_text, media_file_path=None):
    """Sends raw text or image captures straight out to Green API endpoints"""
    if not GREEN_API_ID or not GREEN_API_TOKEN:
        print("[!] Green API Configuration missing.")
        return

    base_url = f"https://api.green-api.com/waInstance{GREEN_API_ID}"
    
    try:
        if media_file_path and os.path.exists(media_file_path):
            # Green API Image upload deployment endpoint
            url = f"{base_url}/sendFileByUpload/{GREEN_API_TOKEN}"
            payload = {
                "chatId": WHATSAPP_GROUP_ID,
                "caption": message_text
            }
            with open(media_file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(url, data=payload, files=files, timeout=30)
        else:
            # Traditional text message payload formatting
            url = f"{base_url}/sendMessage/{GREEN_API_TOKEN}"
            payload = {
                "chatId": WHATSAPP_GROUP_ID,
                "message": message_text
            }
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            
        if response.status_code == 200:
            print("[+] Relay Update Dropped inside Green API Channel successfully.")
        else:
            print(f"[!] Green API Rejected Dispatch Payload: {response.text}")
    except Exception as e:
        print(f"[Green API Relay Engine Crash]: {e}")

def track_and_clean_trades(msg_text):
    global ACTIVE_TRADES
    text_lower = msg_text.lower()
    
    detected_asset = None
    # ADDED: "volatility", "v25", "v75", "v100" to allow synthetic indices to match cleanly
    known_assets = ["gold", "xau", "usd", "eur", "gbp", "jpy", "btc", "eth", "us30", "nas100", "volatility", "v25", "v75", "v100"]
    for asset in known_assets:
        if asset in text_lower:
            detected_asset = asset
            break

    if not detected_asset:
        detected_asset = "generic_asset"

    is_closing_signal = any(term in text_lower for term in ["closing", "closed", "profit booked", "hit tp", "hit sl", "close now", "irangulloo"])
    
    if is_closing_signal:
        if detected_asset in ACTIVE_TRADES:
            print(f"[-] Exit position captured for {detected_asset.upper()}. Purging tracking memory.")
            ACTIVE_TRADES.pop(detected_asset, None)
        else:
            print(f"[*] Close action processed for unindexed asset: {detected_asset.upper()}. Running clear routine.")
    else:
        # Register new positions or tracking metrics
        if any(term in text_lower for term in ["buying", "selling", "buy", "sell", "target", "layer", "entry", "now"]):
            print(f"[+] Position action catalogued for asset reference: {detected_asset.upper()}")
            ACTIVE_TRADES[detected_asset] = {"status": "open", "updated_at": time.time()}

async def telegram_message_handler(event):
    """Handles single raw messages instantly by letting the trained AI do the heavy lifting"""
    msg_text = event.text or ""
    
    if not msg_text.strip() and event.message.media:
        msg_text = event.message.message or ""
        
    if not msg_text.strip():
        return

    print(f"\n[Telegram Incoming] Parsing message straight through workflow pipelines...")
    
    # Run the message through the newly trained AI model
    verified_output = analyze_signal_via_ai(msg_text)
    
    if "IGNORE" in verified_output and len(verified_output) < 15:
        print("[-] Context categorized as noise/general chat. Ignored.")
        return

    print("[+] Valid signal confirmed by AI. Proceeding to forward...")
    
    # Manage asset position states via state tracker
    track_and_clean_trades(verified_output)

    # Extract and prepare media attachments if present
    temp_file_path = None
    if event.message.media:
        try:
            temp_file_path = await event.message.download_media(file="temp_signal_media")
        except Exception as e:
            print(f"[Media Download Fault]: {e}")

    # Forward directly to WhatsApp
    dispatch_to_whatsapp(verified_output, media_file_path=temp_file_path)

    if temp_file_path and os.path.exists(temp_file_path):
        os.remove(temp_file_path)

def run_telegram_loop():
    """Sets up an isolated event loop for Telethon networking"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    print("[Telegram Core] Connecting Userbot loop pipeline...")
    tg_user_client = TelegramClient(StringSession(TG_STRING), TG_API_ID, TG_API_HASH, loop=loop)
    tg_user_client.add_event_handler(telegram_message_handler, events.NewMessage(chats=TG_SOURCE_CHANNEL))
    
    async def main_telegram_runner():
        await tg_user_client.start()
        print("[Telegram Core] Userbot loop running. Listening to channel stream...")
        await tg_user_client.run_until_disconnected()

    loop.run_until_complete(main_telegram_runner())

# =======================================================
#               3. RUNTIME COORDINATION
# =======================================================

def keep_alive_ping():
    """Keeps the host platform active via web container self-pings"""
    time.sleep(20)
    print("[Keep-Alive Web Thread] Active scheduler monitoring up.")
    while True:
        try:
            if RENDER_APP_URL:
                requests.get(RENDER_APP_URL, timeout=10)
                print("[Keep-Alive] Self-pinged active web endpoint.")
        except Exception:
            pass
        time.sleep(300)

if __name__ == '__main__':
    print("[*] Booting Unified System Userbot Engine...")
    
    # 1. Fire up background utility services
    threading.Thread(target=keep_alive_ping, daemon=True).start()
    
    # 2. Fire up the Telegram Worker thread
    threading.Thread(target=run_telegram_loop, daemon=True).start()
    
    # 3. Launch Flask server on the main execution thread 
    print("[System Uplink] All operations routed. Booting Flask server container network...")
    app.run(host='0.0.0.0', port=10000)
