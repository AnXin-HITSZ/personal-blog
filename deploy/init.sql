-- ============================================
-- Personal Blog 数据库初始化脚本
-- ============================================

CREATE DATABASE personal_blog;

USE personal_blog;

-- 创建用户表
CREATE TABLE IF NOT EXISTS tb_user (
    -- 用户ID：主键，自增，使用 BIGINT 避免数据量溢出
                                        user_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',

    -- 用户名：唯一，不能为空，长度限制为 50
                                        username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',

    -- 用户密码：存储加密后的密码（如 BCrypt），长度预留足够
                                        password VARCHAR(100) NOT NULL COMMENT '用户密码（加密存储）',

    -- 是否为管理员：0-普通用户，1-管理员，默认 0
                                        is_admin TINYINT NOT NULL DEFAULT 0 COMMENT '是否为管理员：0-否，1-是',

    -- 创建日期：默认当前时间
                                        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',

    -- 更新日期：自动更新为当前时间
                                        update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 创建文章表
CREATE TABLE IF NOT EXISTS tb_article (
    -- 文章ID：主键，自增，使用 BIGINT 避免数据量溢出
                                          article_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文章ID',

    -- 作者ID：关联 tb_user 表的 user_id
                                          user_id BIGINT NOT NULL DEFAULT 1 COMMENT '作者ID（关联 tb_user.user_id）',

    -- 文章名：不能为空，长度限制为 200
                                          title VARCHAR(200) NOT NULL COMMENT '文章名',

    -- 文章内容：Markdown 格式，使用 LONGTEXT 存储超长内容
                                          content LONGTEXT NOT NULL COMMENT '文章内容（Markdown格式）',

    -- 创建日期：默认当前时间
                                          create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',

    -- 更新日期：自动更新为当前时间
                                          update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统文章表';
