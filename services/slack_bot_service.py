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
        max_memory: int = 10
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
            # Key for sharing memory in the same channel
            conv_id = event.get("channel")
            user_id = event.get("user")

            # Get User Identity
            try:
                info = self.app.client.users_info(user=user_id)
                username = info["user"]["profile"].get("real_name") or "User"
            except:
                username = "User"

            # Clean text
            raw_text = event.get("text", "")
            user_input = raw_text.split(">")[-1].strip()

            # Get reply from LCEL Service
            reply = self.llm_service.generate_reply(conv_id, f"{username}: {user_input}")

            #print(f"DEBUG:  {username}: {user_input}")
            #print(f"DEBUG:  AI: {reply}")

            say(reply)

        @self.app.event("message")
        def handle_message(event, say):
            # Only trigger for Direct Messages (DMs)
            if event.get("channel_type") == "im" and not event.get("bot_id"):
                conv_id = event.get("channel")
                user_input = event.get("text", "")
                
                reply = self.llm_service.generate_reply(conv_id, user_input)
                say(reply)


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
