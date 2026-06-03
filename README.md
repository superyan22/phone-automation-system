# Web Phone Automation System

基于Web的手机自动化控制系统，支持远程控制多台手机设备。

## 功能特性

- 🔍 **设备发现**：自动发现USB/WiFi连接的手机设备
- 📱 **实时投屏**：通过WebSocket实时显示手机屏幕
- 👆 **远程控制**：在网页上点击、滑动控制手机
- 📋 **任务管理**：创建、执行、监控自动化任务
- 🖼️ **模板系统**：HTML模板生成图片
- 📊 **执行日志**：详细记录每个步骤的执行情况

## 技术栈

- **后端**：Python 3.11 + FastAPI + SQLAlchemy + Celery
- **前端**：React 18 + TypeScript + Zustand + Socket.io
- **数据库**：PostgreSQL 15 + Redis 7
- **部署**：Docker + Nginx

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/phone-automation-system.git
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
- **pgAdmin**：http://localhost:5050 (debug模式)

## 开发环境

### 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

## 项目结构

```
phone-automation-system/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务服务
│   │   └── utils/             # 工具函数
│   ├── tests/                 # 测试代码
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── hooks/             # 自定义Hook
│   │   ├── store/             # 状态管理
│   │   ├── services/          # API服务
│   │   ├── pages/             # 页面
│   │   └── types/             # TypeScript类型
│   └── Dockerfile
├── docker/                     # Docker配置
├── docs/                       # 文档
├── scripts/                    # 脚本
├── docker-compose.yml
└── README.md
```

## API接口

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

## 部署

### 生产环境

```bash
# 使用生产配置启动
docker-compose --profile production up -d

# 启动Nginx反向代理
docker-compose --profile production up nginx -d
```

### 备份数据

```bash
# 运行备份脚本
./scripts/backup.sh
```

## 文档

- [技术设计文档](docs/technical-design.md)
- [API文档](http://localhost:8000/docs)

## 许可证

MIT License
