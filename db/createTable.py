import sqlite3
import json
import os
from pathlib import Path

def init_database():
    """
    初始化数据库
    返回: (success: bool, message: str)
    """
    try:
        # 获取项目根目录（向上两级：db -> 项目根目录）
        script_dir = Path(__file__).parent.resolve()
        base_dir = script_dir.parent.resolve()
        
        # 确保db目录存在
        db_dir = base_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径
        db_file = db_dir / "database.db"

        # 连接到SQLite数据库（如果文件不存在会自动创建）
        # 启用外键约束
        conn = sqlite3.connect(str(db_file))
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # 平台类型映射
        platform_map = {
            1: '小红书',
            2: '视频号',
            3: '抖音',
            4: '快手',
            5: 'Bilibili',
            6: '百家号',
            7: 'TikTok'
        }
        
        # 1. 创建账号记录表（优化版）
        cursor.execute('''
CREATE TABLE IF NOT EXISTS user_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER NOT NULL,                    -- 平台类型：1小红书 2视频号 3抖音 4快手 5Bilibili 6百家号 7TikTok
            filePath TEXT NOT NULL,                   -- Cookie文件路径（相对路径）
            userName TEXT NOT NULL,                   -- 账号名称/用户名
            status INTEGER DEFAULT 0,                -- 状态：0无效 1有效 2验证中
            platform_name TEXT,                      -- 平台名称（冗余字段，便于查询）
            avatar_url TEXT,                          -- 头像URL（可选）
            last_verify_time DATETIME,                -- 最后验证时间
            verify_count INTEGER DEFAULT 0,          -- 验证次数
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
            remark TEXT,                              -- 备注信息
            is_active INTEGER DEFAULT 1,              -- 是否启用：0禁用 1启用
            group_id INTEGER,                         -- 分组ID（关联 account_groups 表）
            tags TEXT,                                -- 标签（JSON数组，如 ["主力账号", "测试"]）
            auto_refresh_enabled INTEGER DEFAULT 1,   -- 是否启用自动刷新：0否 1是
            refresh_interval_days INTEGER DEFAULT 7,   -- 刷新间隔（天）
            next_refresh_time DATETIME,               -- 下次刷新时间
            last_used_time DATETIME,                  -- 最后使用时间（发布任务时更新）
            publish_count INTEGER DEFAULT 0,          -- 发布次数
            success_count INTEGER DEFAULT 0,          -- 成功次数
            fail_count INTEGER DEFAULT 0,             -- 失败次数
            FOREIGN KEY (group_id) REFERENCES account_groups(id) ON DELETE SET NULL
)
''')

        # 2. 创建文件记录表（优化版）
        cursor.execute('''CREATE TABLE IF NOT EXISTS file_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,                         -- UUID（从file_path提取，独立存储）
            filename TEXT NOT NULL,                   -- 原始文件名
            file_path TEXT NOT NULL,                  -- 存储路径（包含UUID）
            filesize REAL NOT NULL,                  -- 文件大小（MB）
            file_type TEXT,                           -- 文件类型：video/image/other
            mime_type TEXT,                           -- MIME类型：video/mp4, image/png等
            duration REAL,                            -- 视频时长（秒，仅视频文件，可选）
            width INTEGER,                            -- 宽度（像素，仅图片/视频，可选）
            height INTEGER,                           -- 高度（像素，仅图片/视频，可选）
            md5_hash TEXT,                            -- MD5哈希值（用于去重，可选）
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 上传时间
            last_used_time DATETIME,                  -- 最后使用时间
            use_count INTEGER DEFAULT 0,             -- 使用次数
            is_deleted INTEGER DEFAULT 0,            -- 是否已删除：0否 1是（软删除）
            remark TEXT                               -- 备注
        )
        ''')
        
        # 3. 创建发布任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,                           -- 任务名称（可选）
            platform_type INTEGER NOT NULL,            -- 平台类型
            account_id INTEGER NOT NULL,               -- 账号ID（关联user_info）
            file_id INTEGER NOT NULL,                  -- 文件ID（关联file_records）
            title TEXT NOT NULL,                      -- 视频标题
            tags TEXT,                                -- 标签/话题（JSON数组字符串）
            category INTEGER DEFAULT 0,              -- 分类：0非原创 其他为原创
            product_link TEXT,                        -- 商品链接（抖音）
            product_title TEXT,                        -- 商品标题（抖音）
            thumbnail_path TEXT,                       -- 封面图路径
            is_draft INTEGER DEFAULT 0,             -- 是否草稿：0否 1是（视频号）
            schedule_enabled INTEGER DEFAULT 0,      -- 是否定时发布：0否 1是
            scheduled_time DATETIME,                  -- 计划发布时间
            status INTEGER DEFAULT 0,                -- 状态：0待发布 1发布中 2成功 3失败 4已取消
            is_deleted INTEGER DEFAULT 0,            -- 是否已删除：0否 1是（软删除）
            retry_count INTEGER DEFAULT 0,           -- 重试次数
            max_retry INTEGER DEFAULT 3,             -- 最大重试次数
            error_message TEXT,                       -- 错误信息
            platform_video_id TEXT,                   -- 平台返回的视频ID（成功后）
            platform_video_url TEXT,                  -- 平台视频链接（成功后）
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            publish_time DATETIME,                    -- 实际发布时间
            FOREIGN KEY (account_id) REFERENCES user_info(id) ON DELETE CASCADE,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE SET NULL
        )
        ''')
        
        # 4. 创建发布历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,                          -- 关联publish_tasks.id（可选）
            platform_type INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status INTEGER NOT NULL,                  -- 状态：2成功 3失败
            platform_video_id TEXT,                   -- 平台视频ID
            platform_video_url TEXT,                  -- 平台视频链接
            error_message TEXT,                       -- 错误信息（失败时）
            publish_time DATETIME,                     -- 实际发布时间
            duration_seconds INTEGER,                  -- 上传耗时（秒）
            file_size_mb REAL,                        -- 文件大小（MB）
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES user_info(id) ON DELETE SET NULL,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE SET NULL
        )
        ''')
        
        # 5. 创建Cookie验证日志表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cookie_verification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,              -- 账号ID
            platform_type INTEGER NOT NULL,           -- 平台类型
            verify_result INTEGER NOT NULL,           -- 验证结果：0失败 1成功
            verify_method TEXT,                       -- 验证方法：auto/manual
            error_message TEXT,                       -- 错误信息（失败时）
            verify_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            duration_ms INTEGER,                      -- 验证耗时（毫秒）
            FOREIGN KEY (account_id) REFERENCES user_info(id) ON DELETE CASCADE
        )
        ''')
        
        # 6. 创建账号分组表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,                -- 分组名称
            description TEXT,                         -- 分组描述
            color TEXT,                               -- 分组颜色（用于UI显示）
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 7. 创建平台统计表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_type INTEGER NOT NULL,           -- 平台类型
            account_id INTEGER,                       -- 账号ID（NULL表示全部账号）
            stat_date DATE NOT NULL,                  -- 统计日期
            total_tasks INTEGER DEFAULT 0,            -- 总任务数
            success_count INTEGER DEFAULT 0,         -- 成功数
            fail_count INTEGER DEFAULT 0,             -- 失败数
            total_file_size_mb REAL DEFAULT 0,       -- 总文件大小（MB）
            avg_duration_seconds REAL DEFAULT 0,     -- 平均上传耗时（秒）
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform_type, account_id, stat_date),
            FOREIGN KEY (account_id) REFERENCES user_info(id) ON DELETE CASCADE
)
''')

        # 创建索引
        create_indexes(cursor)

        # 提交更改
        conn.commit()
        conn.close()
        
        return True, "数据库初始化成功"
    except sqlite3.Error as e:
        return False, f"数据库错误: {e}"
    except Exception as e:
        return False, f"初始化失败: {e}"


def create_indexes(cursor):
    """创建所有索引"""
    indexes = [
        # user_info 表索引
        ("idx_user_info_type", "user_info", "type"),
        ("idx_user_info_status", "user_info", "status"),
        ("idx_user_info_create_time", "user_info", "create_time"),
        ("idx_user_info_group_id", "user_info", "group_id"),
        ("idx_user_info_next_refresh_time", "user_info", "next_refresh_time"),
        
        # account_groups 表索引
        ("idx_account_groups_name", "account_groups", "name"),
        
        # file_records 表索引
        ("idx_file_records_uuid", "file_records", "uuid"),
        ("idx_file_records_file_type", "file_records", "file_type"),
        ("idx_file_records_upload_time", "file_records", "upload_time"),
        ("idx_file_records_is_deleted", "file_records", "is_deleted"),
        
        # publish_tasks 表索引
        ("idx_publish_tasks_status", "publish_tasks", "status"),
        ("idx_publish_tasks_platform", "publish_tasks", "platform_type"),
        ("idx_publish_tasks_account", "publish_tasks", "account_id"),
        ("idx_publish_tasks_scheduled_time", "publish_tasks", "scheduled_time"),
        ("idx_publish_tasks_create_time", "publish_tasks", "create_time"),
        
        # publish_history 表索引
        ("idx_publish_history_platform", "publish_history", "platform_type"),
        ("idx_publish_history_account", "publish_history", "account_id"),
        ("idx_publish_history_status", "publish_history", "status"),
        ("idx_publish_history_publish_time", "publish_history", "publish_time"),
        
        # cookie_verification_log 表索引
        ("idx_cookie_verify_account", "cookie_verification_log", "account_id"),
        ("idx_cookie_verify_time", "cookie_verification_log", "verify_time"),
        ("idx_cookie_verify_result", "cookie_verification_log", "verify_result"),
        
        # platform_statistics 表索引
        ("idx_platform_stats_date", "platform_statistics", "stat_date"),
        ("idx_platform_stats_platform", "platform_statistics", "platform_type"),
    ]
    
    for idx_name, table_name, column_name in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name})
            """)
        except sqlite3.Error as e:
            # 索引可能已存在，忽略错误
            pass


if __name__ == "__main__":
    # 直接运行此脚本时执行初始化
    success, message = init_database()
    if success:
        # Windows 默认控制台可能是 GBK，打印 emoji 会触发 UnicodeEncodeError
        print("[OK] " + message)
    else:
        print("[ERR] " + message)
        exit(1)
