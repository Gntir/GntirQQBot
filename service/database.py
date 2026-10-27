from dotenv import load_dotenv
import os
import threading
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
        # 加锁保护：start.py 用 asyncio.to_thread 并发处理消息后，
        # 同一个 Database 实例会被多个线程共享，而 MySQL 连接/游标不是线程安全的
        self._lock = threading.Lock()
        Database.init_database(self)

    def init_database(self):
        # 初始化 db 对象
        # use_pure=True 强制使用纯 Python 实现：默认的 C 扩展(_mysql_connector)在
        # connector 9.x + MySQL 5.7 组合下连接时段错误崩溃（本机实测），纯 Python 实现无此问题
        self.db = mysql.connector.connect(
            host=DATABASE_HOST, # MySQL服务器地址
            user=DATABASE_USER,  # 用户名
            password=DATABASE_PASSWORD,  # 密码
            database=DATABASE_DB,  # 数据库名称
            use_pure=True
        )
        # 创建游标对象，用于执行SQL查询
        self.cursor = self.db.cursor()

    def _reconnect(self):
        # 出错后重建连接；先关闭旧连接，避免长驻进程句柄泄漏
        with self._lock:
            try:
                self.db.close()
            except Exception:
                pass
            Database.init_database(self)

    def insert_text(self, user, text, role):
        try:
            _log.info(f"插入数据: {user, text, role}")
            sql = "INSERT INTO text_history (user, text, role, updateTime) VALUES (%s, %s, %s, NOW())"
            with self._lock:
                self.cursor.execute(sql, (user, text, role))
                self.db.commit()
            _log.info(f"插入数据成功")
            return True
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return False

    def search_text(self, user):
        try:
            _log.info(f"查询数据: {user}")
            # 参数化查询（原先 % 拼接存在 SQL 注入隐患）
            sql = "SELECT * FROM( SELECT * FROM text_history WHERE user=%s ORDER BY id DESC LIMIT 50) AS temp ORDER BY id ASC"
            with self._lock:
                self.cursor.execute(sql, (user,))
                results = self.cursor.fetchall()
            return results
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return []


    def insert_memory(self, user, memory):
        try:
            _log.info(f"插入数据: {user, memory}")
            sql = "INSERT INTO ai_memory (user, memory, updateTime) VALUES (%s, %s, NOW())"
            with self._lock:
                self.cursor.execute(sql, (user, memory))
                self.db.commit()
            _log.info(f"插入数据成功")
            return True
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return False

    def update_memory(self, user, memory):
        try:
            _log.info(f"更新数据: {user, memory}")
            sql = "UPDATE ai_memory SET memory = %s, updateTime = NOW() WHERE user = %s"
            with self._lock:
                self.cursor.execute(sql, (memory, user))
                self.db.commit()
            _log.info(f"更新数据成功")
            return True
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return False

    def get_memory(self, user):
        try:
            _log.info(f"查询数据: {user}")
            sql = "SELECT * FROM( SELECT * FROM ai_memory WHERE user=%s ORDER BY id DESC LIMIT 50) AS temp ORDER BY id ASC"
            with self._lock:
                self.cursor.execute(sql, (user,))
                results = self.cursor.fetchall()
            return results
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return []

    def insert_thought(self, user, thought):
        try:
            _log.info(f"插入数据: {user, thought}")
            sql = "INSERT INTO ai_thought (lastThought, currentThought, user, updateTime) VALUES (%s, %s, %s, NOW())"
            with self._lock:
                self.cursor.execute(sql, ("", thought, user))
                self.db.commit()
            _log.info(f"插入数据成功")
            return True
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return False

    def update_thought(self, user, thought):
        try:
            _log.info(f"更新数据: {user, thought}")
            sql = "UPDATE ai_thought SET lastThought = %s, currentThought = %s, updateTime = NOW() WHERE user = %s"
            with self._lock:
                self.cursor.execute(sql, ("", thought, user))
                self.db.commit()
            _log.info(f"更新数据成功")
            return True
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return False

    def get_thought(self, user):
        try:
            _log.info(f"查询数据: {user}")
            sql = "SELECT * FROM( SELECT * FROM ai_thought WHERE user=%s ORDER BY id DESC LIMIT 1) AS temp ORDER BY id ASC"
            with self._lock:
                self.cursor.execute(sql, (user,))
                results = self.cursor.fetchall()
            return results
        except Exception as e:
            _log.error(f"出错了: {e}")
            Database._reconnect(self)
            return []
