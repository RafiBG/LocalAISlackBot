from services.llm_service import LLMService
from services.slack_bot_service import SlackBotService
from config import Config
from threading import Timer
import uvicorn
import webbrowser


def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

def main() -> None:
    # Setup
    config = Config()
    llm_service = LLMService(config)
    
    # Open the browser after 1.5 seconds
    Timer(1.5, open_browser).start()

    # Start the FastAPI server
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )

if __name__ == "__main__":
    main()
