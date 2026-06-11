# 组织网络分析（ONA）与留任决策模拟平台
## 全栈核心技术白皮书与项目归档标准（v1.0）

---

## 一、系统架构与闭环数据流转

本平台实现了从原始异构 HR 数据输入，到白盒化风险诊断，再到财务 ROI 沙盘模拟与人工反馈的完整人机协同（Human-in-the-loop）闭环。整个系统的权责链路与数据拓扑如下：

```
[多源 HR 数据/API/CSV]
       │
       ▼
[Data Cleaning Pipeline] ──(DQ 逻辑不合规)──> [DQ_Anomaly 隔离表]
       │
       ├─► 1. 中位数动态填充 / 行为数据自动补零
       ├─► 2. 3σ Winsorization 异常截断
       ▼
[核心数仓表 schema.sql] ──► (employee_static / comp_perf_history / ONA元数据)
       │
       ▼
[ROI & ONA 计算引擎] ──► (重算基础离职率 × ONA中心度放大 × 绩效权重)
       │
       ├─► 全局仪表盘: Top 100 高危列表 & 替换损失大屏
       ├─► ONA 拓扑图谱: 异步弹窗 API (150ms 响应、SHAP 因子、级联流失树)
       ▼
[个体下钻 ROI 决策模拟器] ──► (HR 拖动调薪滑块) ──► 实时重算 P_new & Net_Savings
       │
       ▼ (点击确认执行)
[干预状态机变更] ──► (NEW → IN_PROGRESS) ──► 开启 30 天防打扰沉默期
       │
       ▼ (干预周期结束)
[人工标注结果归档] ──► (feedback_history 表) ──► 动态演进特征池，回测重训模型
```

---

## 二、核心数学模型与算法公式集

### 1. 综合风险排序评分模型（Risk Priority Scoring）

$$\text{Score} = P_{\text{base}} \times \text{Centrality}_{\text{ONA}} \times W_{\text{perf}}$$

- $P_{\text{base}}$: 基础机器学习模型输出的个体离职概率
- $\text{Centrality}_{\text{ONA}}$: 非正式互动日志计算得出的特征向量中心度放大系数
- $W_{\text{perf}}$: 绩效权重，确保高绩效 Hub 节点触发 RED 特级预警

### 2. 白盒化归因模型（SHAP Local Explanation）

$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i$$

- $\phi_0$: 全局基准离职概率
- $\phi_i$: 针对特定员工的第 $i$ 个特征的局部 SHAP 贡献值

### 3. 留任决策财务模拟模型（ROI Sandbox Engine）

**调薪后离职率指数衰减：**
$$P_{\text{new}} = P_{\text{base}} \times e^{-\alpha \cdot X}$$

**企业即期现金投入：**
$$\text{Cost}_{\text{invest}} = \text{Current\_Salary} \times X \times 12$$

**预期替换损失挽回收益：**
$$\text{Benefit} = (P_{\text{base}} - P_{\text{new}}) \times \text{Replacement\_Cost}$$

**净节约金额（Net Savings）财务决策判定：**
$$\text{Net\_Savings} = \text{Benefit} - \text{Cost}_{\text{invest}}$$

若 $\text{Net\_Savings} > 0$ → 绿色【⭐ 优选执行决策】
若 $\text{Net\_Savings} \le 0$ → 黄色【建议调和：财务性价比低】

---

## 三、全栈工程资产清单

### 后端与算法引擎

| 文件 | 说明 |
|------|------|
| `sql/001_ddl_schema.sql` | 4 张标准数仓表：employee_static / comp_perf_history / behavioral_dynamics / ona_interaction_log |
| `python/data_cleaning_pipeline.py` | 4 步清洗：DQ拦截 → GroupBy中位数填充 → 行为类补零 → 3σ截断 |
| `python/roi_ona_engine.py` | ROI测算引擎 + 风险等级判定 + Playbook匹配（员工A验证：净节约 2,520元 ✅） |

### API 与状态机

| 文件 | 说明 |
|------|------|
| `api/models/ona_models.py` | Pydantic 模型，含完整类型约束与脱敏注释 |
| `api/routers/ona_hover.py` | `POST /api/v1/ona/node/hover_details`（150ms 响应） |
| `api/mock/mock_ona_hover.py` | 后端 Mock 数据服务 |
| `sql/002_intervention_state_machine.sql` | 状态机 DDL + 触发器 (NEW→IN_PROGRESS→RESOLVED/FP/TURNOVER) |

### 前端交互原型

| 文件 | 说明 |
|------|------|
| `frontend/src/components/OnaTopology.jsx` | G6 gForce 力导向拓扑图 + 200ms防抖悬停弹窗 |
| `frontend/src/components/EmployeeDrillDown.jsx` | 双栏下钻：SHAP归因全景 + ROI滑块模拟器 |
| `frontend/src/mock/mockData.js` | 本地 Mock 降级数据层 |
| `frontend/src/App.jsx` | 平滑视图路由：拓扑 ↔ 下钻 |

### 文档

| 文件 | 说明 |
|------|------|
| `docs/frontend-hover-spec.md` | 前端渲染规范：UI映射、交互行为、性能约束 |
| `docs/architecture-white-paper.md` | 本白皮书 |

---

## 四、快速冷启动

```bash
# 后端 API
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端原型
cd ../frontend
npm install
npm run dev -- --port 5175
```

---

## 五、Demo 演示脚本（CHO 汇报话术）

1. **宏观唤醒**：展示顶部大屏 — "当前高风险核心人才总期望替换损失 ¥284,500"
2. **网络锁定**：ONA 拓扑中定位红色高危 Hub 节点"员工-申鹏程"
3. **悬停诊断**：150ms 弹窗展示 SHAP 归因（薪资涨幅停滞）+ 级联预警（2.4x 倍率）
4. **沙盘推演**：下钻页面拖动滑块 0%→12%，离职率 82%→15%，Net Savings=¥2,520
5. **闭环执行**：决策印章 ⭐ 优选执行决策 → 确认干预 → 状态机 IN_PROGRESS

---

**归档状态：SUCCESS · 2026-06-09 · v1.0**
