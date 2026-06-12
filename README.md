# 组织网络分析（ONA）与留任决策模拟平台

**员工离职风险预测与管理平台** — 全栈原型（v0.3.0 · Demo-Ready）

从原始 HR 数据清洗到白盒化归因诊断，从 ROI 财务沙盘到 LLM 定制面谈剧本，提供完整的 **人机协同（Human-in-the-loop）离职风险预测与干预闭环**。

---

## 全栈架构

```
[HR 数据/CSV] → Data Cleaning Pipeline → 数仓(employee_static, ONA元数据)
                                              ↓
                                     ROI & ONA 计算引擎
                                              ↓
                   ┌─── 全局仪表盘(Top100 + 替换损失大屏)
                   ├─── ONA 拓扑图(G6 力导向 · 焦点聚焦模式)
                   ├─── 个体下钻诊断页(核心不满驱动因子矩阵 + ROI滑块)
                   ├─── 干预状态机(NEW→IN_PROGRESS→RESOLVED/FP)
                   └─── LLM 面谈剧本生成(Playbook Drawer)
```

## 项目规模

| 层 | 语言 | 行数 |
|----|------|------|
| 后端 (API + 模型 + 路由 + 服务) | Python | 1,917 |
| 前端 (React + G6 拓扑 + 下钻组件) | JSX / JS | 1,546 |
| 算法引擎 (特征工程 + 清洗 + ROI) | Python | 739 |
| 数据库 DDL (数仓 + 状态机 + 索引) | SQL | 417 |
| 文档 (白皮书 + 数据字典 + 部署手册) | Markdown | 1,035 |
| **总计** | | **5,903** |

## 快速冷启动

```bash
# 后端
cd api && pip install -r ../requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend && npm install
npm run dev -- --port 5175
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/employee/diagnostic/{id}` | 39 字段档案 + 归因矩阵 |
| `GET` | `/api/v1/ona/graph/topology` | 全局拓扑图（Top 100 Hub） |
| `GET` | `/api/v1/ona/graph/subgraph` | Ego Network 子图 |
| `POST` | `/api/v1/ona/node/hover_details` | 节点悬停详情 150ms |
| `POST` | `/api/v1/ona/intervention/create` | 创建干预（状态机） |
| `POST` | `/api/v1/roi/simulate` | ROI 实时模拟测算 |
| `POST` | `/api/v1/ona/playbook/generate` | LLM 面谈剧本生成 |
| `POST` | `/api/v1/ona/graph/upload` | CSV/Excel 批量导入员工数据 |
| `GET` | `/api/v1/ona/report/{id}` | 导出留任建议书 PDF |

## 核心数学模型

- **综合风险排序**: `Score = P_base × Centrality_ONA × W_perf`
- **调薪后离职率**: `P_new = P_base × e^(-α × X)`
- **净节约金额**: `Net_Savings = Pre_Cost - Post_Cost - Invest_Cost`

## 项目结构

```
turnover-prediction/
├── api/                     # FastAPI 后端（6 routers, 10 endpoints）
│   ├── routers/             # diagnostic, onahover, playbook, roi, subgraph
│   ├── models/ona_models.py # Pydantic 数据模型（含业务翻译层字段）
│   ├── services/            # db.py（SQLite 连接）+ interpretation.py（业务翻译）
│   └── main.py
├── frontend/                # React + Vite + AntV G6
│   ├── src/components/      # OnaTopology（焦点聚焦）+ EmployeeDrillDown（ROI沙盘）
│   ├── src/api/ona.js       # Axios 网络层
│   ├── src/mock/            # employeeRegistry.js（统一数据源）
│   └── package.json
├── python/                  # 算法引擎
│   ├── build_ona_feature_engineering_pipeline.py  # 6 维特征工程
│   ├── data_cleaning_pipeline.py                  # 4 步清洗管道
│   └── roi_ona_engine.py                          # ROI 测算 + 风险等级
├── sql/                     # PostgreSQL DDL
│   ├── 001_ddl_schema.sql
│   ├── 002_intervention_state_machine.sql
│   └── 003_performance_indices.sql
├── docs/                     # 文档（11 份 · 1,611 行）
│   ├── product/              # 产品文档（3 份）
│   │   ├── cho_demo_script.md       # CHO 演示脚本
│   │   ├── competitive_analysis.md # 竞品分析报告
│   │   └── product_roadmap.md       # 产品路线图
│   ├── product_business_logic_whitepaper.md   # 算法白皮书
│   ├── data_pipeline_and_dictionary_spec.md   # 数据字典
│   ├── deployment_and_operations_manual.md    # 部署手册
│   ├── architecture-white-paper.md
│   ├── checkpoint_v0.2.0_manifest.md
│   ├── checkpoint_v0.3.0_manifest.md
│   ├── frontend-hover-spec.md
│   └── ona-openapi-v1.md
├── calibration_sandbox.py   # 校准沙箱（4/4 断言通过）
└── requirements.txt
```

## Git 版本历史

```
c1bc582 fix: preserve focus mode on mouseleave
a313f9c feat: default focus mode (SHEN_HASH 1-degree neighbors)
7108b19 fix: HR terminology replacement
f235416 refactor: unified EMPLOYEE_REGISTRY, ROI formulas, reactive top bar
7903845 docs: product whitepaper, data dictionary, deployment manual
2fb7f0c release: v0.2.0 - full data pipeline + sqlite integration
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, Pydantic, Pandas, Uvicorn
- **前端**: React 18, Vite, G6 (AntV), Axios, Lodash
- **数据库**: PostgreSQL (DDL + Recursive CTE) / SQLite (dev)
- **算法**: SHAP 归因, 指数衰减模型, 3σ Winsorization
