from dotenv import load_dotenv
import os
import mysql.connector
from botpy import logging

load_dotenv()
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_DB = os.getenv('DATABASE_DB')
_log = logging.get_logger()

class Database:
    def __init__(self):
        Database.init_database(self)

    def init_database(self):
        # 初始化 db 对象
        self.db = mysql.connector.connect(
            host=DATABASE_HOST, # MySQL服务器地址
            user=DATABASE_USER,  # 用户名
            password=DATABASE_PASSWORD,  # 密码
            database=DATABASE_DB  # 数据库名称
        )
        # 创建游标对象，用于执行SQL查询
        self.cursor = self.db.cursor()

    def insert_text(self,user,text,role):
        try:
            _log.info(f"插入数据: {user, text, role}")
            sql = "INSERT INTO text_history (user, text, role, updateTime) VALUES (%s, %s, %s, NOW())"
            self.cursor.execute(sql, (user, text, role))
            self.db.commit()
            _log.info(f"插入数据成功")
            return True
        except Exception as e:
            _log.error("出错了", e)
            Database.init_database(self)
            return False

    def search_text(self,user):
        try:
            _log.info(f"查询数据: {user}")
            sql = "SELECT * FROM( SELECT * FROM text_history WHERE user='%s' ORDER BY id DESC LIMIT 50) AS temp ORDER BY id ASC" % user
            self.cursor.execute(sql)
            # 获取查询结果
            results = self.cursor.fetchall()
            return results
        except Exception as e:
            _log.error("出错了", e)
            Database.init_database(self)
            return []