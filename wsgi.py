import threading
import asyncio
import os
import sys

# 1. 導入您的 Discord Bot 程式碼
# 這裡保留導入，讓 Gunicorn 知道 main 模組存在。
import main 

# 2. 從 keep_alive 載入 Flask 實例 (Health Check 伺服器)
from keep_alive import app as application

# 3. 定義 Bot 啟動邏輯
def start_bot_thread():
    # 修正：在函數內部再次導入 main 模組，以修復 NameError 
    # 這確保 main 變數在 try/except 作用域內都可用。
    import main 
    print("Starting Discord Bot in a background thread...")
    try:
        # 將 --no-update 參數加入系統參數列表，確保 Bot 不會嘗試自動更新
        if "--no-update" not in sys.argv:
            sys.argv.append("--no-update")
        
        # 修正：呼叫 main.py 中新的同步啟動函數
        # 這個函數內部已經包含了 asyncio.run()
        main.run_bot_application() 
        
    except Exception as e:
        # 如果 Bot 啟動失敗，強制退出 Worker，讓 Render 平台知道服務已停止
        print(f"FATAL: Discord Bot thread failed to start: {e}")
        os._exit(1)

# 4. 在 Gunicorn Worker 啟動時，啟動 Bot 執行緒
#    daemon=True 確保主執行緒結束時，這個執行緒也會被終止
bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
bot_thread.start()

print("Gunicorn WSGI: Health Check server (Flask) is ready and Bot is starting.")

# Gunicorn 將會服務這個 application 實例
