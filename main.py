import uvicorn
import webbrowser
import sys
from threading import Timer
from web.app import app  
from config import Config
from services.llm_service import LLMService
from services.slack_bot_service import SlackBotService
from services.bot_manager import BotManager

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

def main():
        config = Config()
        llm_service = LLMService(config)
        
        slack_bot = SlackBotService(
            llm_service=llm_service,
            bot_token=config.BOT_TOKEN,
            app_token=config.APP_TOKEN,
            allowed_channel_ids=config.ALLOWED_GROUP_CHANNEL_IDS
        )
        
        bot_manager = BotManager(slack_bot)

        app.state.bot_manager = bot_manager
        app.state.llm_service = llm_service

        Timer(2.0, open_browser).start()

        uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")

if __name__ == "__main__":
    main()