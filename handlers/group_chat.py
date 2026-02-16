import threading
import os
import time

class GroupChatHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def handle(self, event, say, client):
        # Ignore messages from bots
        if event.get("bot_id") is not None:
            return
        
        conv_id = event.get("channel")
        user_id = event.get("user")

        # Get username or real name
        try:
            info = client.users_info(user=user_id)
            username = info["user"]["profile"].get("real_name") or "User"
        except Exception:
            username = "User"

        # Clean the input text (removing the bot mention)
        raw_text = event.get("text", "")
        user_input = raw_text.split(">")[-1].strip()

        self.llm_service.comfy_image_tool.is_generating = False

        reply = self.llm_service.generate_reply(conv_id, f"{username}: {user_input}")

        if reply and reply.strip():
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": reply}}]

            # Set up Attachments (Collapsible Sources)
            attachments = []
            serper_links = self.llm_service.serper_web_search_tool.latest_links
            
            if serper_links:
                # List format for clickable links
                links_text = "\n".join([f"• {link}" for link in serper_links])
                attachments.append({
                    "color": "#36a64f",
                    "title": "🔗 Click to view Sources",
                    "text": links_text,
                    "fallback": "Web Search Sources",
                })
                # Clear links list
                self.llm_service.serper_web_search_tool.latest_links = []

            say(blocks=blocks, attachments=attachments, text=reply, thread_ts=None)

            # Start background watcher if image is generating
            if self.llm_service.comfy_image_tool.is_generating:
                threading.Thread(
                    target=self._image_watcher_thread, 
                    args=(conv_id, client),
                    daemon=True
                ).start()
        else:
            say(text="The AI returned an empty response. Check the logs.", thread_ts=None)

    def _image_watcher_thread(self, channel, client):
        """Monitors folder for new images and uploads them as a standalone message in the group."""
        path = self.llm_service.config.COMFYUI_IMAGE_PATH
        initial_files = set(os.listdir(path))
        
        # Poll for up to 4.5 minutes
        for _ in range(90):
            time.sleep(3)
            current_files = set(os.listdir(path))
            new_files = current_files - initial_files
            
            if new_files:
                png_files = [os.path.join(path, f) for f in new_files if f.endswith('.png')]
                if png_files:
                    time.sleep(1) # Buffer for saving
                    latest_image = max(png_files, key=os.path.getctime)
                    
                    try:
                        client.files_upload_v2(
                            channel=channel,
                            file=latest_image,
                            title="AI Generated Image",
                            initial_comment="🎨 *Image ready for the group:*"
                        )
                    except Exception as e:
                        print(f"Group upload failed: {e}")
                    return