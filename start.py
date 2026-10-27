# -*- coding: utf-8 -*-
import asyncio
import os

from dotenv import load_dotenv
import botpy
from botpy import logging
from botpy.message import C2CMessage
from service.chat import ChatService

load_dotenv()
QQ_BOT_APPID = os.getenv('QQ_BOT_APPID')
QQ_BOT_SECRET = os.getenv('QQ_BOT_SECRET')
_log = logging.get_logger()
chatService = ChatService()

# 单条消息整体处理超时（含记忆画像、内心独白、主对话多次 LLM 调用），超时则给兜底回复
PROCESS_TIMEOUT_SECONDS = 120
# 处理失败/超时时的兜底回复（贴合鲸鱼娘人设，可自行修改）
FALLBACK_REPLY = "呜……我刚才好像走神了，主人再说一遍好不好？"

# 每用户一把异步锁：同一用户连发多条消息时按顺序处理，避免回复乱序/上下文错乱；不同用户之间仍然并行
_user_locks: dict = {}


def _get_user_lock(user_id: str) -> asyncio.Lock:
    lock = _user_locks.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _user_locks[user_id] = lock
    return lock


class MyClient(botpy.Client):

    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_c2c_message_create(self, message: C2CMessage):
        _log.info(message)
        user_id = message.author.user_openid

        # 忽略空内容/非文本消息（如表情、图片），避免无意义的 LLM 调用
        if not message.content:
            _log.info("收到非文本消息，忽略")
            return

        try:
            # get_chat_messages 是同步阻塞方法（内部多次 LLM 调用 + 数据库读写，可能耗时十几秒），
            # 直接调用会卡死事件循环导致机器人期间无法收发任何消息，这里丢进线程池执行并加超时保护
            async with _get_user_lock(user_id):
                ai_content = await asyncio.wait_for(
                    asyncio.to_thread(
                        chatService.get_chat_messages,
                        user_id,
                        message.content
                    ),
                    timeout=PROCESS_TIMEOUT_SECONDS
                )
            _log.info("AI方法返回" + ai_content)
        except asyncio.TimeoutError:
            _log.error("消息处理超时")
            ai_content = FALLBACK_REPLY
        except Exception as e:
            # LLM 调用失败、数据库断连等任何异常，都只记录日志并兜底回复，绝不让异常冲垮事件循环
            _log.error(f"消息处理失败: {e}")
            ai_content = FALLBACK_REPLY

        try:
            await message._api.post_c2c_message(
                openid=user_id,
                msg_type=0, msg_id=message.id,
                content=ai_content
            )
        except Exception as e:
            _log.error(f"回复消息发送失败: {e}")


if __name__ == "__main__":
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=QQ_BOT_APPID, secret=QQ_BOT_SECRET)
