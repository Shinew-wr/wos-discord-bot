import sys
import os
import asyncio
import warnings
import sqlite3 # 補齊：資料庫連接需要這個
from colorama import Fore, Style, init # 補齊：F, R, init 需要這個

# 假設這裡有 import discord 和 commands
# import discord
# from discord.ext import commands

# Colorama shortcuts
F = Fore
R = Style.RESET_ALL

warnings.filterwarnings("ignore", category=DeprecationWarning)

init(autoreset=True)

# ----------------------------------------------------------------------
# ⚠️ 假設這裡有 intents 的定義和 CustomBot 類別定義 ⚠️
# ----------------------------------------------------------------------
# Example: intents = discord.Intents.default()
# Example: intents.members = True
# Example: class CustomBot(commands.Bot): ...

# 這是 Bot 實例，必須在頂層，無縮排
bot = CustomBot(command_prefix="/", intents=intents)

# 為了讓 create_tables 存取到 connections 字典，我們在頂層聲明
databases = {}
connections = {}


def create_tables():
    # 創建表格的邏輯保持不變，但現在它依賴於全域 connections 字典
    global connections
    global databases

    with connections["conn_changes"] as conn_changes:
        conn_changes.execute("""CREATE TABLE IF NOT EXISTS nickname_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_nickname TEXT, 
            new_nickname TEXT, 
            change_date TEXT
         )""")
            
        conn_changes.execute("""CREATE TABLE IF NOT EXISTS furnace_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_furnace_lv INTEGER, 
            new_furnace_lv INTEGER, 
            change_date TEXT
        )""")

    with connections["conn_settings"] as conn_settings:
        conn_settings.execute("""CREATE TABLE IF NOT EXISTS botsettings (
            id INTEGER PRIMARY KEY, 
            channelid INTEGER, 
            giftcodestatus TEXT 
        )""")
            
        conn_settings.execute("""CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY, 
            is_initial INTEGER
        )""")

    with connections["conn_users"] as conn_users:
        conn_users.execute("""CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY, 
            nickname TEXT, 
            furnace_lv INTEGER DEFAULT 0, 
            kid INTEGER, 
            stove_lv_content TEXT, 
            alliance TEXT
        )""")

    with connections["conn_giftcode"] as conn_giftcode:
        conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
            giftcode TEXT PRIMARY KEY, 
            date TEXT
        )""")
            
        conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS user_giftcodes (
            fid INTEGER, 
            giftcode TEXT, 
            status TEXT, 
            PRIMARY KEY (fid, giftcode),
            FOREIGN KEY (giftcode) REFERENCES gift_codes (giftcode)
        )""")

    with connections["conn_alliance"] as conn_alliance:
        conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliancesettings (
            alliance_id INTEGER PRIMARY KEY, 
            channel_id INTEGER, 
            interval INTEGER
        )""")
            
        conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliance_list (
            alliance_id INTEGER PRIMARY KEY, 
            name TEXT
           )""")

    print(F.GREEN + "All tables checked." + R)


async def load_cogs():
    cogs = ["olddb", "control", "alliance", "alliance_member_operations", "bot_operations", "logsystem", "support_operations", "gift_operations", "changes", "w", "wel", "other_features", "bear_trap", "bear_trap_schedule", "id_channel", "backup_operations", "bear_trap_editor", "attendance", "attendance_report", "minister_schedule", "minister_menu", "minister_archive", "registration"]

    failed_cogs = []
        
    for cog in cogs:
        try:
            # 確保這裡的 load_extension 是 bot 的方法
            await bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            print(f"✗ Failed to load cog {cog}: {e}")
            failed_cogs.append(cog)
        
    if failed_cogs:
        print(F.RED + f"\n⚠️  {len(failed_cogs)} cog(s) failed to load:" + R)
        for cog in failed_cogs:
            print(F.YELLOW + f"   • {cog}" + R)
        print(F.YELLOW + "\nThe bot will continue with reduced functionality." + R)
        print(F.YELLOW + "Please check the log for the full error.\n" + R) # 刪除不必要的 --repair 訊息

# ----------------------------------------------------------------------
# FIX: on_ready 移到 load_cogs 函數外，作為一個獨立的事件
# ----------------------------------------------------------------------
@bot.event 
async def on_ready():
    try:
        print(f"{F.GREEN}Logged in as {F.CYAN}{bot.user}{R}")
        await bot.tree.sync()
    except Exception as e:
        print(f"Error syncing commands: {e}")


# ----------------------------------------------------------------------
# 核心啟動函數：所有執行邏輯都必須在這裡，確保 Gunicorn 導入時是乾淨的
# ----------------------------------------------------------------------
def run_bot_application():
    import os
    import sys
    import asyncio
    
    # 聲明全域變數
    global bot
    global databases
    global connections

    # --- 1. Token 獲取邏輯 (從頂層移入並修正錯誤訊息) ---
    token_file = "bot_token.txt"
    if not os.path.exists(token_file):
        bot_token = os.getenv("DISCORD_TOKEN")
        if not bot_token:
            print("FATAL: DISCORD_TOKEN environment variable not found.") # 修正錯誤訊息
            sys.exit(1)
        with open(token_file, "w") as f:
            f.write(bot_token)
    else:
        with open(token_file, "r") as f:
            bot_token = f.read().strip()
            
    # --- 2. 資料庫連接邏輯 (從頂層移入) ---
    if not os.path.exists("db"):
        os.makedirs("db")
        print(F.GREEN + "db folder created" + R)

    # ⚠️ 這裡對全域變數進行賦值/連接
    databases.update({
        "conn_alliance": "db/alliance.sqlite",
        "conn_giftcode": "db/giftcode.sqlite",
        "conn_changes": "db/changes.sqlite",
        "conn_users": "db/users.sqlite",
        "conn_settings": "db/settings.sqlite",
    })
    connections.update({name: sqlite3.connect(path) for name, path in databases.items()})

    print(F.GREEN + "Database connections have been successfully established." + R)

    # 呼叫 create_tables (從頂層移入)
    create_tables()

    # --- 3. 異步啟動邏輯 ---
    async def main_async():
        await load_cogs() 
        await bot.start(bot_token)

    asyncio.run(main_async())
# <--- 檔案在這裡結束 --->