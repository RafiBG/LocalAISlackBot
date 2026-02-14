class PrivateChatHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def handle(self, event, say):
        # 1. Check conditions first
        if event.get("channel_type") == "im" and not event.get("bot_id"):
            conv_id = event.get("channel")
            user_input = event.get("text", "")
            
            # 2. Define reply inside the block
            reply = self.llm_service.generate_reply(conv_id, user_input)
            
            # 3. Move the check INSIDE this block
            if reply and reply.strip():
                serper_links = self.llm_service.serper_web_search_tool.latest_links
                blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": reply}}]

                if serper_links:
                    links_text = "\n".join([f"• <{link}>" for link in serper_links])
                    blocks.append({
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": f"*Sources:*\n{links_text}"}]
                    })
                    # Clear links after use
                    self.llm_service.serper_web_search_tool.latest_links = []

                say(blocks=blocks, text=reply)
            else:
                say(text="The AI returned an empty response. Check the logs.")