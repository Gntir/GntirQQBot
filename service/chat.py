from dotenv import load_dotenv
import os
from openai import OpenAI
from botpy import logging
from datetime import datetime
from service.database import Database
from service.memory import MemoryService
from service.thinking import ThinkService
from service.persona import PERSONA_PROMPT, REPLY_MAX_CHARS
_log = logging.get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
USERNAME = os.getenv('MASTER_NAME')
databaseObj = Database()
memoryService = MemoryService()
thinkService = ThinkService()

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

        # 记忆画像与内心独白是旁路增强：失败时降级为空值继续，不中断主对话
        try:
            memoryLine = memoryService.get_memory_line(userId)
        except Exception as e:
            _log.error(f"获取记忆画像失败，降级为空记忆: {e}")
            memoryLine = ""
        _log.info(f"获取记忆信息: {memoryLine}")
        try:
            thoughtLine = thinkService.get_thought(userId,prompt_text, memoryLine)
        except Exception as e:
            _log.error(f"生成内心独白失败，降级为空独白: {e}")
            thoughtLine = ""
        _log.info(f"获取想法信息: {thoughtLine}")

        message = [{
                "role": 'system', "content": f"""<Instruction>你是一个高水准的角色扮演引擎，你的任务是完整代入下方指定角色的情感、性格与记忆，以该角色的第一人称身份与用户实时对话，始终保持角色一致，绝不脱离角色。
                    <RoleSetting>
                    {PERSONA_PROMPT}
                    </RoleSetting>
                    <OutputStyle>
                    1. 使用口语化的对话风格，像真人发消息一样自然
                    2. 单次回复尽量不超过{REPLY_MAX_CHARS}字
                    3. 只输出角色的对话内容本身：不要旁白、不要动作描写、不要输出任何标签
                    </OutputStyle>
                    <Interaction>快速会话模式：理解能力强、回复简短，在合适时机可以主动引导或延伸话题</Interaction>
                    <CurrentUser>{USERNAME}</CurrentUser>
                    <CurrentMemories>
                    关于当前用户的长期记忆画像（可能不完整或有错误，请自行判断采信）：
                    {memoryLine}
                    </CurrentMemories>
                    <InnerMonologue>
                    你拥有实时的内心活动，即下方独白内容。你只负责读取并参考它来组织本轮回复（它体现你此刻真实的心理状态），严禁在回复中输出独白的任何内容。
                    {thoughtLine}
                    </InnerMonologue>
                    <CurrentTime>{formatted_datetime}</CurrentTime>
                    </Instruction>""",
            }]

        historyList = databaseObj.search_text(userId)

        for historyItem in historyList:
            message.append({"role": historyItem[3], "content": historyItem[2]})

        message.append({"role": "user", "content": prompt_text})
        databaseObj.insert_text(userId, prompt_text, "user")
        # 记忆抽取同样不允许影响主流程
        try:
            memoryService.set_memory(userId, prompt_text)
        except Exception as e:
            _log.error(f"记忆抽取失败，跳过本次: {e}")

        response = self.client.chat.completions.create(
            model= LLM_MODEL,
            messages= message,
            temperature= 1.0,
            max_tokens= 1000
        )

        # content 极少数情况下可能为 None（如触发内容审查），统一兜成空串；
        # 不再用 response.to_json() 打整包日志（部分 openai 版本无此方法，且噪音大）
        reply = response.choices[0].message.content or ""
        _log.info(f"调用接口返回content: {reply}")
        databaseObj.insert_text(userId, reply, "assistant")

        return reply