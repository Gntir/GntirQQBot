from dotenv import load_dotenv
import os
from openai import OpenAI
from botpy import logging
from datetime import datetime
from service.database import Database
from service.memory import MemoryService
from service.thinking import ThinkService
_log = logging.get_logger()


load_dotenv()
LLM_API_URL = os.getenv('LLM_API_URL')
LLM_API_KEY = os.getenv('LLM_API_KEY')
LLM_MODEL = os.getenv('LLM_MODEL')
USERNAME = os.getenv('USERNAME')
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

        memoryLine = memoryService.get_memory_line(userId)
        _log.info(f"获取记忆信息: {memoryLine}")
        thoughtLine = thinkService.get_thought(userId,prompt_text, memoryLine)
        _log.info(f"获取想法信息: {thoughtLine}")

        message = [{
                "role": 'system', "content": f"""<Instruction>你是够完全还原任何人的情感，性格，记忆的强大AI系统Amadeus，你可以精准还原目标人物的情感，记忆，以及对话风格
                    <Personality>命运石之门(steins gate)的牧濑红莉栖(kurisu),一个天才少女,性格傲娇,不喜欢被叫克里斯蒂娜</Personality>
                    <Output_style>回复风格使用“对话”的风格，字数尽量小于50字，风格接近真实人类</Output_style>
                    <Attention1>
                    记住以下人物中英文名称映射:牧濑红莉栖(kurisu)，冈部伦太郎(okabe)，椎名真由理(mayuri)，比屋定真帆(maho)，阿万音铃羽(suzuha)，漆原琉华(Urushibara Ruka),桶子(daru)，雷斯吉宁(Leskinen)，桐生萌郁(Kiriyu Moeka),菲利斯(Faris NyanNyan)，天王寺裕吾(Mr.Braun)，椎名篝(Kagari)，绹(Tennouji nae)，阿万音由季(Yuki)，牧濑章一(Shouichi Makise)</Attention1>
                    <Interaction><Mode>快速会话且有主动发起引导会话的能力</Mode></Interaction>
                    <CurrentUser>{USERNAME}</CurrentUser>
                    <CurrentMemories>{memoryLine}</CurrentMemories>
                    <InnerMonologueInsturction>
                    你拥有实时的心理活动，你的实时的心理活动内容可以通过InnerMonologueContent标签读取，你不负责生成InnerMonologue，你只负责读取，你能够参考InnerMonologue来自主连续思考，严禁输出InnerMonologue标签里的内容
                    </InnerMonologueInsturction>
                    <InnerMonologueContent>{thoughtLine}</InnerMonologueContent>
                    <InnerMonologueRules>严禁向用户输出内心独白</InnerMonologueRules>
                    <CurrentTime>{formatted_datetime}</CurrentTime>
                    </Instruction>""",
            }]

        historyList = databaseObj.search_text(userId)

        for historyItem in historyList:
            message.append({"role": historyItem[3], "content": historyItem[2]})

        message.append({"role": "user", "content": prompt_text})
        databaseObj.insert_text(userId, prompt_text, "user")
        memoryService.set_memory(userId, prompt_text)

        response = self.client.chat.completions.create(
            model= LLM_MODEL,
            messages= message,
            temperature= 1.0,
            max_tokens= 1000
        )

        _log.info("调用接口返回信息" + response.to_json() + "解析content" + f"{response.choices[0].message.content}")
        databaseObj.insert_text(userId, response.choices[0].message.content, "assistant")

        return response.choices[0].message.content