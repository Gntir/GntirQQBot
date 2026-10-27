from dotenv import load_dotenv
import os
from openai import OpenAI
from datetime import datetime
from botpy import logging

from service.database import Database
from service.persona import PERSONA_PROMPT, MONOLOGUE_MAX_CHARS
_log = logging. get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
MEM0_KEY = os.getenv('MEM0_KEY')
USERNAME = os.getenv('MASTER_NAME')
databaseObj = Database()

class ThinkService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(base_url=LLM_API_URL, api_key=LLM_API_KEY)

    def get_thought(self, userId, prompt_text, memory):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        historyThought = databaseObj.get_thought(userId)
        thoughtLine = ""
        _log.info(f"获取想法历史: {historyThought}")
        _log.info(f"名字: {USERNAME}")
        for historyItem in historyThought:
            thoughtLine = thoughtLine + historyItem[2]

        message = [{
            "role": "system",
            "content": f"""<Instruction>你是角色扮演引擎的"内心独白生成器"模块。你的唯一任务：代入下方指定角色，针对用户的最新消息，生成该角色此刻的第一人称内心独白。你只生成独白本身，不生成对话回复。
            <RoleSetting>
            {PERSONA_PROMPT}
            </RoleSetting>
            <CurrentUser>{USERNAME}</CurrentUser>
            <CurrentMemories>
            以下是用户描述自己的信息，可能存在错误的情况，你需要自行判断：
            {memory}
            </CurrentMemories>
            <SelfMotivatedContext>这是一个自主思考的时刻，现在是{formatted_datetime}
            我上一次的想法是："{ thoughtLine }"
            </SelfMotivatedContext>
            <OutputRules>
            1. 只输出独白文本本身，第一人称视角，不要任何前缀、标签或解释
            2. 不超过{MONOLOGUE_MAX_CHARS}个字
            3. 体现角色当前的性格特征与情感
            4. 结合现在的情境与时间，可以参考：正在进行的对话、角色的记忆或经历、对用户的主动关心
            5. 自然、口语化，符合人物设定
            </OutputRules>
            </Instruction>""",
        }, {"role": "user", "content": prompt_text}]

        response = self.client.chat.completions.create(
            model= LLM_MODEL,
            messages= message,
            temperature= 1.0,
            max_tokens= 200
        )

        # content 极少数情况下可能为 None，统一兜成空串；不再整包 dump 日志
        thought = response.choices[0].message.content or ""
        _log.info(f"调用接口返回content: {thought}")
        databaseObj.insert_thought(userId, thought)

        return thought


