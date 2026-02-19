from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain.agents import create_tool_calling_agent, AgentExecutor
# Import tool 
from tools.time_tool import get_current_date, get_current_time
from tools.serper_web_search import SerperSearchTool
from tools.comfy_tool import ComfyUIImageTool
from config import Config

class LLMService:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.llm_params = {
            "openai_api_key": config.API_KEY,
            "base_url": config.LOCAL_HOST,
            "model_name": config.MODEL,
            "temperature": 0.7
        }

        # Optional separate vision model
        self.vision_llm = ChatOpenAI(
            openai_api_key=config.API_KEY,
            base_url=config.LOCAL_HOST,
            model_name=config.VISION_MODEL,
            temperature=0.2
        )
        
        # Memory
        self.history_db = {} 

        self.serper_web_search_tool = SerperSearchTool(config.SERPER_API_KEY)
        self.comfy_image_tool = ComfyUIImageTool(config)
        # Tools available to the AI
        self.tools = [
            get_current_date,
            get_current_time,
            self.serper_web_search_tool.get_web_tool(),
            self.comfy_image_tool.get_tool(),
            ]

    def generate_reply(self, conversation_id: str, prompt: str, images=None) -> str:

        if conversation_id not in self.history_db:
            self.history_db[conversation_id] = []

        # If images exist, describe them first
        if images:
            image_description = self._describe_images(images, prompt)
            prompt = (
                "The user uploaded image(s).\n"
                "Here is a detailed description of the image(s):\n"
                f"{image_description}\n\n"
                f"User question: {prompt}"
            )
            response = self._run_agent(conversation_id, prompt, images_present=True)
        else:
            response = self._run_agent(conversation_id, prompt, images_present=False)

        # Run tool agent normally (text only)
        response = self._run_agent(conversation_id, prompt)

        return response

    # VISION STEP
    def _describe_images(self, images, user_prompt):

        content = [{
            "type": "text",
            "text": f"Describe this image in detail. Focus on objects, text, numbers, structure, and context. The user asked: {user_prompt}"
        }]

        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img['base64']}"
                }
            })

        vision_response = self.vision_llm.invoke([
            ("system", "You are a precise visual analysis assistant."),
            HumanMessage(content=content)
        ])

        return vision_response.content

    # AGENT STEP
    def _run_agent(self, conversation_id, prompt, images_present = False):

        llm = ChatOpenAI(**self.llm_params)

        # Dynamically select tools
        if images_present:
            tools = [
                get_current_date,
                get_current_time,
                self.serper_web_search_tool.get_web_tool(),
                # self.comfy_image_tool.get_tool()  # <-- disabled for image analysis
            ]
        else:
            tools = [
                get_current_date,
                get_current_time,
                self.serper_web_search_tool.get_web_tool(),
                self.comfy_image_tool.get_tool()  # <-- only exposed when generating
            ]

        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.SYSTEM_MESSAGE),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, self.tools, chat_prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

        # Add user message to memory
        self.history_db[conversation_id].append(
            HumanMessage(content=prompt)
        )

        result = agent_executor.invoke({
            "input": prompt,
            "history": self.history_db[conversation_id]
        })

        response = result.get("output", "")

        if not response:
            if result.get("intermediate_steps"):
                last_tool_result = result["intermediate_steps"][-1][1]
                response = f"I've checked that for you: {last_tool_result}"
            else:
                response = "Error no response. Please check if AI server is running."

        # Add AI reply to memory
        self.history_db[conversation_id].append(
            AIMessage(content=response)
        )

        # Trim memory
        max_messages = int(self.config.SHORT_MEMORY) * 2
        if len(self.history_db[conversation_id]) > max_messages:
            self.history_db[conversation_id] = self.history_db[conversation_id][-max_messages:]

        return response