from slack_bolt import App

class SlashClearMemoryHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def register_commands(self, app: App):
        # Clear user memory (works in private and group chats)
        @app.command("/clear_memory")
        def clear_user_memory_command(ack, body, client):
            ack()
            self._clear_user_memory(body, client)

    # Internal Methods
    def _clear_user_memory(self, body, client):
        channel_id = body["channel_id"]
        user_id = body["user_id"]

        if channel_id in self.llm_service.history_db:
            # Keep system messages and remove user messages in this channel
            self.llm_service.history_db[channel_id] = [
                msg for msg in self.llm_service.history_db[channel_id]
                if msg.__class__.__name__ == "SystemMessage"
                or (msg.__class__.__name__ != "HumanMessage" or getattr(msg, "user_id", None) != user_id)
            ]

        client.chat_postMessage(
            channel=channel_id,
            text=f"<@{user_id}>, your AI memory for this chat has been cleared! ✅"
        )