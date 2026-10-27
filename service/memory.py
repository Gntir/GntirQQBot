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
# 记忆服务专用通道：默认与主通道共用（aihubmix），仅模型不同（LLM_MEMORY_MODEL）
# 配置了 MEMORY_API_* 时才会走独立供应商
MEMORY_API_URL = os.getenv('MEMORY_API_URL') or LLM_API_URL
MEMORY_API_KEY = os.getenv('MEMORY_API_KEY') or LLM_API_KEY
MEMORY_MODEL = os.getenv('LLM_MEMORY_MODEL', LLM_MODEL)
MEM0_KEY = os.getenv('MEM0_KEY')
databaseObj = Database()

class MemoryService:
    def __init__(self):
        # 记忆服务 client：默认与主通道同源（aihubmix），仅模型不同
        self.client = OpenAI(base_url=MEMORY_API_URL, api_key=MEMORY_API_KEY)
        self.m0Client = MemoryClient(api_key=MEM0_KEY)

    def set_memory(self, userId, text):
        _log.info(f"保存记忆: {text}")
        # Chat Completions 的工具定义格式（DeepSeek 兼容），并修正原 location/content 字段不一致的问题
        tools = [{
            "type": "function",
            "function": {
                "name": "set_memory",
                "description": "存储长期记忆的工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": """The content of the memory.Need user information (personal details, hobbies, experiences, etc.) as short statements like "name is xxx", "likes cake".Must use English"""
                        },
                        "metadata": {
                            "type": "string",
                            "description": "The metadata of the memory.Need one or two words to generalize.Must use English",
                        }
                    },
                    "required": ["content", "metadata"]
                }
            }
        }]
        # DeepSeek 不支持 OpenAI 的 Responses API，改用 chat.completions + function calling
        response = self.client.chat.completions.create(
            model=MEMORY_MODEL,
            messages=[
                {"role": 'system', "content": "你需要作为一个工具调用器，你需要判断当前对话是否包含用户的关键信息，如果包含则需要对关键信息进行分类，并输出长期记忆内容"},
                {"role": "user", "content": text}
            ],
            tools=tools
        )
        message = response.choices[0].message
        _log.info(f"调用记忆存储返回信息: {message}")

        # 模型判断当前对话不含关键信息时不会调用工具，直接跳过
        if not message.tool_calls:
            _log.info("当前对话未包含需要长期存储的关键信息")
            return

        try:
            args_dict = json.loads(message.tool_calls[0].function.arguments)
        except json.JSONDecodeError as e:
            _log.error(f"解析工具参数出错: {e}")
            return
        _log.info(f"参数转换: {args_dict}")
        content = args_dict.get('content')
        if content:
            self.m0Client.add([{"role": "assistant", "content": content}], user_id=userId, metadata={"category": args_dict.get('metadata', '')})


    def get_memory_line(self, userId):
        memoryList = MemoryService.get_memory(self, userId)
        memoryStr = ""
        for index in range(len(memoryList)):
            memoryStr += str(index) + "." + memoryList[index].get("memory") + ";"

        response = self.client.chat.completions.create(
            model=MEMORY_MODEL,
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