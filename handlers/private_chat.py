import threading
import os
import time

class PrivateChatHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def handle(self, event, say, client):
        if event.get("channel_type") == "im" and not event.get("bot_id"):
            conv_id = event.get("channel")
            user_input = event.get("text", "")
            
            self.llm_service.comfy_image_tool.is_generating = False
            reply = self.llm_service.generate_reply(conv_id, user_input)
            
            if reply and reply.strip():
                # AI text remains in Blocks
                blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": reply}}]

                #  Links go 'attachment' to get the collapsible arrow
                attachments = []
                serper_links = self.llm_service.serper_web_search_tool.latest_links
                
                if serper_links:
                    links_text = "\n".join([f"• {link}" for link in serper_links])
                    attachments.append({
                        "color": "#36a64f",
                        "title": "🔗 Click to view Sources",
                        "text": links_text,
                        "fallback": "Web Search Sources",
                    })
                    self.llm_service.serper_web_search_tool.latest_links = []

                # Send both together with arrow if text is bigger
                say(blocks=blocks, attachments=attachments, text=reply, thread_ts=None)

                # Image Watcher
                if self.llm_service.comfy_image_tool.is_generating:
                    threading.Thread(
                        target=self._image_watcher_thread, 
                        args=(conv_id, client),
                        daemon=True
                    ).start()
            else:
                say(text="The AI returned an empty response.", thread_ts=None)

    def _image_watcher_thread(self, channel, client):
        path = self.llm_service.config.COMFYUI_IMAGE_PATH
        initial_files = set(os.listdir(path))
        
        for _ in range(90):
            time.sleep(3)
            current_files = set(os.listdir(path))
            new_files = current_files - initial_files
            
            if new_files:
                png_files = [os.path.join(path, f) for f in new_files if f.endswith('.png')]
                if png_files:
                    time.sleep(1)
                    latest_image = max(png_files, key=os.path.getctime)
                    
                    try:
                        client.files_upload_v2(
                            channel=channel,
                            file=latest_image,
                            title="AI Generated Image",
                            initial_comment="🎨 *Image ready:*"
                        )
                    except Exception as e:
                        print(f"Error uploading: {e}")
                    return