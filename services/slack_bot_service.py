from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from services.llm_service import LLMService
from services.chat_memory_service import ChatMemoryService
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
        self.memory = ChatMemoryService(max_history_size=max_memory)
        self.allowed_channel_ids = allowed_channel_ids
        self.app_token = app_token
        self.app = App(token=bot_token)
        self.handler: SocketModeHandler | None = None
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.app.event("app_mention")
        def handle_mention(event, say):
            channel_id = event.get("channel")
            user_id = event.get("user")
            
            if self.allowed_channel_ids is not None and channel_id not in self.allowed_channel_ids:
                return
            # Get username
            try:
                user_info = self.app.client.users_info(user=user_id)
                profile = user_info["user"]["profile"]
                
                # Try real_name, then display_name, then name, then fallback
                username = profile.get("real_name") or profile.get("display_name") or profile.get("name") or "User"
            except Exception as e:
                print(f"Error fetching user info: {e}")
                username = "User"

            # # Clean the text (remove bot mention)
            raw_text = event.get("text", "")
            user_text = raw_text.split(">")[-1].strip() # Get everything after the mention
            
            # Add "User [Name]:" so the AI sees who said what
            self.memory.add_message(user_id, "user", f"Context: I am talking to {username}. My message: {user_text}")
            
            # Get history
            messages = self.memory.get_history(user_id, self.llm_service.system_message)
            
            # DEBUG: See exactly what is sent to the AI
            #print(f"DEBUG: Sending to LLM: {messages}")
            
            # Generate reply
            reply = self.llm_service.generate_reply(messages)

            print(f"DEBUG: {username}: {user_text} ")
            print(f"DEBUG: AI: {reply} ")

            # Add assistant reply to memory
            self.memory.add_message(user_id, "assistant", reply)
            
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
