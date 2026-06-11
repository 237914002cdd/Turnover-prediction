# Checkpoint v0.2.0 — 全量数据穿透版

**冻结时间**: 2026-06-10  
**Git Commit Hash**: `2fb7f0c40d6b029c1e9d5c27283306fedefc4357`  
**Git Tag**: `v0.2.0`

---

## 版本状态

| 维度 | 指标 |
|------|------|
| 数据库 | turnover.db — 1,470 条员工记录 |
| 后端 API | 7 端点全部 200 OK |
| 前端 | pages: OnaTopology + EmployeeDrillDown + Playbook Drawer |
| 初始拓扑 | 从前端 API 获取 Top 100 Hub 节点（294 条边） |
| 数据迁移 | 中文 Schema ETL 映射 + Eigenvector Centrality 全量计算 |

---

## 本次迭代核心变更（从 Mock → 数据库穿透）

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `api/services/db.py` | **新增** | SQLite 统一连接层（find_employee, get_top_hubs, get_neighbors） |
| `api/routers/diagnostic.py` | **重写** | 从 turnover.db 读取数据，动态拼装 39 维档案 + 8 项归因因子 |
| `api/routers/ona_hover.py` | **重写** | 从 DB 读取悬停详情，动态构建级联预测 |
| `api/routers/subgraph.py` | **重写** | 移除 12 人 Mock，新增 `GET /graph/topology`（Top 100 Hub） |
| `api/routers/roi_simulate.py` | **重写** | 从 DB 读月薪/风险等级，动态计算 α 和 ROI |
| `api/routers/playbook.py` | **重写** | 基于 DB 画像动态生成面谈剧本 |
| `frontend/src/components/OnaTopology.jsx` | **重构** | 初始加载改为 fetch `localhost:8000/api/v1/ona/graph/topology` |
| `api/utils/run_final_migration.py` | **新增** | 1470 条全量迁移脚本 |
| `docs/ona-openapi-v1.md` | **新增** | OpenAPI 第三方集成规范 |
| `calibration_sandbox.py` | **新增** | 算法校准沙箱（4/4 断言通过） |
| `turnover.db` | **新增** | SQLite 数据库（已在 .gitignore 中排除） |

---

## 回退命令

```bash
git reset --hard v0.2.0
```
