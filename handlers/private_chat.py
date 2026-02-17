import threading
import os
import time
import requests
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

class PrivateChatHandler:
    def __init__(self, llm_service):
        self.llm_service = llm_service

    def handle(self, event, say, client):
        if event.get("bot_id"):
            return

        conv_id = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")
        raw_text = event.get("text", "")
        user_input = raw_text.strip()

        # Post placeholder
        initial_msg = client.chat_postMessage(
            channel=conv_id, 
            text="_Initializing..._",
            thread_ts=thread_ts 
        )
        msg_ts = initial_msg["ts"]

        # File Processing
        file_content = ""
        if "files" in event:
            client.chat_update(channel=conv_id, ts=msg_ts, text="_Reading files..._")
            file_content = self._process_files(event["files"], client)
            
            if file_content:
            # We use a very clear delimiter and a direct instruction
                user_input = (
                    "IMPORTANT: The user has uploaded a document. Use the following text to answer the question.\n"
                    "--- START OF DOCUMENT ---\n"
                    f"{file_content}\n"
                    "--- END OF DOCUMENT ---\n\n"
                    f"USER QUESTION: {user_input if user_input else 'Please summarize this document.'}"
            )
            else:
                # If extraction failed, we should know why
                print("DEBUG: File extraction resulted in no text.")

        # Get LLM Response
        client.chat_update(channel=conv_id, ts=msg_ts, text="_Thinking..._")
        self.llm_service.comfy_image_tool.is_generating = False

        try:
            # generate_reply should be your non-streaming method in LLMService
            final_text = self.llm_service.generate_reply(conv_id, user_input)
        except Exception as e:
            print(f"LLM Error: {e}")
            final_text = "Sorry, I had trouble processing that request."

        # Final Update
        client.chat_update(
            channel=conv_id, 
            ts=msg_ts, 
            text=final_text if final_text.strip() else "Done."
        )

        # Image Watcher
        if self.llm_service.comfy_image_tool.is_generating:
            threading.Thread(
                target=self._image_watcher_thread, 
                args=(conv_id, client, thread_ts),
                daemon=True
            ).start()

    def _image_watcher_thread(self, channel, client, thread_ts):
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
                            thread_ts=thread_ts,
                            file=latest_image,
                            title="AI Generated Image",
                            initial_comment="🎨 *Image ready:*"
                        )
                    except Exception as e:
                        print(f"Image upload failed: {e}")
                    return

    def _process_files(self, files, client):
        extracted_text = []
        token = client.token 
        for file_info in files:
            file_url = file_info.get("url_private_download")
            if not file_url: continue

            file_name = file_info.get('name')
            temp_path = f"temp_dm_{int(time.time())}_{file_name}"
            extension = os.path.splitext(file_name)[1].lower()

            try:
                resp = requests.get(file_url, headers={"Authorization": f"Bearer {token}"}, stream=True)
                if resp.status_code == 200:
                    with open(temp_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    time.sleep(0.5) 
                    if extension == ".pdf": loader = PyPDFLoader(temp_path)
                    elif extension in [".docx", ".doc"]: loader = Docx2txtLoader(temp_path)
                    elif extension in [".txt", ".md", ".py", ".json", ".csv"]:
                        loader = TextLoader(temp_path, encoding='utf-8')
                    else: continue

                    docs = loader.load()
                    content = "\n".join([d.page_content for d in docs])
                    extracted_text.append(f"--- FILE: {file_name} ---\n{content}")
            except Exception as e:
                print(f"Error processing {file_name} in DM: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)
        return "\n\n".join(extracted_text)
