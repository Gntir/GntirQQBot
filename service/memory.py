from dotenv import load_dotenv
import os
from mem0 import MemoryClient
from openai import OpenAI
import json
from botpy import logging
from service.database import Database
_log = logging.get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
MEM0_KEY = os.getenv('MEM0_KEY')
databaseObj = Database()

class MemoryService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(base_url=LLM_API_URL, api_key=LLM_API_KEY)
        self.m0Client = MemoryClient(api_key=MEM0_KEY)

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
                        "description": """The content of the memory.Need user information (personal details, hobbies, experiences, etc.) as short statements like "name is xxx", "likes cake".Must use English"""
                    },
                    "metadata": {
                        "type": "string",
                        "description": "The metadata of the memory.Need one or two words to generalize.Must use English",
                    }
                },
                "required":  ["content", "metadata"]
                # "additionalProperties": False
            }
        }]
        response = self.client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": 'system',"content": "你需要作为一个工具调用器，你需要判断当前对话是否包含用户的关键信息，如果包含则需要对关键信息进行分类，并输出长期记忆内容"},
                {"role": "user", "content": text}
            ],
            tools=tools
        )
        _log.info(f"调用记忆存储返回信息: {response.output[0]}")

        if hasattr(response.output[0], "arguments"):
            args_dict = json.loads(getattr(response.output[0], "arguments"))
            _log.info(f"参数转换: {args_dict, args_dict['content']}")
            self.m0Client.add([{"role": "assistant", "content": args_dict['content']}], user_id=userId, metadata={"category": args_dict['metadata']})


    def get_memory_line(self, userId):
        memoryList = MemoryService.get_memory(self, userId)
        memoryStr = ""
        for index in range(len(memoryList)):
            memoryStr += str(index) + "." + memoryList[index].get("memory") + ";"

        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你需要作为一个记忆整理大师，对已有的用户信息的进行整合，汇总为不超过200字的描述画像，当用户信息不存在时返回空即可",
                },
                {
                    "role": "user",
                    "content": f"""以下为用户的信息
                    <CurrentMemories>{ memoryStr }</CurrentMemories>""",
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )
        menoryLine = response.choices[0].message.content

        return menoryLine

    def get_memory(self, userId):
        response = self.m0Client.get_all(user_id=userId)
        return response