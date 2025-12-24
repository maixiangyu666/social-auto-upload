#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务执行器
负责执行发布任务，包括调用上传器、重试机制、错误处理等
"""
import asyncio
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from conf import BASE_DIR
from services.task_service import TaskService
from services.account_service import AccountService

# 导入上传器
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from playwright.async_api import async_playwright


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self):
        self.task_service = TaskService()
        self.account_service = AccountService()
        self.db_path = BASE_DIR / "db" / "database.db"
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_account_info(self, account_id: int) -> Optional[Dict]:
        """获取账号信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM user_info WHERE id = ?', (account_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def _get_file_info(self, file_id: int) -> Optional[Dict]:
        """获取文件信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM file_records WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def _update_file_usage(self, file_id: int):
        """更新文件使用统计"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE file_records 
                SET use_count = use_count + 1,
                    last_used_time = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (file_id,))
            conn.commit()
        finally:
            conn.close()
    
    async def execute_task(self, task_id: int) -> Dict:
        """
        执行单个任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            执行结果字典
        """
        task = self.task_service.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}
        
        # 检查任务状态
        if task['status'] != TaskService.STATUS_PENDING:
            return {'success': False, 'error': f'任务状态不正确: {task["status"]}'}
        
        # 更新任务状态为执行中
        self.task_service.update_task_status(task_id, TaskService.STATUS_RUNNING)
        
        start_time = time.time()
        error_message = None
        platform_video_id = None
        platform_video_url = None
        
        try:
            # 获取账号和文件信息
            account_info = self._get_account_info(task['account_id'])
            file_info = self._get_file_info(task['file_id'])
            
            if not account_info:
                raise Exception(f"账号不存在: {task['account_id']}")
            if not file_info:
                raise Exception(f"文件不存在: {task['file_id']}")
            
            # 更新文件使用统计
            self._update_file_usage(task['file_id'])
            
            # 构建文件路径和账号路径
            account_file = BASE_DIR / "cookiesFile" / account_info['filePath']
            video_file = BASE_DIR / "videoFile" / file_info['file_path']
            
            if not account_file.exists():
                raise Exception(f"账号Cookie文件不存在: {account_file}")
            if not video_file.exists():
                raise Exception(f"视频文件不存在: {video_file}")
            
            # 处理计划发布时间
            publish_date = None
            if task['schedule_enabled'] and task['scheduled_time']:
                try:
                    publish_date = datetime.strptime(task['scheduled_time'], '%Y-%m-%d %H:%M:%S')
                except:
                    publish_date = datetime.strptime(task['scheduled_time'], '%Y-%m-%d %H:%M')
            elif not task['schedule_enabled']:
                publish_date = 0
            
            # 解析tags
            tags = task['tags'] if isinstance(task['tags'], list) else []
            
            # 根据平台类型调用对应的上传器
            result = await self._execute_upload(
                platform_type=task['platform_type'],
                title=task['title'],
                file_path=str(video_file),
                account_file=str(account_file),
                tags=tags,
                publish_date=publish_date,
                category=task['category'],
                product_link=task.get('product_link', ''),
                product_title=task.get('product_title', ''),
                thumbnail_path=task.get('thumbnail_path', ''),
                is_draft=task.get('is_draft', 0)
            )
            
            duration = int(time.time() - start_time)
            
            if result['success']:
                # 任务成功
                self.task_service.update_task_status(
                    task_id=task_id,
                    status=TaskService.STATUS_SUCCESS,
                    platform_video_id=result.get('video_id'),
                    platform_video_url=result.get('video_url'),
                    publish_time=datetime.now()
                )
                
                # 更新账号使用统计
                self.account_service.update_account_usage(task['account_id'], success=True)
                
                # 记录到历史表
                self._record_to_history(
                    task_id=task_id,
                    task=task,
                    status=TaskService.STATUS_SUCCESS,
                    duration=duration,
                    platform_video_id=result.get('video_id'),
                    platform_video_url=result.get('video_url')
                )
                
                return {'success': True, 'duration': duration}
            else:
                # 任务失败
                error_message = result.get('error', '未知错误')
                raise Exception(error_message)
        
        except Exception as e:
            duration = int(time.time() - start_time)
            error_message = str(e)
            
            # 更新任务状态为失败
            self.task_service.update_task_status(
                task_id=task_id,
                status=TaskService.STATUS_FAILED,
                error_message=error_message
            )
            
            # 更新账号使用统计
            self.account_service.update_account_usage(task['account_id'], success=False)
            
            # 记录到历史表
            self._record_to_history(
                task_id=task_id,
                task=task,
                status=TaskService.STATUS_FAILED,
                duration=duration,
                error_message=error_message
            )
            
            return {'success': False, 'error': error_message, 'duration': duration}
    
    async def _execute_upload(
        self,
        platform_type: int,
        title: str,
        file_path: str,
        account_file: str,
        tags: list,
        publish_date,
        category: int = 0,
        product_link: str = '',
        product_title: str = '',
        thumbnail_path: str = '',
        is_draft: int = 0
    ) -> Dict:
        """
        执行上传（调用对应的平台上传器）
        
        Returns:
            {'success': True/False, 'video_id': str, 'video_url': str, 'error': str}
        """
        try:
            async with async_playwright() as playwright:
                if platform_type == 1:  # 小红书
                    app = XiaoHongShuVideo(title, file_path, tags, publish_date, account_file)
                elif platform_type == 2:  # 视频号
                    category_val = TencentZoneTypes.LIFESTYLE.value if category else None
                    app = TencentVideo(title, file_path, tags, publish_date, account_file, category_val, is_draft)
                elif platform_type == 3:  # 抖音
                    app = DouYinVideo(title, file_path, tags, publish_date, account_file, thumbnail_path, product_link, product_title)
                elif platform_type == 4:  # 快手
                    app = KSVideo(title, file_path, tags, publish_date, account_file)
                else:
                    return {'success': False, 'error': f'不支持的平台类型: {platform_type}'}
                
                # 执行上传
                await app.upload(playwright)
                
                # 返回成功（目前上传器没有返回视频ID和URL，后续可以增强）
                return {
                    'success': True,
                    'video_id': None,  # 后续可以从上传器获取
                    'video_url': None  # 后续可以从上传器获取
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def execute_with_retry(self, task_id: int, max_retries: int = 3) -> Dict:
        """
        带重试的任务执行
        
        Args:
            task_id: 任务ID
            max_retries: 最大重试次数
        
        Returns:
            执行结果
        """
        task = self.task_service.get_task(task_id)
        if not task:
            return {'success': False, 'error': '任务不存在'}
        
        # 重试间隔（秒）：1, 5, 30
        retry_delays = [1, 5, 30]
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                # 增加重试次数
                self.task_service.increment_retry_count(task_id)
                
                # 等待重试
                if attempt <= len(retry_delays):
                    delay = retry_delays[attempt - 1]
                    await asyncio.sleep(delay)
            
            result = await self.execute_task(task_id)
            
            if result['success']:
                return result
            
            # 如果是最后一次尝试，返回失败
            if attempt >= max_retries:
                return result
        
        return result
    
    def _record_to_history(
        self,
        task_id: int,
        task: Dict,
        status: int,
        duration: int,
        platform_video_id: str = None,
        platform_video_url: str = None,
        error_message: str = None
    ):
        """
        记录任务到历史表
        
        Args:
            task_id: 任务ID
            task: 任务信息
            status: 状态（2成功，3失败）
            duration: 执行耗时（秒）
            platform_video_id: 平台视频ID
            platform_video_url: 平台视频链接
            error_message: 错误信息
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取文件大小
            file_info = self._get_file_info(task['file_id'])
            file_size_mb = file_info['filesize'] if file_info else 0
            
            cursor.execute('''
                INSERT INTO publish_history (
                    task_id, platform_type, account_id, file_id, title, status,
                    platform_video_id, platform_video_url, error_message,
                    publish_time, duration_seconds, file_size_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id, task['platform_type'], task['account_id'], task['file_id'],
                task['title'], status, platform_video_id, platform_video_url,
                error_message, datetime.now(), duration, file_size_mb
            ))
            
            conn.commit()
        except Exception as e:
            print(f"记录历史失败: {e}")
        finally:
            conn.close()

