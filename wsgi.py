import threading
import asyncio
import os
import sys

import main 

from keep_alive import app as application

def start_bot_thread():
    print("Starting Discord Bot in a background thread...")
    try:
        if "--no-update" not in sys.argv:
            sys.argv.append("--no-update")
        
        main.run_bot_application()
        
    except Exception as e:
        print(f"FATAL: Discord Bot thread failed to start: {e}")
        os._exit(1)

# 4. 在 Gunicorn Worker 啟動時，啟動 Bot 執行緒
#    daemon=True 確保主執行緒結束時，這個執行緒也會被終止
bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
bot_thread.start()

print("Gunicorn WSGI: Health Check server (Flask) is ready and Bot is starting.")

# Gunicorn 將會服務這個 application 實例
