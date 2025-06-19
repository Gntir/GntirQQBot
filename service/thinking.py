from dotenv import load_dotenv
import os
from mem0 import MemoryClient
from openai import OpenAI
import json
from botpy import logging
from service.database import Database
_log = logging. get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
MEM0_KEY = os.getenv('MEM0_KEY')
databaseObj = Database()

class ThinkService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(base_url=LLM_API_URL, api_key=LLM_API_KEY)
        self.m0Client = MemoryClient(api_key=MEM0_KEY)

    def think(self, memoryLine, text):
        selfMotivatedMessage = {
            "message_type": "ai_self_motivated",
            "context": {
                "lastMonologue": lastThought,
            },
        }


