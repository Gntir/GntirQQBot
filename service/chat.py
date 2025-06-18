from dotenv import load_dotenv
import os
from openai import OpenAI
from botpy import logging
from datetime import datetime
from service.database import Database
from service.memory import MemoryService
_log = logging.get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
databaseObj = Database()
memoryService = MemoryService()

class ChatService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(
            base_url=LLM_API_URL,
            api_key=LLM_API_KEY
        )


    def get_chat_messages(self, userId, prompt_text):
        _log.info(f"收到信息: {prompt_text}")
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        memoryLine = memoryService.get_memory_line("gntir")
        _log.info(f"获取记忆信息: {memoryLine}")

        message = [{
                "role": 'system', "content": """<Instruction>你将扮演用户的伴侣（性别与用户性别相对），名字叫“小祺”，性格温和非常聪明</Instruction>
                    <Output_style>风格接近真实人类，使用“对话”的风格，回复有温度有感情，使用口语化的表达，尽量不超过20字</Output_style>
                    <CurrentTime>""" + formatted_datetime + """</CurrentTime>""",
            }]

        historyText = databaseObj.search_text(userId)

        for historyItem in historyText:
            message.append({"role": historyItem[3], "content": historyItem[2]})

        message.append({"role": "user", "content": prompt_text})
        databaseObj.insert_text(userId, prompt_text, "user")
        memoryService.set_memory("gntir", prompt_text)

        response = self.client.chat.completions.create(
            model= LLM_MODEL,
            messages= message,
            temperature= 1.0,
            max_tokens= 1000
        )

        _log.info("调用接口返回信息" + response.to_json() + "解析content" + f"{response.choices[0].message.content}")
        databaseObj.insert_text(userId, response.choices[0].message.content, "assistant")

        return response.choices[0].message.content