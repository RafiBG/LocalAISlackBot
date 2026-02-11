from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from config import Config
from services.llm_service import LLMService
from services.slack_bot_service import SlackBotService
from services.bot_manager import BotManager
from services.env_service import EnvService

app = FastAPI()
env_service = EnvService()

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

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    env_data = env_service.read()

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "bot_token": env_data.get("BOT_TOKEN", ""),
            "app_token": env_data.get("APP_TOKEN", ""),
            "api_key": env_data.get("API_KEY", ""),
            "local_host": env_data.get("LOCAL_HOST", ""),
            "allowed_channels": env_data.get("ALLOWED_GROUP_CHANNEL_IDS", ""),
            "model": env_data.get("MODEL", ""),
            "system_message": env_data.get("SYSTEM_MESSAGE", "").replace("\\n", "\n"),
        },
    )


@app.post("/config")
async def save_config(
    bot_token: str = Form(...),
    app_token: str = Form(...),
    api_key: str = Form(...),
    local_host: str = Form(...),
    allowed_channels: str = Form(""),
    model: str = Form(...),
    system_message: str = Form(...),
):
    updates = {
        "BOT_TOKEN": bot_token,
        "APP_TOKEN": app_token,
        "API_KEY": api_key,
        "LOCAL_HOST": local_host,
        "ALLOWED_GROUP_CHANNEL_IDS": allowed_channels,
        "MODEL": model,
        "SYSTEM_MESSAGE": system_message.replace("\n", "\\n"),
    }

    env_service.write_selected(updates)

    return RedirectResponse("/config", status_code=303)
