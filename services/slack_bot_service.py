from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from services.llm_service import LLMService
import time

class SlackBotService:
    def __init__(
        self,
        llm_service: LLMService,
        bot_token: str,
        app_token: str,
        allowed_channel_ids: set[str] | None,
    ) -> None:
        self.llm_service = llm_service
        self.allowed_channel_ids = allowed_channel_ids
        self.app_token = app_token
        self.app = App(token=bot_token)
        self.handler: SocketModeHandler | None = None
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.app.event("app_mention")
        def handle_mention(event, say):
            channel_id = event.get("channel")
            if self.allowed_channel_ids is not None and channel_id not in self.allowed_channel_ids:
                return
            user_text = event.get("text", "")
            reply = self.llm_service.generate_reply(user_text)
            say(reply)

        @self.app.event("message")
        def ignore_messages(event):
            pass

    def run_sync(self) -> None:
        """Starts the bot synchronously. This blocks the thread it is called in."""
        self.handler = SocketModeHandler(self.app, self.app_token)
        # .connect() starts the websocket WITHOUT trying to register OS signals
        self.handler.connect()
        
        while self.handler is not None:
            time.sleep(1)

    def stop(self) -> None:
        """Gracefully shuts down the connection."""
        if self.handler:
            self.handler.close()
            self.handler = None
