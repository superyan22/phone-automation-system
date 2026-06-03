# Web手机自动化控制系统 - 技术设计文档

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户浏览器                                │
│                    (React + TypeScript)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    Nginx反向代理    │
                    │   (WebSocket代理)   │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  FastAPI后端   │    │   PostgreSQL  │    │     Redis     │
│  (8000端口)    │    │   (数据库)     │    │   (缓存+队列)  │
└───────┬───────┘    └───────────────┘    └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                     ADBManager                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 设备发现     │  │ 连接池管理   │  │ 心跳监控     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    PhoneController                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 截屏管理     │  │ 坐标映射     │  │ 输入管理     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ┌─────────────┐  ┌─────────────┐         │
│                   │   手机1     │  │   手机2     │  ...    │
│                   └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

**后端：**
- Python 3.11
- FastAPI (异步Web框架)
- SQLAlchemy 2.0 (ORM)
- Celery + Redis (异步任务)
- asyncio (并发控制)

**前端：**
- React 18 + TypeScript
- Zustand (状态管理)
- Socket.io (WebSocket)
- React Router (路由)
- Tailwind CSS (样式)

**数据库：**
- PostgreSQL 15 (主数据库)
- Redis 7 (缓存+消息队列)

**部署：**
- Docker + Docker Compose
- Nginx (反向代理)
- Prometheus + Grafana (监控)

---

## 2. 数据库设计

### 2.1 设备表 (devices)

```sql
CREATE TABLE devices (
    id              SERIAL PRIMARY KEY,
    serial          VARCHAR(100) UNIQUE NOT NULL,
    device_type     VARCHAR(20) NOT NULL CHECK (device_type IN ('usb', 'wifi')),
    ip_address      VARCHAR(50),
    port            INTEGER DEFAULT 5555,
    
    -- 设备信息
    model           VARCHAR(100),
    brand           VARCHAR(50),
    android_version VARCHAR(20),
    screen_width    INTEGER,
    screen_height   INTEGER,
    screen_density  FLOAT DEFAULT 1.0,
    
    -- 状态
    status          VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'busy', 'error')),
    is_connected    BOOLEAN DEFAULT FALSE,
    last_heartbeat  TIMESTAMP WITH TIME ZONE,
    
    -- 配置
    config          JSONB DEFAULT '{}',
    
    -- 时间戳
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    connected_at    TIMESTAMP WITH TIME ZONE
);
```

### 2.2 任务表 (tasks)

```sql
CREATE TABLE tasks (
    id              SERIAL PRIMARY KEY,
    task_id         VARCHAR(50) UNIQUE NOT NULL DEFAULT uuid_generate_v4()::VARCHAR,
    
    -- 任务信息
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    task_type       VARCHAR(50) NOT NULL CHECK (task_type IN ('automation', 'batch', 'test', 'template')),
    
    -- 状态
    status          VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'paused', 'completed', 'failed', 'cancelled')),
    priority        INTEGER DEFAULT 0 CHECK (priority >= 0 AND priority <= 10),
    progress        INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- 配置
    steps           JSONB NOT NULL DEFAULT '[]',
    params          JSONB DEFAULT '{}',
    config          JSONB DEFAULT '{}',
    
    -- 执行信息
    device_serial   VARCHAR(100) REFERENCES devices(serial) ON DELETE SET NULL,
    current_step    INTEGER DEFAULT 0,
    retry_count     INTEGER DEFAULT 0,
    max_retries     INTEGER DEFAULT 3,
    
    -- 结果
    result          JSONB,
    error_message   TEXT,
    
    -- 调度
    scheduled_at    TIMESTAMP WITH TIME ZONE,
    timeout_seconds INTEGER DEFAULT 3600,
    
    -- 时间戳
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE
);
```

### 2.3 任务日志表 (task_logs)

```sql
CREATE TABLE task_logs (
    id              SERIAL PRIMARY KEY,
    task_id         VARCHAR(50) NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    
    -- 日志信息
    level           VARCHAR(20) DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warning', 'error', 'critical')),
    step_index      INTEGER,
    step_name       VARCHAR(100),
    
    -- 内容
    message         TEXT NOT NULL,
    details         JSONB,
    
    -- 截图
    screenshot_path VARCHAR(500),
    screenshot_url  VARCHAR(500),
    
    -- 性能
    duration_ms     INTEGER,
    
    -- 时间戳
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 图片模板表 (image_templates)

```sql
CREATE TABLE image_templates (
    id              SERIAL PRIMARY KEY,
    template_id     VARCHAR(50) UNIQUE NOT NULL DEFAULT uuid_generate_v4()::VARCHAR,
    
    -- 模板信息
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    category        VARCHAR(50),
    
    -- 模板内容
    html_template   TEXT NOT NULL,
    css_styles      TEXT,
    default_params  JSONB DEFAULT '{}',
    
    -- 渲染配置
    width           INTEGER DEFAULT 1080,
    height          INTEGER DEFAULT 1920,
    format          VARCHAR(20) DEFAULT 'png' CHECK (format IN ('png', 'jpg', 'webp')),
    quality         INTEGER DEFAULT 90 CHECK (quality >= 1 AND quality <= 100),
    
    -- 预览
    preview_url     VARCHAR(500),
    thumbnail_url   VARCHAR(500),
    
    -- 状态
    is_active       BOOLEAN DEFAULT TRUE,
    version         INTEGER DEFAULT 1,
    
    -- 时间戳
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100)
);
```

---

## 3. API接口设计

### 3.1 设备管理API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/devices | 获取设备列表 |
| GET | /api/v1/devices/{serial} | 获取设备详情 |
| POST | /api/v1/devices/scan | 扫描设备 |
| POST | /api/v1/devices/{serial}/connect | 连接设备 |
| POST | /api/v1/devices/{serial}/disconnect | 断开设备 |
| POST | /api/v1/devices/{serial}/command | 执行命令 |
| GET | /api/v1/devices/{serial}/screenshot | 获取截图 |

### 3.2 任务管理API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/tasks | 获取任务列表 |
| GET | /api/v1/tasks/{task_id} | 获取任务详情 |
| POST | /api/v1/tasks | 创建任务 |
| PUT | /api/v1/tasks/{task_id} | 更新任务 |
| DELETE | /api/v1/tasks/{task_id} | 删除任务 |
| POST | /api/v1/tasks/{task_id}/start | 启动任务 |
| POST | /api/v1/tasks/{task_id}/pause | 暂停任务 |
| POST | /api/v1/tasks/{task_id}/resume | 恢复任务 |
| POST | /api/v1/tasks/{task_id}/cancel | 取消任务 |
| GET | /api/v1/tasks/{task_id}/logs | 获取任务日志 |

### 3.3 WebSocket接口

| 路径 | 描述 |
|------|------|
| /ws/device/{serial} | 设备实时控制 |
| /ws/task/{task_id} | 任务进度监控 |
| /ws/notifications | 全局通知 |

**消息格式：**

```json
// 客户端 -> 服务端
{
  "type": "tap",
  "params": {"x": 0.5, "y": 0.5}
}

// 服务端 -> 客户端
{
  "type": "screenshot",
  "data": {"image": "base64...", "timestamp": 1234567890}
}
```

---

## 4. 核心模块设计

### 4.1 ADBManager模块

**职责：**
- 设备发现（USB/WiFi）
- 连接池管理
- 断线重连
- 心跳检测

**关键类：**
- `DeviceDiscovery` - 设备发现
- `ConnectionPool` - 连接池
- `ReconnectionManager` - 断线重连
- `HeartbeatMonitor` - 心跳监控
- `ADBManager` - 主管理器

### 4.2 PhoneController模块

**职责：**
- 截屏管理（screencap/scrcpy）
- 坐标映射（相对/绝对）
- 输入管理（中文支持）
- 批量操作

**关键类：**
- `ScreenshotManager` - 截屏管理
- `CoordinateMapper` - 坐标映射
- `InputMethodManager` - 输入管理
- `BatchExecutor` - 批量执行
- `PhoneController` - 主控制器

### 4.3 TaskExecutor模块

**职责：**
- 任务调度
- 步骤执行
- 错误处理
- 进度上报

---

## 5. 前端设计

### 5.1 页面结构

```
/dashboard          # 仪表盘
/devices            # 设备列表
/devices/:serial    # 设备详情+控制
/tasks              # 任务列表
/tasks/create       # 创建任务
/tasks/:task_id     # 任务详情+日志
/templates          # 模板列表
/templates/editor   # 模板编辑器
```

### 5.2 核心组件

- `ScreenMirror` - 屏幕镜像（WebSocket实时流）
- `TouchOverlay` - 触摸覆盖层（点击/滑动）
- `StepEditor` - 步骤编辑器（拖拽排序）
- `TaskLogViewer` - 任务日志查看器

### 5.3 状态管理（Zustand）

```typescript
// 设备状态
interface DeviceState {
  devices: Device[];
  selectedDevice: Device | null;
  fetchDevices: () => Promise<void>;
  connectDevice: (serial: string) => Promise<void>;
}

// 任务状态
interface TaskState {
  tasks: Task[];
  selectedTask: Task | null;
  fetchTasks: () => Promise<void>;
  createTask: (params: TaskCreateParams) => Promise<Task>;
}
```

---

## 6. Docker部署

### 6.1 服务组件

| 服务 | 端口 | 描述 |
|------|------|------|
| backend | 8000 | FastAPI后端 |
| frontend | 80 | React前端 |
| postgres | 5432 | PostgreSQL数据库 |
| redis | 6379 | Redis缓存 |
| celery-worker | - | 异步任务执行器 |
| pgadmin | 5050 | 数据库管理（调试） |

### 6.2 数据持久化

```
data/
├── postgres/       # PostgreSQL数据
├── redis/          # Redis数据
├── uploads/        # 用户上传
├── screenshots/    # 截图存储
├── logs/           # 应用日志
└── backups/        # 数据库备份
```

---

## 7. 开发计划

### Phase 1（MVP）- 8-10周

| Sprint | 时间 | 内容 |
|--------|------|------|
| Sprint 1 | 第1-2周 | 项目基础、框架搭建 |
| Sprint 2 | 第3-4周 | ADBManager核心 |
| Sprint 3 | 第5-6周 | PhoneController核心 |
| Sprint 4 | 第7-8周 | 前端界面开发 |
| Sprint 5 | 第9-10周 | 集成测试、优化 |

### 里程碑

1. **M1（第2周末）**：项目骨架完成，Docker环境可用
2. **M2（第4周末）**：ADBManager完成，可连接设备
3. **M3（第6周末）**：PhoneController完成，可执行操作
4. **M4（第8周末）**：前端界面完成，基本功能可用
5. **M5（第10周末）**：MVP发布，可对外演示

---

## 8. 技术风险

| 风险 | 影响 | 应对策略 |
|------|------|----------|
| scrcpy Web集成复杂 | 高 | MVP用screencap，后期升级scrcpy |
| 多设备并发性能 | 中 | Celery分布式任务队列 |
| 中文输入兼容性 | 中 | ADB Keyboard + 剪贴板双方案 |
| 跨平台ADB连接 | 低 | Docker内安装android-tools-adb |

---

*文档版本：v1.0*
*创建时间：2026-06-03*
*作者：MasterAgent + TRAE*
