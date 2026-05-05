-- ============================================
-- Personal Blog 数据库初始化脚本
-- ============================================

-- 数据库已由 docker-compose 的 MYSQL_DATABASE 自动创建
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

-- 创建 RAG 知识库表
CREATE TABLE IF NOT EXISTS tb_rag (
    rag_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '知识库ID',
    user_id BIGINT NOT NULL COMMENT '创建者ID（关联 tb_user.user_id）',
    name VARCHAR(100) NOT NULL COMMENT '知识库名称',
    description VARCHAR(500) DEFAULT '' COMMENT '知识库描述',
    namespace VARCHAR(100) NOT NULL UNIQUE COMMENT '命名空间（唯一标识）',
    collection_name VARCHAR(100) NOT NULL DEFAULT 'rag_knowledge_base' COMMENT 'Qdrant集合名',
    file_path VARCHAR(500) DEFAULT '' COMMENT '知识库文件路径',
    file_count INT DEFAULT 0 COMMENT '文件数量',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0-未索引，1-已索引，2-索引中',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG知识库表';

-- 创建计划表
CREATE TABLE IF NOT EXISTS tb_plan (
    plan_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '计划ID',
    user_id BIGINT NOT NULL COMMENT '用户ID（关联 tb_user.user_id）',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    main_goal VARCHAR(1024) NOT NULL COMMENT '计划主要目标',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_session (session_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务计划表';

-- 创建计划任务表
CREATE TABLE IF NOT EXISTS tb_plan_task (
    task_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    plan_id BIGINT NOT NULL COMMENT '所属计划ID（关联 tb_plan.plan_id，级联删除）',
    parent_task_id BIGINT NULL COMMENT '父任务ID（关联 tb_plan_task.task_id，级联删除）',
    task_path VARCHAR(32) NOT NULL COMMENT '任务路径：如 0、0.1、0.1.2',
    task_goal VARCHAR(2048) NOT NULL COMMENT '任务目标描述',
    task_state VARCHAR(32) NOT NULL DEFAULT 'open' COMMENT '任务状态：open/in_progress/completed/verified/abandoned',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (plan_id) REFERENCES tb_plan(plan_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_task_id) REFERENCES tb_plan_task(task_id) ON DELETE CASCADE,
    INDEX idx_plan (plan_id),
    INDEX idx_parent (parent_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计划任务表';
