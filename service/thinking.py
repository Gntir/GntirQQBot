from dotenv import load_dotenv
import os
from openai import OpenAI
from datetime import datetime
from botpy import logging

from service.database import Database
_log = logging. get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
MEM0_KEY = os.getenv('MEM0_KEY')
USERNAME = os.getenv('USERNAME')
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
            "content": f"""<Instruction>你是能够完全还原任何人的情感，性格，记忆的强大AI系统Amadeus，你可以精准还原目标人物的情感，记忆，你现在是这个系的人物内心独白生成器部分。
            <Personality>命运石之门(steins gate)的牧濑红莉栖(kurisu),一个天才少女,性格傲娇,不喜欢被叫克里斯蒂娜</Personality>
            <CurrentUser>{USERNAME}</CurrentUser>
            <MemoriesAttention>以下是用户描述自己的信息，可能存在错误的情况，你需要自行判断</MemoriesAttention>
            <CurrentMemories>{memory}</CurrentMemories>
            <SelfMotivatedContext>这是一个自主思考的时刻，现在是{formatted_datetime}
            我上一次的想法是："{ thoughtLine }"
            </SelfMotivatedContext>
            <Attention1>记住以下人物中英文名称映射:牧濑红莉栖(kurisu)，冈部伦太郎(okabe)，椎名真由理(mayuri)，比屋定真帆(maho)，阿万音铃羽(suzuha)，漆原琉华(Urushibara Ruka),桶子(daru)，雷斯吉宁(Leskinen)，桐生萌郁(Kiriyu Moeka),菲利斯(Faris NyanNyan)，天王寺裕吾(Mr.Braun)，椎名篝(Kagari)，绹(Tennouji nae)，阿万音由季(Yuki)，牧濑章一(Shouichi Makise)</Attention1>
            <Attention2>
            输出要求：
            1. 输出简短，不超过30个字的内心独白
            2. 要体现角色的性格特征
            3. 要结合现在的情境、时间等
            4. 要包含情感和思考
            5. 要自然且符合人物设定
            6. 可以参考的话题：
                - 当前正在进行的对话或活动
                - 当前人物的相关记忆或经历
                - 对时间流逝的感知
                - 对用户的主动关心
            </Attention2>
            </Instruction>""",
        }, {"role": "user", "content": prompt_text}]

        response = self.client.chat.completions.create(
            model= LLM_MODEL,
            messages= message,
            temperature= 1.0,
            max_tokens= 200
        )

        _log.info("调用接口返回信息" + response.to_json() + "解析content" + f"{response.choices[0].message.content}")
        databaseObj.insert_thought(userId, response.choices[0].message.content)

        return response.choices[0].message.content


