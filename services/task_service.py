#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务管理服务
负责任务的CRUD操作，包括创建任务、查询任务、更新状态等
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from conf import BASE_DIR


class TaskService:
    """任务管理服务"""
    
    # 任务状态常量
    STATUS_PENDING = 0      # 待发布
    STATUS_RUNNING = 1      # 发布中
    STATUS_SUCCESS = 2      # 成功
    STATUS_FAILED = 3       # 失败
    STATUS_CANCELLED = 4    # 已取消
    
    def __init__(self):
        self.db_path = BASE_DIR / "db" / "database.db"
        # 轻量 schema 自修复：避免本地库未重建导致缺列报错
        self._ensure_schema()

    def _ensure_schema(self):
        """确保任务表具备必要字段（软删除等）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA table_info(publish_tasks)")
            cols = {row["name"] for row in cursor.fetchall()}
            if "is_deleted" not in cols:
                cursor.execute("ALTER TABLE publish_tasks ADD COLUMN is_deleted INTEGER DEFAULT 0")
                conn.commit()
        finally:
            conn.close()
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # 使用Row工厂，可以通过列名访问
        return conn
    
    def create_publish_task(
        self,
        platform_type: int,
        account_id: int,
        file_id: int,
        title: str,
        tags: List[str] = None,
        category: int = 0,
        product_link: str = '',
        product_title: str = '',
        thumbnail_path: str = '',
        is_draft: int = 0,
        schedule_enabled: int = 0,
        scheduled_time: datetime = None,
        task_name: str = None
    ) -> int:
        """
        创建发布任务
        
        Args:
            platform_type: 平台类型
            account_id: 账号ID
            file_id: 文件ID
            title: 视频标题
            tags: 标签列表
            category: 分类（0非原创，其他为原创）
            product_link: 商品链接（抖音）
            product_title: 商品标题（抖音）
            thumbnail_path: 封面图路径
            is_draft: 是否草稿（0否，1是）
            schedule_enabled: 是否定时发布（0否，1是）
            scheduled_time: 计划发布时间
            task_name: 任务名称（可选）
        
        Returns:
            任务ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 将tags列表转为JSON字符串
            tags_json = json.dumps(tags if tags else [], ensure_ascii=False)
            
            # 处理计划发布时间
            scheduled_time_str = None
            if scheduled_time:
                if isinstance(scheduled_time, datetime):
                    scheduled_time_str = scheduled_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    scheduled_time_str = str(scheduled_time)
            
            cursor.execute('''
                INSERT INTO publish_tasks (
                    task_name, platform_type, account_id, file_id, title, tags,
                    category, product_link, product_title, thumbnail_path,
                    is_draft, schedule_enabled, scheduled_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_name, platform_type, account_id, file_id, title, tags_json,
                category, product_link, product_title, thumbnail_path,
                is_draft, schedule_enabled, scheduled_time_str, self.STATUS_PENDING
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            return task_id
        except Exception as e:
            conn.rollback()
            raise Exception(f"创建任务失败: {e}")
        finally:
            conn.close()
    
    def create_batch_tasks(
        self,
        platform_type: int,
        account_ids: List[int],
        file_ids: List[int],
        title: str,
        tags: List[str] = None,
        category: int = 0,
        product_link: str = '',
        product_title: str = '',
        thumbnail_path: str = '',
        is_draft: int = 0,
        schedule_enabled: int = 0,
        scheduled_times: List[datetime] = None
    ) -> List[int]:
        """
        批量创建发布任务
        
        Args:
            platform_type: 平台类型
            account_ids: 账号ID列表
            file_ids: 文件ID列表
            title: 视频标题
            tags: 标签列表
            category: 分类
            product_link: 商品链接
            product_title: 商品标题
            thumbnail_path: 封面图路径
            is_draft: 是否草稿
            schedule_enabled: 是否定时发布
            scheduled_times: 计划发布时间列表（与file_ids对应）
        
        Returns:
            任务ID列表
        """
        task_ids = []
        scheduled_times = scheduled_times or [None] * len(file_ids)
        
        for file_idx, file_id in enumerate(file_ids):
            for account_id in account_ids:
                scheduled_time = scheduled_times[file_idx] if file_idx < len(scheduled_times) else None
                task_id = self.create_publish_task(
                    platform_type=platform_type,
                    account_id=account_id,
                    file_id=file_id,
                    title=title,
                    tags=tags,
                    category=category,
                    product_link=product_link,
                    product_title=product_title,
                    thumbnail_path=thumbnail_path,
                    is_draft=is_draft,
                    schedule_enabled=schedule_enabled,
                    scheduled_time=scheduled_time
                )
                task_ids.append(task_id)
        
        return task_ids
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        """
        获取任务详情
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务信息字典，如果不存在返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM publish_tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
        finally:
            conn.close()
    
    def update_task_status(
        self,
        task_id: int,
        status: int,
        error_message: str = None,
        platform_video_id: str = None,
        platform_video_url: str = None,
        publish_time: datetime = None
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态
            error_message: 错误信息（失败时）
            platform_video_id: 平台视频ID（成功时）
            platform_video_url: 平台视频链接（成功时）
            publish_time: 实际发布时间
        
        Returns:
            是否更新成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            update_fields = ['status = ?', 'update_time = CURRENT_TIMESTAMP']
            params = [status]
            
            if error_message is not None:
                update_fields.append('error_message = ?')
                params.append(error_message)
            
            if platform_video_id is not None:
                update_fields.append('platform_video_id = ?')
                params.append(platform_video_id)
            
            if platform_video_url is not None:
                update_fields.append('platform_video_url = ?')
                params.append(platform_video_url)
            
            if publish_time is not None:
                if isinstance(publish_time, datetime):
                    publish_time_str = publish_time.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    publish_time_str = str(publish_time)
                update_fields.append('publish_time = ?')
                params.append(publish_time_str)
            
            params.append(task_id)
            
            cursor.execute(f'''
                UPDATE publish_tasks 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', params)
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"更新任务状态失败: {e}")
        finally:
            conn.close()
    
    def increment_retry_count(self, task_id: int) -> bool:
        """
        增加任务重试次数
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否更新成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE publish_tasks 
                SET retry_count = retry_count + 1,
                    update_time = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (task_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise Exception(f"更新重试次数失败: {e}")
        finally:
            conn.close()
    
    def cancel_task(self, task_id: int) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否取消成功
        """
        return self.update_task_status(task_id, self.STATUS_CANCELLED)
    
    def list_tasks(
        self,
        platform_type: int = None,
        account_id: int = None,
        status: int = None,
        status_in: List[int] = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> List[Dict]:
        """
        查询任务列表
        
        Args:
            platform_type: 平台类型（可选）
            account_id: 账号ID（可选）
            status: 状态（可选）
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            任务列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            where_clauses = []
            params = []
            
            if not include_deleted:
                where_clauses.append('is_deleted = 0')

            if platform_type is not None:
                where_clauses.append('platform_type = ?')
                params.append(platform_type)
            
            if account_id is not None:
                where_clauses.append('account_id = ?')
                params.append(account_id)
            
            if status is not None:
                where_clauses.append('status = ?')
                params.append(status)

            if status_in:
                placeholders = ",".join(["?"] * len(status_in))
                where_clauses.append(f"status IN ({placeholders})")
                params.extend(status_in)
            
            where_sql = ''
            if where_clauses:
                where_sql = 'WHERE ' + ' AND '.join(where_clauses)
            
            params.extend([limit, offset])
            
            cursor.execute(f'''
                SELECT * FROM publish_tasks
                {where_sql}
                ORDER BY create_time DESC
                LIMIT ? OFFSET ?
            ''', params)
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def count_tasks(
        self,
        platform_type: int = None,
        account_id: int = None,
        status: int = None,
        status_in: List[int] = None,
        include_deleted: bool = False,
    ) -> int:
        """统计任务数量（与 list_tasks 同筛选条件）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            where_clauses = []
            params = []

            if not include_deleted:
                where_clauses.append("is_deleted = 0")

            if platform_type is not None:
                where_clauses.append("platform_type = ?")
                params.append(platform_type)

            if account_id is not None:
                where_clauses.append("account_id = ?")
                params.append(account_id)

            if status is not None:
                where_clauses.append("status = ?")
                params.append(status)

            if status_in:
                placeholders = ",".join(["?"] * len(status_in))
                where_clauses.append(f"status IN ({placeholders})")
                params.extend(status_in)

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(f"SELECT COUNT(1) as cnt FROM publish_tasks {where_sql}", params)
            row = cursor.fetchone()
            return int(row["cnt"] if row else 0)
        finally:
            conn.close()

    def soft_delete_task(self, task_id: int) -> bool:
        """
        软删除任务：
        - 若任务为待发布/发布中，则先标记为已取消
        - 最终设置 is_deleted=1
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, status FROM publish_tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return False

            updates = ["is_deleted = 1", "update_time = CURRENT_TIMESTAMP"]
            params = []

            if row["status"] in (self.STATUS_PENDING, self.STATUS_RUNNING):
                updates.append("status = ?")
                params.append(self.STATUS_CANCELLED)

            params.append(task_id)
            cursor.execute(
                f"UPDATE publish_tasks SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_pending_tasks(self, limit: int = 10) -> List[Dict]:
        """
        获取待执行的任务列表
        
        Args:
            limit: 限制数量
        
        Returns:
            待执行任务列表
        """
        return self.list_tasks(status=self.STATUS_PENDING, limit=limit)
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转为字典"""
        task_dict = dict(row)
        
        # 解析tags JSON
        if task_dict.get('tags'):
            try:
                task_dict['tags'] = json.loads(task_dict['tags'])
            except:
                task_dict['tags'] = []
        else:
            task_dict['tags'] = []
        
        return task_dict

