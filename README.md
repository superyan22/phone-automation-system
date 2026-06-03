# Web Phone Automation System

基于Web的手机自动化控制系统，支持远程控制多台手机设备。

## 🎉 MVP已完成

### 功能特性

- 🔍 **设备发现**：自动发现USB/WiFi连接的手机设备
- 📱 **实时投屏**：通过WebSocket实时显示手机屏幕
- 👆 **远程控制**：在网页上点击、滑动控制手机
- 📋 **任务管理**：创建、执行、监控自动化任务
- 🖼️ **模板系统**：HTML模板生成图片
- 📊 **执行日志**：详细记录每个步骤的执行情况

## 📁 项目结构

```
phone-automation-system/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/routes/        # API路由（设备、任务、WebSocket）
│   │   ├── core/              # 核心配置（数据库、设置）
│   │   ├── models/            # 数据模型（Device、Task）
│   │   └── services/          # 业务服务
│   │       ├── adb_manager.py       # ADB设备管理
│   │       ├── phone_controller.py  # 手机控制器
│   │       ├── task_executor.py     # 任务执行器
│   │       └── websocket_manager.py # WebSocket管理
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/        # 组件
│   │   │   └── device/       # 设备组件（ScreenMirror）
│   │   ├── pages/             # 页面
│   │   │   ├── Dashboard/    # 仪表盘
│   │   │   ├── Devices/      # 设备管理
│   │   │   └── Tasks/        # 任务管理
│   │   ├── services/          # 服务（API、WebSocket）
│   │   ├── store/             # 状态管理（Zustand）
│   │   └── types/             # TypeScript类型
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml          # Docker编排
├── docs/technical-design.md    # 技术文档
└── README.md
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd phone-automation-system
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码等
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- **前端界面**：http://localhost:3000
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 🛠️ 技术栈

### 后端
- Python 3.11
- FastAPI (异步Web框架)
- SQLAlchemy 2.0 (ORM)
- Celery + Redis (异步任务)
- asyncio (并发控制)

### 前端
- React 18 + TypeScript
- Zustand (状态管理)
- Socket.io (WebSocket)
- React Router (路由)
- Tailwind CSS (样式)

### 数据库
- PostgreSQL 15 (主数据库)
- Redis 7 (缓存+消息队列)

### 部署
- Docker + Docker Compose
- Nginx (反向代理)

## 📚 API接口

### 设备管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/devices | 获取设备列表 |
| GET | /api/v1/devices/{serial} | 获取设备详情 |
| POST | /api/v1/devices/scan | 扫描设备 |
| POST | /api/v1/devices/{serial}/connect | 连接设备 |
| POST | /api/v1/devices/{serial}/command | 执行命令 |

### 任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/tasks | 获取任务列表 |
| POST | /api/v1/tasks | 创建任务 |
| POST | /api/v1/tasks/{task_id}/start | 启动任务 |
| POST | /api/v1/tasks/{task_id}/pause | 暂停任务 |
| POST | /api/v1/tasks/{task_id}/cancel | 取消任务 |

### WebSocket

| 路径 | 描述 |
|------|------|
| /ws/device/{serial} | 设备实时控制 |
| /ws/task/{task_id} | 任务进度监控 |
| /ws/notifications | 全局通知 |

## 📊 开发进度

| Sprint | 内容 | 状态 |
|--------|------|------|
| Sprint 1 | 项目基础搭建 | ✅ 完成 |
| Sprint 2 | ADBManager核心开发 | ✅ 完成 |
| Sprint 3 | PhoneController核心开发 | ✅ 完成 |
| Sprint 4 | 前端界面开发 | ✅ 完成 |
| Sprint 5 | 集成测试与优化 | ✅ 完成 |

## 📝 文档

- [技术设计文档](docs/technical-design.md)
- [API文档](http://localhost:8000/docs)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
