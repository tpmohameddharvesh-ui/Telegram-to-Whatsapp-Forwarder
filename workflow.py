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

@app.route('/sim-test', methods=['GET', 'POST'])
def simulate_channel_message():
    import asyncio
    # Extract text from the URL parameter (defaults to a Volatility test)
    test_text = request.args.get('text', 'Volatility(25) BUY entry now!')
    
    print(f"[SIMULATOR] Triggering fake channel message: '{test_text}'")
    
    # Safely inject the text into your script's processing function
    # Note: Replace 'process_channel_message' with the actual name of the function 
    # in your script that handles the forwarding logic.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    # If your message handler function is async, we run it in the loop
    # You pass a dummy object or just the text string depending on how your code is written
    # For example, if your function just takes a string:
    # loop.run_until_complete(your_message_handler_function(test_text))
    
    return f"Simulation triggered for text: '{test_text}'", 200

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
    system_prompt = (
        "You are an automated financial router analyzing trading signal updates.\n"
        "Your sole task is to determine if the incoming text is a valid trade entry signal, "
        "a setup/layer target update, a Take Profit (TP)/Stop Loss (SL) update, or a position closing notification.\n\n"
        "CRITICAL RULE: If the text contains any trade updates, closing announcements (e.g., 'CLOSING PROFITS'), "
        "or entry execution instructions, output the ORIGINAL message text exactly as received without translating, "
        "changing, or adding any commentary.\n"
        "If it is a pure general chat message, unrelated advertisement, or marketing link, reply exactly with 'IGNORE'."
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
    """
    Inspects keywords dynamically to match natural signal phrasing.
    Removes tracking parameters when positions close out.
    """
    global ACTIVE_TRADES
    text_lower = msg_text.lower()
    
    # Identify standard trading pairs inside varied string formats
    detected_asset = None
    known_assets = ["gold", "xau", "usd", "eur", "gbp", "jpy", "btc", "eth", "us30", "nas100"]
    for asset in known_assets:
        if asset in text_lower:
            detected_asset = asset
            break

    if not detected_asset:
        detected_asset = "generic_asset"

    # Adapt tracking to match natural expressions like "closing profits", "close now", "hit sl"
    is_closing_signal = any(term in text_lower for term in ["closing", "closed", "profit booked", "hit tp", "hit sl", "close now", "irangulloo"])
    
    if is_closing_signal:
        if detected_asset in ACTIVE_TRADES:
            print(f"[-] Exit position captured for {detected_asset.upper()}. Purging tracking memory.")
            ACTIVE_TRADES.pop(detected_asset, None)
        else:
            print(f"[*] Close action processed for unindexed asset: {detected_asset.upper()}. Running clear routine.")
    else:
        # Register new or update existing open entries ("selling", "buying", "target", "layer")
        if any(term in text_lower for term in ["buying", "selling", "buy", "sell", "target", "layer", "entry"]):
            print(f"[+] Position action catalogued for asset reference: {detected_asset.upper()}")
            ACTIVE_TRADES[detected_asset] = {"status": "open", "updated_at": time.time()}

async def telegram_message_handler(event):
    """Handles single raw messages instantly upon creation"""
    msg_text = event.text or ""
    
    if not msg_text.strip() and event.message.media:
        msg_text = event.message.message or ""
        
    if not msg_text.strip():
        return

    print(f"\n[Telegram Incoming] Parsing message straight through workflow pipelines...")
    
    # Phase 1: Determine trade relevance using the AI
    verified_output = analyze_signal_via_ai(msg_text)
    
    if "IGNORE" in verified_output and len(verified_output) < 15:
        print("[-] Context did not match target financial conditions. Ignored.")
        return

    # Phase 2: Manage asset position states via state tracker
    track_and_clean_trades(verified_output)

    # Phase 3: Extract and prepare media attachments if present
    temp_file_path = None
    if event.message.media:
        print("[Media Handling] Fetching attached photo payload details from cloud server...")
        try:
            temp_file_path = await event.message.download_media(file="temp_signal_media")
        except Exception as e:
            print(f"[Media Download Fault]: {e}")

    # Phase 4: Forward everything directly to WhatsApp using Green API
    dispatch_to_whatsapp(verified_output, media_file_path=temp_file_path)

    # Housekeeping: Clear local storage assets safely
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
