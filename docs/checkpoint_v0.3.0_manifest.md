# Checkpoint v0.3.0 — Demo-Ready Milestone

**冻结时间**: 2026-06-11  
**Git Tag**: `v0.3.0`  
**前一个版本**: `v0.2.0`

---

## 版本状态

| 维度 | 指标 |
|------|------|
| 项目规模 | 53 个源文件 / 6,334 行代码 |
| API 端点 | 10 个（全部 200 OK） |
| 数据库 | turnover.db — 1,470 条员工记录 |
| 前端构建 | 0 errors / 0 warnings |
| 运行时 | 0 console errors |
| 代码基线 | Git 10 commits |

---

## v0.3.0 增量变更

### 新增功能
- **焦点聚焦模式** — 拓扑图默认高亮申鹏程及其一阶邻接，其余淡化，点击按钮切换全量视图
- **CSV/Excel 批量导入** — `POST /api/v1/ona/graph/upload`，自动中文化映射 + 38 字段写入
- **PDF 留任建议书** — `GET /api/v1/ona/report/{id}`，含 SHAP 因子表 + ROI 测算 + 级联风险
- **前端上传弹窗** — 拖拽区、进度指示、结果反馈

### 架构改进
- **HR 术语替换**: 中心度→组织核心影响力、SHAP→核心不满驱动因子、震荡指数→骨干离职辐射圈、多米诺级联→潜在团队流失放大效应
- **统一员工注册表**: `employeeRegistry.js` 取代散落各处硬编码
- **ROI 公式 PRD 对齐**: `PreCost - PostCost - Investment = NetSavings` 三层计算
- **mouseleave 回归修复**: 焦点模式下移出节点不再破坏背景淡化

### 清理工作
- 删除 6 个无引用文件：`assets/` 下 3 个 Vite 默认图标、`App.css`、`public/icons.svg`、`mock_ona_hover.py`
- 代码量从 6,656 降至 6,334 行

---

## 当前 API 端点

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

---

## 回退命令

```bash
git reset --hard v0.3.0
```
