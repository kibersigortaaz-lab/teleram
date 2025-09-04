import asyncio
import threading
import uvicorn
from bot import TelegramBot
from web_app import app
from config import Config

config = Config.from_env()

def run_web_server():
    """Run the web server in a separate thread"""
    uvicorn.run(app, host=config.HOST, port=config.PORT)

async def run_bot():
    """Run the Telegram bot"""
    bot = TelegramBot()
    await bot.run()

async def main():
    """Main function to run both bot and web server"""
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Run the bot
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())
