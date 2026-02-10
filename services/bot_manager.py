import threading
from services.slack_bot_service import SlackBotService
from colorama import Fore

class BotManager:
    def __init__(self, slack_bot: SlackBotService) -> None:
        self.slack_bot = slack_bot
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        # The bot is running if the handler exists and the thread is alive
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return 

        # Call run_sync inside this thread
        self._thread = threading.Thread(
            target=self.slack_bot.run_sync,
            daemon=True,
        )
        self._thread.start()
        print(f"\n===============\n{Fore.GREEN}Bot is online!{Fore.RESET}\n===============")

    def stop(self) -> None:
        if not self.is_running:
            return

        self.slack_bot.stop()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        print(f"\n===============\n{Fore.RED}Bot is offline!{Fore.RESET}\n===============")