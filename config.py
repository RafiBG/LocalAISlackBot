import os
from dotenv import load_dotenv


class Config:
    def __init__(self) -> None:
        load_dotenv()

        self.BOT_TOKEN = self._get_required("BOT_TOKEN")
        self.APP_TOKEN = self._get_required("APP_TOKEN")
        self.API_KEY = os.getenv("API_KEY", "")
        self.LOCAL_HOST = self._get_required("LOCAL_HOST")
        self.MODEL = self._get_required("MODEL")
        self.SYSTEM_MESSAGE = self._get_required("SYSTEM_MESSAGE")
        self.SHORT_MEMORY = int(os.getenv("SHORT_MEMORY", "10"))
        self.ALLOWED_GROUP_CHANNEL_IDS = self._parse_channel_ids(
            os.getenv("ALLOWED_GROUP_CHANNEL_IDS", "")
        )
        self.SERPER_API_KEY = self._get_required("SERPER_API_KEY")
        self.COMFYUI_API = self._get_required("COMFYUI_API")
        self.COMFYUI_IMAGE_PATH = self._get_required("COMFYUI_IMAGE_PATH")
        self.COMFYUI_IMAGE_WIDTH = self._get_required("COMFYUI_IMAGE_WIDTH")
        self.COMFYUI_IMAGE_HEIGHT = self._get_required("COMFYUI_IMAGE_HEIGHT")
        self.COMFYUI_STEPS = self._get_required("COMFYUI_STEPS")
        self.VISION_MODEL = self._get_required("VISION_MODEL")

    def _get_required(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Missing environment variable: {name}")
        return value

    def _parse_channel_ids(self, raw_value: str) -> set[str] | None:
        raw_value = raw_value.strip()
        if not raw_value:
            return None

        return {v.strip() for v in raw_value.split(",") if v.strip()}
