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

    def generate_reply(self, conversation_id: str, prompt: str) -> str:
        if conversation_id not in self.history_db:
            self.history_db[conversation_id] = []

        llm = ChatOpenAI(**self.llm_params)
        
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.SYSTEM_MESSAGE),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, self.tools, chat_prompt)
        
        # Create the Executor (The engine that runs the tool)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )

        # Run the Agent (it automatically handles the history and tool calls)
        result = agent_executor.invoke({
            "input": prompt,
            "history": self.history_db[conversation_id]
        })
        
        response = result["output"]

        if not response:
            if result.get("intermediate_steps"):
                last_tool_result = result["intermediate_steps"][-1][1]
                response = f"I've checked that for you: {last_tool_result}"
            else:
                response = "Error no response. Please try again or check if AI server is online!"

        # Update Memory
        self.history_db[conversation_id].append(HumanMessage(content=prompt))
        self.history_db[conversation_id].append(AIMessage(content=response))
        
        # 1 exchange = 2 messages  
        # If user enters 10 = 20 messages
        max_messages = int(self.config.SHORT_MEMORY) * 2
        if len(self.history_db[conversation_id]) > max_messages:
            self.history_db[conversation_id] = self.history_db[conversation_id][-max_messages:]

        return response