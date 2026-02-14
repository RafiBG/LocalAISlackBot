class GroupChatHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def handle(self, event, say, client):
        # Ignore bots
        if event.get("bot_id") is not None:
            return
        
        conv_id = event.get("channel")
        user_id = event.get("user")

        try:
            info = client.users_info(user=user_id)
            username = info["user"]["profile"].get("real_name") or "User"
        except Exception:
            username = "User"

        raw_text = event.get("text", "")
        user_input = raw_text.split(">")[-1].strip()

        reply = self.llm_service.generate_reply(conv_id, f"{username}: {user_input}")

        if reply and reply.strip():
            serper_links = self.llm_service.serper_web_search_tool.latest_links
            
            blocks = [
                {
                    "type": "section", 
                    "text": {"type": "mrkdwn", "text": reply}
                }
            ]

            if serper_links:
                # Proper Slack link formatting: <URL|Display>
                links_text = "\n".join([f"• <{link}|{link}>" for link in serper_links])
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn", 
                            "text": f"🔗 *Web Sources:*\n{links_text}"
                        }
                    ]
                })
                # Clear links
                self.llm_service.serper_web_search_tool.latest_links = []

            say(blocks=blocks, text=reply)
        else:
            say(text="The AI returned an empty response. Check the logs.")