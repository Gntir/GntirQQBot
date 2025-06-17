from dotenv import load_dotenv
import os
from mem0 import MemoryClient
from openai import OpenAI
from botpy import logging
from datetime import datetime
from service.database import Database
_log = logging.get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
databaseObj = Database()

class MemoryService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(base_url=LLM_API_URL, api_key=LLM_API_KEY)
        self.m0Client = MemoryClient(api_key="m0-pclrFtJo1dd7wJY0sp2bno7KRVp0qRhX1N4Xt1ey")

    def set_memory(self, userId, text):
        _log.info(f"保存记忆: {text}")
        tools = [{
            "type": "function",
            "name": "set_memory",
            "description": "存储长期记忆的工具",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The content of the memory.Must use English"
                    },
                    "metadata": {
                        "type": "Object",
                        "description": "The metadata of the memory.Must use English",
                    }
                },
                "required":  ["content", "metadata"]
                # "additionalProperties": False
            }
        }]
        response = self.client.responses.create(
            model=LLM_MODEL,
            input=[{"role": "user", "content": text}],
            tools=tools
        )
        _log.info(f"返回信息是什么，测试: {response.output}")

        # self.m0Client.add(saveContent, {"user_id": userId, "metadata": saveData.metadata})

