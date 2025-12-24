#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键启动器 - 社交平台自动上传工具
自动检测环境、安装依赖、配置管理、启动服务
"""
import os
import sys
import subprocess
import webbrowser
import time
import json
import shutil
import threading
import socket
from pathlib import Path
from tkinter import Tk, Label, Button, Text, Scrollbar, ttk, messagebox
import tkinter as tk

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("社交平台自动上传工具 - 启动器")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 基础路径
        self.base_dir = Path(__file__).parent.resolve()
        self.config_file = self.base_dir / "launcher_config.json"
        
        # 检测结果
        self.python_path = None
        self.nodejs_available = False
        self.chrome_path = None
        self.backend_process = None
        self.frontend_process = None
        
        # 创建GUI
        self.create_gui()
        
        # 加载配置
        self.load_config()
        
        # 开始检测
        self.start_checking()
    
    def create_gui(self):
        """创建GUI界面"""
        # 标题
        title_label = Label(
            self.root,
            text="社交平台自动上传工具",
            font=("Microsoft YaHei", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.root,
            variable=self.progress_var,
            maximum=100,
            length=550,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)
        
        # 状态标签
        self.status_label = Label(
            self.root,
            text="正在初始化...",
            font=("Microsoft YaHei", 10),
            fg="blue"
        )
        self.status_label.pack(pady=5)
        
        # 日志区域
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = Text(
            log_frame,
            height=15,
            width=70,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9),
            wrap=tk.WORD
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # 按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.start_button = Button(
            button_frame,
            text="启动服务",
            command=self.start_services,
            font=("Microsoft YaHei", 10),
            bg="#4CAF50",
            fg="white",
            width=12,
            height=2,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = Button(
            button_frame,
            text="取消",
            command=self.cancel,
            font=("Microsoft YaHei", 10),
            bg="#f44336",
            fg="white",
            width=12,
            height=2
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
    
    def log(self, message, status="info"):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        if status == "success":
            prefix = "✓"
            color = "green"
        elif status == "error":
            prefix = "✗"
            color = "red"
        elif status == "warning":
            prefix = "⚠"
            color = "orange"
        else:
            prefix = "•"
            color = "black"
        
        log_message = f"[{timestamp}] {prefix} {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_status(self, message):
        """更新状态标签"""
        self.status_label.config(text=message)
        self.root.update()
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        self.root.update()
    
    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def check_python(self):
        """检测Python环境"""
        self.update_status("正在检测Python环境...")
        self.update_progress(10)
        self.log("正在检测Python环境...")
        
        # 尝试使用当前Python
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                self.python_path = sys.executable
                self.log(f"检测到 Python {version.major}.{version.minor}.{version.micro}", "success")
                return True
        except:
            pass
        
        # 尝试从PATH查找
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.python_path = "python"
                self.log(f"检测到 {result.stdout.strip()}", "success")
                return True
        except:
            pass
        
        self.log("未检测到Python 3.8+，请先安装Python", "error")
        return False
    
    def check_nodejs(self):
        """检测Node.js环境"""
        self.update_status("正在检测Node.js环境...")
        self.update_progress(20)
        self.log("正在检测Node.js环境...")
        
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.nodejs_available = True
                self.log(f"检测到 npm {result.stdout.strip()}", "success")
                return True
        except:
            pass
        
        self.log("未检测到Node.js，将使用生产模式（无需前端开发服务器）", "warning")
        self.nodejs_available = False
        return True  # Node.js不是必需的
    
    def check_chrome(self):
        """检测Chrome浏览器"""
        self.update_status("正在检测Chrome浏览器...")
        self.update_progress(30)
        self.log("正在检测Chrome浏览器...")
        
        # 从配置中读取
        if "chrome_path" in self.config and os.path.exists(self.config["chrome_path"]):
            self.chrome_path = self.config["chrome_path"]
            self.log(f"使用配置的Chrome路径: {self.chrome_path}", "success")
            return True
        
        # 常见安装位置
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                self.chrome_path = path
                self.config["chrome_path"] = path
                self.save_config()
                self.log(f"检测到Chrome: {path}", "success")
                return True
        
        self.log("未检测到Chrome，将使用Playwright内置浏览器", "warning")
        return True  # Chrome不是必需的
    
    def create_directories(self):
        """创建必要文件夹"""
        self.update_status("正在创建必要文件夹...")
        self.update_progress(40)
        self.log("正在创建必要文件夹...")
        
        dirs = [
            self.base_dir / "cookiesFile",
            self.base_dir / "videoFile",
            self.base_dir / "db",
        ]
        
        for dir_path in dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"创建文件夹: {dir_path.name}", "success")
            except Exception as e:
                self.log(f"创建文件夹失败 {dir_path.name}: {e}", "error")
                return False
        
        return True
    
    def init_database(self):
        """初始化数据库"""
        self.update_status("正在初始化数据库...")
        self.update_progress(50)
        self.log("正在初始化数据库...")
        
        db_file = self.base_dir / "db" / "database.db"
        if db_file.exists():
            self.log("数据库已存在，跳过初始化", "success")
            return True
        
        try:
            # 导入数据库初始化函数
            import sys
            db_path = str(self.base_dir / "db")
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from createTable import init_database
            
            success, message = init_database()
            if success:
                self.log(message, "success")
                return True
            else:
                self.log(message, "error")
                return False
        except ImportError:
            # 如果导入失败，尝试直接运行脚本
            try:
                old_cwd = os.getcwd()
                os.chdir(self.base_dir / "db")
                
                result = subprocess.run(
                    [self.python_path, "createTable.py"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                os.chdir(old_cwd)
                
                if result.returncode == 0:
                    self.log("数据库初始化成功", "success")
                    return True
                else:
                    self.log(f"数据库初始化失败: {result.stderr}", "error")
                    return False
            except Exception as e:
                os.chdir(old_cwd) if 'old_cwd' in locals() else None
                self.log(f"数据库初始化异常: {e}", "error")
                return False
        except Exception as e:
            self.log(f"数据库初始化异常: {e}", "error")
            return False
    
    def update_config_file(self):
        """更新配置文件"""
        self.update_status("正在更新配置文件...")
        self.update_progress(60)
        self.log("正在更新配置文件...")
        
        conf_file = self.base_dir / "conf.py"
        conf_example = self.base_dir / "conf.example.py"
        
        # 如果配置文件不存在，从示例复制
        if not conf_file.exists() and conf_example.exists():
            try:
                shutil.copy(conf_example, conf_file)
                self.log("已创建配置文件", "success")
            except Exception as e:
                self.log(f"创建配置文件失败: {e}", "error")
                return False
        
        # 更新Chrome路径
        if conf_file.exists() and self.chrome_path:
            try:
                content = conf_file.read_text(encoding='utf-8')
                if 'LOCAL_CHROME_PATH = ""' in content:
                    content = content.replace(
                        'LOCAL_CHROME_PATH = ""',
                        f'LOCAL_CHROME_PATH = r"{self.chrome_path}"'
                    )
                    conf_file.write_text(content, encoding='utf-8')
                    self.log("已更新Chrome路径配置", "success")
            except Exception as e:
                self.log(f"更新配置文件失败: {e}", "warning")
        
        return True
    
    def check_dependencies(self):
        """检查Python依赖"""
        self.update_status("正在检查Python依赖...")
        self.update_progress(70)
        self.log("正在检查Python依赖...")
        
        requirements_file = self.base_dir / "requirements.txt"
        if not requirements_file.exists():
            self.log("未找到requirements.txt", "warning")
            return True
        
        # 检查关键依赖
        key_packages = ["flask", "playwright", "requests"]
        missing_packages = []
        
        for package in key_packages:
            try:
                result = subprocess.run(
                    [self.python_path, "-m", "pip", "show", package],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    missing_packages.append(package)
            except:
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"缺少依赖: {', '.join(missing_packages)}", "warning")
            self.log("是否现在安装？这可能需要几分钟...", "info")
            return self.install_dependencies()
        else:
            self.log("Python依赖检查通过", "success")
            return True
    
    def install_dependencies(self):
        """安装Python依赖"""
        self.update_status("正在安装Python依赖...")
        self.log("正在安装Python依赖（这可能需要几分钟）...", "info")
        
        requirements_file = self.base_dir / "requirements.txt"
        try:
            # 使用清华镜像源加速
            cmd = [
                self.python_path, "-m", "pip", "install",
                "-r", str(requirements_file),
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in process.stdout:
                if "Successfully installed" in line or "Requirement already satisfied" in line:
                    self.log(line.strip(), "success")
                self.root.update()
            
            process.wait()
            
            if process.returncode == 0:
                self.log("Python依赖安装完成", "success")
                return True
            else:
                self.log("Python依赖安装失败，但将继续启动", "warning")
                return True  # 允许继续
        except Exception as e:
            self.log(f"安装依赖异常: {e}", "warning")
            return True  # 允许继续
    
    def install_playwright(self):
        """安装Playwright驱动"""
        self.update_status("正在安装Playwright驱动...")
        self.update_progress(80)
        self.log("正在安装Playwright浏览器驱动...")
        
        try:
            result = subprocess.run(
                [self.python_path, "-m", "playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                self.log("Playwright驱动安装完成", "success")
                return True
            else:
                self.log("Playwright驱动安装失败，但将继续启动", "warning")
                return True  # 允许继续
        except Exception as e:
            self.log(f"安装Playwright驱动异常: {e}", "warning")
            return True  # 允许继续
    
    def check_port(self, port):
        """检查端口是否被占用"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0  # 0表示端口被占用
        except:
            return True
    
    def start_backend(self):
        """启动后端服务"""
        self.update_status("正在启动后端服务...")
        self.update_progress(90)
        self.log("正在启动后端服务...")
        
        # 检查端口
        if not self.check_port(5409):
            self.log("端口5409已被占用，请关闭占用该端口的程序", "error")
            return False
        
        backend_script = self.base_dir / "sau_backend.py"
        if not backend_script.exists():
            self.log("未找到sau_backend.py", "error")
            return False
        
        try:
            # 在后台启动后端
            self.backend_process = subprocess.Popen(
                [self.python_path, str(backend_script)],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # 等待服务启动
            self.log("等待后端服务启动...", "info")
            for i in range(30):  # 最多等待30秒
                time.sleep(1)
                # 检查端口是否可连接
                if not self.check_port(5409):
                    # 端口被占用，说明服务可能已启动
                    try:
                        import urllib.request
                        response = urllib.request.urlopen("http://localhost:5409", timeout=2)
                        if response.getcode() == 200:
                            self.log("后端服务启动成功", "success")
                            return True
                    except:
                        pass
                if i % 5 == 0:
                    self.log(f"等待中... ({i+1}/30秒)", "info")
            
            self.log("后端服务启动超时，但可能已启动", "warning")
            return True  # 允许继续
        except Exception as e:
            self.log(f"启动后端服务失败: {e}", "error")
            return False
    
    def start_frontend_dev(self):
        """启动前端开发服务器（如果Node.js可用）"""
        if not self.nodejs_available:
            return True
        
        self.update_status("正在启动前端开发服务器...")
        self.log("正在启动前端开发服务器...")
        
        frontend_dir = self.base_dir / "sau_frontend"
        if not frontend_dir.exists():
            self.log("未找到前端目录，跳过前端启动", "warning")
            return True
        
        # 检查端口
        if not self.check_port(5173):
            self.log("端口5173已被占用，跳过前端开发服务器", "warning")
            return True
        
        try:
            # 检查是否已安装前端依赖
            node_modules = frontend_dir / "node_modules"
            if not node_modules.exists():
                self.log("正在安装前端依赖...", "info")
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    self.log("前端依赖安装失败，跳过前端启动", "warning")
                    return True
            
            # 启动前端开发服务器
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            self.log("前端开发服务器启动中...", "info")
            time.sleep(3)  # 等待启动
            self.log("前端开发服务器已启动", "success")
            return True
        except Exception as e:
            self.log(f"启动前端开发服务器失败: {e}", "warning")
            return True  # 允许继续
    
    def open_browser(self):
        """打开浏览器"""
        self.update_status("正在打开浏览器...")
        self.update_progress(100)
        self.log("正在打开浏览器...")
        
        time.sleep(2)  # 等待服务完全启动
        
        # 根据是否有前端开发服务器选择URL
        if self.nodejs_available and self.frontend_process:
            url = "http://localhost:5173"
        else:
            url = "http://localhost:5409"
        
        try:
            webbrowser.open(url)
            self.log(f"已打开浏览器: {url}", "success")
        except Exception as e:
            self.log(f"打开浏览器失败: {e}", "warning")
    
    def start_checking(self):
        """开始检测流程"""
        def check_thread():
            try:
                # 1. 检测Python
                if not self.check_python():
                    self.log("Python环境检测失败，无法继续", "error")
                    messagebox.showerror("错误", "未检测到Python环境，请先安装Python 3.8+")
                    return
                
                # 2. 检测Node.js
                self.check_nodejs()
                
                # 3. 检测Chrome
                self.check_chrome()
                
                # 4. 创建文件夹
                if not self.create_directories():
                    self.log("创建文件夹失败", "error")
                    return
                
                # 5. 初始化数据库
                if not self.init_database():
                    self.log("数据库初始化失败，但将继续", "warning")
                
                # 6. 更新配置文件
                self.update_config_file()
                
                # 7. 检查依赖
                self.check_dependencies()
                
                # 8. 安装Playwright
                self.install_playwright()
                
                # 完成检测
                self.update_status("检测完成，可以启动服务")
                self.log("=" * 50, "info")
                self.log("检测完成！点击'启动服务'按钮开始使用", "success")
                self.start_button.config(state=tk.NORMAL)
                
            except Exception as e:
                self.log(f"检测过程出错: {e}", "error")
                messagebox.showerror("错误", f"检测过程出错: {e}")
        
        # 在后台线程中执行检测
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def start_services(self):
        """启动所有服务"""
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.DISABLED)
        
        def start_thread():
            try:
                # 启动后端
                if not self.start_backend():
                    messagebox.showerror("错误", "后端服务启动失败")
                    self.start_button.config(state=tk.NORMAL)
                    self.cancel_button.config(state=tk.NORMAL)
                    return
                
                # 启动前端（如果可用）
                self.start_frontend_dev()
                
                # 打开浏览器
                self.open_browser()
                
                # 完成
                self.update_status("服务已启动，正在运行...")
                self.log("=" * 50, "info")
                self.log("所有服务已启动！", "success")
                self.log("关闭此窗口将停止所有服务", "info")
                
                # 修改按钮
                self.start_button.config(text="服务运行中", state=tk.DISABLED)
                self.cancel_button.config(text="停止服务", state=tk.NORMAL, command=self.stop_services)
                
            except Exception as e:
                self.log(f"启动服务失败: {e}", "error")
                messagebox.showerror("错误", f"启动服务失败: {e}")
                self.start_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=start_thread, daemon=True)
        thread.start()
    
    def stop_services(self):
        """停止所有服务"""
        self.log("正在停止服务...", "info")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.log("前端服务已停止", "success")
            except:
                pass
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.log("后端服务已停止", "success")
            except:
                pass
        
        self.root.quit()
    
    def cancel(self):
        """取消并退出"""
        if messagebox.askokcancel("确认", "确定要退出吗？"):
            self.stop_services()


def main():
    """主函数"""
    root = Tk()
    app = LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

