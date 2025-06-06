# -*- coding: utf-8 -*-
import asyncio
import os

import botpy
from service.chat import ChatService
from botpy import logging
from botpy.message import C2CMessage

_log = logging.get_logger()
chatService = ChatService()

class MyClient(botpy.Client):

    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_c2c_message_create(self, message: C2CMessage):
        _log.info(message)

        ai_content = chatService.get_chat_messages(message.author.user_openid, message.content)
        _log.info("AI方法返回" + ai_content)
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
            msg_type=0, msg_id=message.id,
            content=ai_content
        )

if __name__ == "__main__":
    # 通过预设置的类型，设置需要监听的事件通道
    # intents = botpy.Intents.none()
    # intents.public_guild_messages=True

    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True)
    client = MyClient(intents=intents)
    client.run(appid="102778112", secret="X7hHrR2dEpQ1cEqS4gIuW9mP2fIvZDrV")

    # X7hHrR2dEpQ1cEqS4gIuW9mP2fIvZDrV