from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from config import Config
from services.llm_service import LLMService
from services.slack_bot_service import SlackBotService
from services.bot_manager import BotManager

app = FastAPI()

app.mount("/static", StaticFiles(directory="web/static"), name="static")

templates = Jinja2Templates(directory="web/templates")

config = Config()
llm_service = LLMService(config)

slack_bot = SlackBotService(
    llm_service=llm_service,
    bot_token=config.BOT_TOKEN,
    app_token=config.APP_TOKEN,
    allowed_channel_ids=config.ALLOWED_GROUP_CHANNEL_IDS,
)

bot_manager = BotManager(slack_bot)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "status_text": "online" if bot_manager.is_running else "offline",
            "status_class": "online" if bot_manager.is_running else "offline",
            "button_text": "Stop bot" if bot_manager.is_running else "Start bot",
        },
    )


@app.post("/toggle_ajax")
def toggle_ajax():
    if bot_manager.is_running:
        bot_manager.stop()
    else:
        bot_manager.start()

    status_text = "online" if bot_manager.is_running else "offline"
    status_class = "online" if bot_manager.is_running else "offline"
    button_text = "Stop bot" if bot_manager.is_running else "Start bot"

    return JSONResponse(
        content={
            "status_text": status_text,
            "status_class": status_class,
            "button_text": button_text
        }
    )
