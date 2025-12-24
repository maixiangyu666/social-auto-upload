# 一键启动器使用说明

## 快速开始

### Windows 用户

1. 双击 `start.bat` 文件
2. 等待启动器自动检测和配置
3. 点击"启动服务"按钮
4. 浏览器会自动打开，开始使用！

### 其他系统

运行以下命令：
```bash
python launcher.py
```

## 启动器功能

启动器会自动完成以下操作：

1. **环境检测**
   - 检测 Python 3.8+ 是否安装
   - 检测 Node.js 是否可用（可选，用于前端开发模式）
   - 自动查找 Chrome 浏览器路径

2. **自动配置**
   - 创建必要文件夹（cookiesFile、videoFile、db）
   - 从 conf.example.py 生成 conf.py
   - 自动填充 Chrome 路径到配置文件
   - 初始化 SQLite 数据库

3. **依赖安装**
   - 检查并安装 Python 依赖包
   - 安装 Playwright 浏览器驱动
   - （可选）安装前端依赖（如果检测到 Node.js）

4. **服务启动**
   - 启动后端服务（端口 5409）
   - 启动前端开发服务器（端口 5173，如果 Node.js 可用）
   - 自动打开浏览器访问服务

## 使用模式

### 开发模式（推荐开发者）

- 需要安装 Node.js
- 前端使用 Vite 开发服务器
- 支持热重载，方便开发调试
- 访问地址：http://localhost:5173

### 生产模式（推荐普通用户）

- 不需要 Node.js
- 前端已构建并集成到后端
- 访问地址：http://localhost:5409

启动器会自动检测 Node.js，如果可用则使用开发模式，否则使用生产模式。

## 常见问题

### Q: 启动器提示"未检测到Python"
A: 请先安装 Python 3.8 或更高版本，下载地址：https://www.python.org/downloads/
   安装时记得勾选 "Add Python to PATH"

### Q: 依赖安装失败
A: 可以尝试：
   - 检查网络连接
   - 使用代理或VPN
   - 手动运行：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

### Q: 端口被占用
A: 关闭占用 5409 或 5173 端口的其他程序，或修改配置文件中的端口设置

### Q: Chrome 未检测到
A: 不影响使用，系统会使用 Playwright 内置的浏览器。如需使用本地 Chrome，请手动在 conf.py 中配置路径。

### Q: 服务启动失败
A: 查看启动器日志区域的错误信息，常见原因：
   - 端口被占用
   - 依赖未正确安装
   - 配置文件错误

## 停止服务

在启动器窗口中点击"停止服务"按钮，或直接关闭启动器窗口。

## 配置文件

启动器会在项目根目录创建 `launcher_config.json`，保存以下配置：
- Chrome 浏览器路径
- 其他用户偏好设置

可以手动编辑此文件来修改配置。

