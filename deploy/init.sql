-- qqAmadeus 数据库初始化脚本
-- 在服务器上执行一次：mysql -u root -p < deploy/init.sql
-- 表结构字段顺序与代码 SELECT * 的下标访问严格对应，勿调整列顺序：
--   text_history:  [0]=id [1]=user [2]=text [3]=role [4]=updateTime
--   ai_thought:    [0]=id [1]=lastThought [2]=currentThought [3]=user [4]=updateTime

CREATE DATABASE IF NOT EXISTS py_amadeus
    DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE py_amadeus;

-- 对话历史（短期上下文，每次取最近 50 条）
CREATE TABLE IF NOT EXISTS `text_history` (
    `id`         BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user`       VARCHAR(64)  NOT NULL COMMENT 'QQ 用户 openid',
    `text`       TEXT         NOT NULL COMMENT '消息内容',
    `role`       VARCHAR(16)  NOT NULL COMMENT 'user / assistant',
    `updateTime` DATETIME     NOT NULL,
    KEY `idx_user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 内心独白（每次取最近 1 条作为"上一次的想法"）
CREATE TABLE IF NOT EXISTS `ai_thought` (
    `id`            BIGINT AUTO_INCREMENT PRIMARY KEY,
    `lastThought`   TEXT COMMENT '预留字段，当前代码未真正使用',
    `currentThought` TEXT NOT NULL COMMENT '本轮生成的内心独白',
    `user`          VARCHAR(64) NOT NULL,
    `updateTime`    DATETIME    NOT NULL,
    KEY `idx_user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 记忆表（遗留表，当前代码已改用 mem0 云端，保留以兼容历史数据）
CREATE TABLE IF NOT EXISTS `ai_memory` (
    `id`         BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user`       VARCHAR(64) NOT NULL,
    `memory`     TEXT,
    `updateTime` DATETIME    NOT NULL,
    KEY `idx_user` (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
