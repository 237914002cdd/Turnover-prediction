# 系统环境复制与一键部署操作手册

**版本**: v0.2.0 · 对应全量数据穿透版  
**文档状态**: 已冻结归档

---

## 1. 全栈双端沙箱运行流水线依赖顺序

### 1.1 前置依赖

| 组件 | 版本要求 | 安装命令 |
|------|---------|---------|
| Python | ≥ 3.10 | python.org |
| Node.js | ≥ 18 | nodejs.org |
| npm | ≥ 9 | 随 Node.js 安装 |

### 1.2 后端环境搭建

```bash
# 1. 克隆项目
cd D:\claude code mode\files
git clone <repo-url> turnover-prediction
# 或直接进入已有目录
cd turnover-prediction

# 2. 创建虚拟环境（可选但推荐）
python -m venv venv
.\venv\Scripts\activate

# 3. 安装 Python 依赖
pip install -r requirements.txt
```

**`requirements.txt` 包含**：

```
fastapi>=0.110.0
uvicorn>=0.29.0
pydantic>=2.5.0
pandas>=2.0.0
numpy>=1.24.0
```

### 1.3 前端依赖安装

```bash
cd frontend
npm install
```

**核心依赖**：
- `@antv/g6@^4.8.25` — ONA 拓扑图渲染引擎
- `react@^19.2.6` + `react-dom@^19.2.6` — UI 框架
- `axios@^1.17.0` — HTTP 客户端
- `lodash@^4.18.1` — 防抖工具

### 1.4 数据库初始化

```bash
# 运行全量迁移脚本（生成 turnover.db）
python api/utils/run_final_migration.py

# 预期输出:
#   迁移完成: 1470 条记录已写入 turnover.db
```

### 1.5 启动后端（FastAPI）

```bash
# 从项目根目录执行
cd D:\claude code mode\files\turnover-prediction

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 预期输出:
#   Uvicorn running on http://0.0.0.0:8000

# 验证:
#   curl http://localhost:8000/health
#   → {"status":"ok","service":"turnover-prediction-api","version":"0.2.0"}
```

### 1.6 启动前端（Vite + React）

```bash
# 新终端窗口
cd D:\claude code mode\files\turnover-prediction\frontend

npx vite --port 5175 --host

# 预期输出:
#   VITE ready in xxx ms
#   Local: http://localhost:5175/
```

### 1.7 依赖顺序总览

```
1. pip install -r requirements.txt
       ↓
2. cd frontend && npm install
       ↓
3. python api/utils/run_final_migration.py
       ↓
4. uvicorn api.main:app (后端 8000)
       ↓
5. npx vite (前端 5175)
       ↓
6. 浏览器打开 http://localhost:5175
```

---

## 2. 灰度测试与完整性断言验证（Sanity Check Plan）

### 2.1 10 行灰度验证（不污染生产 DB）

在完整刷库前，用 `test_10_rows_migration.py` 验证数据管道完整性：

```bash
# 仅处理 10 行数据，验证中文化映射
py -3 api/utils/test_10_rows_migration.py

# 验证内容:
#   ✓ 离职状态 = 离职/在岗（无拼音残留）
#   ✓ 部门中文化（用友网络 - 数智人力事业部 / 数智营销事业部）
#   ✓ 月工作时长 = int
#   ✓ 输出 CSV 在 api/mock/test_10_rows.csv
```

### 2.2 校准沙箱全量验证

每次完整刷库后执行：

```bash
py -3 calibration_sandbox.py
```

**4 项断言检查清单**：

| 步骤 | 验证项 | 通过条件 |
|------|--------|---------|
| 1.1 | 特征工程管道 | Shape=(1470,17), EC 归一化, P90 > P50×2 |
| 2.1 | 李夏种子对齐 | P=71.7%±1%, Risk=ORANGE, Top3 顺序正确 |
| 3.1 | 多重干预仿真 | 复合干预 P < 15%, Net Savings > 0 |
| 4.1 | 飞书卡片 OpenAPI | msg_type=interactive, 2 actions |

**输出示例**：

```
测试总数: 4
通过:     4
通过率:   100%
```

### 2.3 API 端点手动验证

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. ONA 悬停详情
curl -X POST http://localhost:8000/api/v1/ona/node/hover_details \
  -H "Content-Type: application/json" \
  -d '{"employee_id_hash":"<hash>"}'

# 3. 员工诊断
curl http://localhost:8000/api/v1/employee/diagnostic/<hash>

# 4. ROI 模拟
curl -X POST http://localhost:8000/api/v1/roi/simulate \
  -H "Content-Type: application/json" \
  -d '{"employee_id_hash":"<hash>","salary_increase_pct":0.12}'

# 5. 子图
curl "http://localhost:8000/api/v1/ona/graph/subgraph?center_employee_id_hash=<hash>&depth=2"

# 6. 全局拓扑
curl http://localhost:8000/api/v1/ona/graph/topology

# 7. Playbook
curl -X POST http://localhost:8000/api/v1/ona/playbook/generate \
  -H "Content-Type: application/json" \
  -d '{"employee_id_hash":"<hash>"}'

# 8. 干预创建
curl -X POST http://localhost:8000/api/v1/ona/intervention/create \
  -H "Content-Type: application/json" \
  -d '{"employee_id_hash":"<hash>","proposed_salary_increase":0.12}'
```

**全部预期返回 `200 OK`**。

### 2.4 常见问题排查

| 症状 | 原因 | 解决 |
|------|------|------|
| 前端空白 / 加载中 | Vite 端口被占用 | `pkill -f vite` 后重试 |
| 后端 8000 端口被占用 | 旧 uvicorn 进程残留 | `taskkill //F //PID <pid>` |
| API 返回 404 | 路由未注册 | 确认 `api/main.py` 中 `include_router` |
| 数据库查询为空 | turnover.db 不存在或路径错误 | 运行 `run_final_migration.py` |
| 前端控制台 fetch error | 后端未启动或 CORS 问题 | 确认后端在 8000 运行，CORS `allow_origins=["*"]` |
| G6 画布不渲染 | 容器尺寸为 0 | 浏览器窗口大小变化触发 resize |

---

## 3. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.2.0 | 2026-06-10 | 全量数据穿透版：5 路由接入 SQLite，前端加载 Top 100 Hub |
| v0.1.0 | 2026-06-09 | Mock 原型版：所有路由返回硬编码数据 |
