from openai import OpenAI
from botpy import logging
from datetime import datetime
from service.database import Database
_log = logging.get_logger()

databaseObj = Database()

class ChatService:
    def __init__(self):
        # 初始化 client 对象
        self.client = OpenAI(
            # This is the default and can be omitted
            base_url="https://aihubmix.com/v1",
            api_key='sk-l8BRrZoZHRj4ZEgMCe16Fe0c0e634777A3F33eDcCcA3Af9b'
        )


    def get_chat_messages(self, userId, prompt_text):
        _log.info(f"收到信息: {prompt_text}")
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # if ("删除对话历史" in prompt_text):
        #     return "已删除"

        message = [{
                "role": 'system', "content": """<Instruction>你将扮演用户的伴侣（性别与用户性别相对），名字叫“小祺”，性格温和非常聪明</Instruction>
                    <Output_style>风格接近真实人类，使用“对话”的风格，回复有温度有感情，使用口语化的表达，尽量不超过20字</Output_style>
                    <CurrentTime>""" + formatted_datetime + """</CurrentTime>""",
            }]

        historyText = databaseObj.search_text(userId)

        _log.info(f"查询数据库: {historyText}")

        for historyItem in historyText:
            _log.info(f"列表的数据: {historyItem[3]},{historyItem[2]}")
            message.append({"role": historyItem[3], "content": historyItem[2]})

        message.append({"role": "user", "content": prompt_text})
        databaseObj.insert_text(userId, prompt_text, "user")
        _log.info(f"数据是什么: {message}")

        response = self.client.chat.completions.create(
            model= "claude-3-7-sonnet-20250219",
            messages= message,
            temperature= 1.0,
            max_tokens= 1000
        )

        _log.info("调用接口返回信息" + response.to_json() + "解析content" + f"{response.choices[0].message.content}")
        databaseObj.insert_text(userId, response.choices[0].message.content, "assistant")

        return response.choices[0].message.content