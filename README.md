# 组织网络分析（ONA）与留任决策模拟平台

**员工离职风险预测与管理平台** — 全栈原型（Master PRD V4.0）

从原始 HR 数据清洗到白盒化归因诊断，从 ROI 财务沙盘到 LLM 定制面谈剧本，提供完整的 **人机协同（Human-in-the-loop）离职风险预测与干预闭环**。

---

## 全栈架构

```
[HR 数据/CSV] → Data Cleaning Pipeline → 数仓(employee_static, ONA元数据)
                                              ↓
                                     ROI & ONA 计算引擎
                                              ↓
                   ┌─── 全局仪表盘(Top100 + 替换损失大屏)
                   ├─── ONA 拓扑图(G6 力导向 · 悬停150ms)
                   ├─── 个体下钻诊断页(39字段归因矩阵 + ROI滑块)
                   ├─── 干预状态机(NEW→IN_PROGRESS→RESOLVED/FP)
                   └─── LLM 面谈剧本生成(Playbook Drawer)
```

## 快速冷启动

### 后端（FastAPI）

```bash
cd api
pip install -r ../requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 前端（React + Vite）

```bash
cd frontend
npm install
npm run dev -- --port 5175
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/employee/diagnostic/{id}` | 39字段档案 + 归因矩阵 |
| `GET` | `/api/v1/ona/graph/subgraph` | Ego Network 子图(BFS) |
| `POST` | `/api/v1/ona/node/hover_details` | 节点悬停详情(150ms) |
| `POST` | `/api/v1/ona/intervention/create` | 创建干预(状态机) |
| `POST` | `/api/v1/roi/simulate` | ROI 实时模拟测算 |
| `POST` | `/api/v1/ona/playbook/generate` | LLM 面谈剧本生成 |

## 核心数学模型

- **综合风险排序**: `Score = P_base × Centrality_ONA × W_perf`
- **调薪后离职率**: `P_new = P_base × e^(-α × X)`
- **净节约金额**: `Net_Savings = Benefit - Cost_invest`

## 项目结构

```
turnover-prediction/
├── api/            # FastAPI 后端
│   ├── models/     # Pydantic 数据模型
│   ├── routers/    # API 路由(7个端点)
│   ├── mock/       # Mock 数据服务
│   └── main.py     # 应用入口
├── frontend/       # React + Vite 前端
│   ├── src/
│   │   ├── api/        # Axios 网络层
│   │   ├── components/ # ONA拓扑 + 下钻诊断 + Playbook
│   │   └── mock/       # 本地降级数据
│   └── package.json
├── python/         # 算法引擎
│   ├── build_ona_feature_engineering_pipeline.py  # 6维特征工程管道
│   ├── data_cleaning_pipeline.py                  # 4步清洗管道
│   └── roi_ona_engine.py                          # ROI测算 + 风险等级
├── sql/            # PostgreSQL DDL
│   ├── 001_ddl_schema.sql
│   ├── 002_intervention_state_machine.sql
│   └── 003_performance_indices.sql
└── docs/           # 架构文档
    ├── architecture-white-paper.md
    ├── frontend-hover-spec.md
    └── ona-openapi-v1.md                         # OpenAPI 第三方集成规范
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, Pydantic, Pandas, Uvicorn
- **前端**: React 18, Vite, G6 (AntV), Axios, Lodash
- **数据库**: PostgreSQL (DDL + Recursive CTE)
- **算法**: SHAP 归因, 指数衰减模型, 3σ Winsorization
