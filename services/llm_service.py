from config import Config
from openai import OpenAI


class LLMService:
    def __init__(self, config: Config) -> None:
        self.client = OpenAI(
            api_key= config.API_KEY,
            base_url= config.LOCAL_HOST,
        )
        self.model = config.MODEL
        self.system_message = config.SYSTEM_MESSAGE

    def generate_reply(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model = self.model,
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
            temperature = 0.7,
        )

        return response.choices[0].message.content.strip()