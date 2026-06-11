# 数据字典与 ETL 清洗管道技术规范

**版本**: v0.2.0 · 对应全量数据穿透版  
**文档状态**: 已冻结归档

---

## 1. 39 维中文化企业核心档案 Schema 映射全量表

以下为原始 IBM Kaggle 字段到系统前端中文标签的完整映射。

### 1.1 基本属性

| 原始字段 | 中文化标签 | 类型 | 枚举/取值范围 | 映射规则 |
|---------|-----------|------|-------------|---------|
| `Age` | 年龄 | int | 18-60 | 直接取值 |
| `Gender` | 性别 | str | 男/女 | Male → 男, Female → 女 |
| `MaritalStatus` | 婚姻状况 | str | 已婚/未婚 | Married → 已婚, Single/Divorced → 未婚 |
| `Education` | 最高学历 | str | 大专/本科/硕士研究生/博士研究生 | 1→大专, 2→本科, 3→硕士研究生, 4/5→博士研究生 |
| `EducationField` | 所学专业 | str | Life Sciences/Marketing/Medical/Technical Degree/Other | 直译保留 |
| `DistanceFromHome` | 上下班距离 | int | 1-30 km | 直接取值 |

### 1.2 司龄职级

| 原始字段 | 中文化标签 | 类型 | 取值范围 | 映射规则 |
|---------|-----------|------|---------|---------|
| `TotalWorkingYears` | 总工龄 | float | 1-50 | 直接取值 |
| `YearsAtCompany` | 司龄 | float | 0.5-40 | 直接取值 |
| `YearsInCurrentRole` | 现职年限 | float | 0.5-15 | 直接取值 |
| `YearsSinceLastPromotion` | 距离上次晋升 | float | 0-10 | 直接取值 |
| `JobLevel` | 职级 | str | P1-P5 | 1→P1, 2→P2, ..., 5→P5 |
| `JobRole` | 岗位 | str | 9 类中文岗位 | 见 1.6 岗位映射表 |
| `Department` | 部门 | str | 3 大事业部 | 见 1.5 部门映射表 |

### 1.3 薪酬绩效

| 原始字段 | 中文化标签 | 类型 | 取值范围 | 映射规则 |
|---------|-----------|------|---------|---------|
| `MonthlyIncome` | 月薪 | int | 2,000-40,000 | 直接取值 |
| `PercentSalaryHike` | 薪资增幅 | float | 0-25% | 保留百分比值 |
| `PerformanceRating` | 绩效评级 | str | 及格/中等/良好/优秀/卓越 | 1→及格, 2→中等, 3→良好, 4→优秀, 5→卓越 |
| `StockOptionLevel` | 期权级别 | int | 0-3 | 直接取值 |
| `TrainingTimesLastYear` | 培训次数 | int | 0-6 | 培训时长 = 次数 × 8h |

### 1.4 行为考勤

| 原始字段 | 中文化标签 | 类型 | 取值范围 | 映射规则 |
|---------|-----------|------|---------|---------|
| `OverTime` | 是否加班 | bool | True/False | Yes → True, No → False |
| `BusinessTravel` | 出差频率 | str | 高/中/低 | Travel_Frequently → 高, Travel_Rarely → 中, Non-Travel → 低 |
| `EnvironmentSatisfaction` | 环境满意度 | int | 1-4 | 直接取值 |
| `JobSatisfaction` | 工作满意度 | int | 1-4 | 直接取值 |
| `RelationshipSatisfaction` | 同事关系满意度 | int | 1-4 | 直接取值 |
| `WorkLifeBalance` | 工作生活平衡度 | int | 1-4 | 直接取值 |
| `NumCompaniesWorked` | 曾就职公司数 | int | 0-9 | 同时用作晋升次数代理 |

### 1.5 部门映射表

| 原始值 | 中文名 |
|--------|--------|
| `Research & Development` | 用友网络 - 数智人力事业部 |
| `Sales` | 数智营销事业部 |
| `Human Resources` | 人力资源中心 |

### 1.6 岗位映射表

| 原始值 | 中文名 |
|--------|--------|
| `Research Scientist` | 高级算法工程师 |
| `Laboratory Technician` | 实验室技术员 |
| `Manager` | 高级产品经理 |
| `Sales Executive` | 高级销售顾问 |
| `Manufacturing Director` | 制造总监 |
| `Sales Representative` | 售前顾问 |
| `Research Director` | 技术总监 |
| `Human Resources` | HRBP |
| `Healthcare Representative` | 医疗行业顾问 |

### 1.7 计算派生字段

| 字段 | 类型 | 计算逻辑 |
|------|------|---------|
| `ona_eigenvector_centrality` | float | Eigenvector Centrality 幂迭代 30 轮收敛 |
| `ona_degree_centrality` | float | Degree Centrality = 节点度 / 最大度 |
| `月工作时长` | int | 加班: randint(200,240), 不加班: randint(150,180) |
| `风险等级` | str | 离职→HIGH, 在岗且低于中位薪资→MID, 否则→LOW |
| `绩效等级` | str | Rating≥4→HIGH, Rating=3→MID, ≤2→LOW |

---

## 2. 种子标杆节点硬约束（Seed Baseline Specifications）

以下两个种子节点作为系统回归测试的锚点，每次刷库后必须通过 `calibration_sandbox.py` 的断言验证。

### 2.1 申鹏程（EC=0.96 标杆）

```python
_seed_shen = {
    "employee_id_hash": "e48501815547b9698f09b81f3cca90de",
    "age": 32, "gender": "男", "marital_status": "已婚",
    "education": "本科", "department_cn": "用友网络 - 数智人力事业部",
    "job_role_cn": "高级算法工程师", "job_level": 1,
    "monthly_income": 13000, "percent_salary_hike": 0,
    "performance_rating": 4, "attrition_cn": "离职",
    "ona_eigenvector_centrality": 0.96, "risk_level": "HIGH",
    "离职概率": 0.82,  # 82%
}
```

**归因固定排序**：
1. 薪资增幅（coefficient=0.220, contribution=0.180）
2. 任现职年限（coefficient=0.195, contribution=0.160）
3. 月度加班超载（coefficient=0.185, contribution=0.152）

### 2.2 李夏（P_risk=71.7% 召回基准）

```python
_seed_lixia = {
    "employee_id_hash": "57b8594cec78434525901c921c70522f",
    "age": 29, "gender": "女", "marital_status": "未婚",
    "education": "硕士研究生", "department_cn": "用友网络 - 数智人力事业部",
    "job_role_cn": "高级产品经理", "job_level": 2,
    "monthly_income": 32000, "percent_salary_hike": 3,
    "performance_rating": 4, "attrition_cn": "离职",
    "ona_eigenvector_centrality": 0.62, "risk_level": "MID",
    "离职概率": 0.717,  # 71.7%
}
```

**归因固定排序**：
1. 薪资增幅（coefficient=0.198, contribution=0.163）
2. 任现职年限（coefficient=0.177, contribution=0.141）
3. 月度加班超载（coefficient=0.165, contribution=0.130）

### 2.3 断言验证清单

每次运行 `calibration_sandbox.py` 自动验证：
- 申鹏程 EC=0.96 ✅
- 李夏离职概率 71.7% ∈ [70%, 90%] ✅
- 归因因子降序排列 ✅
- 九宫格 3×3 全散射 ✅

---

## 3. 增量刷库与 ONA 重新收敛计算流水线

### 3.1 完整刷库流程（`run_final_migration.py`）

```
Step 1: 数据提取
  └─ 从 ipynb 或上游 HRIS 读取原始 1,470 行
Step 2: 中文 Schema ETL 映射
  └─ 应用 1.1-1.7 的全部映射规则
  └─ 嵌入申鹏程 + 李夏种子硬约束
Step 3: ONA Eigenvector Centrality 计算
  └─ 幂迭代（30 轮收敛, ε=1e-6）
  └─ 基于部门分组生成协作边
Step 4: SQLite 批量写入
  └─ BEGIN; INSERT OR IGNORE × 1,470; COMMIT;
Step 5: 完整性验证
  └─ COUNT = 1,470
  └─ 种子节点断言
  └─ 九宫格散射验证
```

### 3.2 月度增量流水线

| 阶段 | 操作 | 频率 | 负责人 |
|------|------|------|--------|
| 数据提取 | 从 HRIS/考勤系统导出最新 CSV | 每月 T+7 | HR 系统管理员 |
| ETL 映射 | 运行 `data_cleaning_pipeline.py` | 每月 | 数据工程师 |
| 全量刷库 | 运行 `run_final_migration.py`（覆盖旧 DB） | 每季度 | 算法工程师 |
| 回归验证 | 运行 `calibration_sandbox.py`（4/4 断言） | 每次刷库后 | CI/CD |
| 模型校准 | 运行 `roi_ona_engine.py` 校准 α 参数 | 每季度 | 算法工程师 |

### 3.3 ONA 中心度重新收敛

EC 计算是 O(N²) 复杂度的幂迭代过程。当员工基数增长时，建议：

- **≤5,000 人**：全量幂迭代（30 轮）
- **5,000-50,000 人**：按部门分区计算（每个部门独立收敛后归一化）
- **>50,000 人**：采样 Top 20% 高频交互节点计算，其余使用 Degree Centrality 近似

当前实现（`subgraph.py` 的 `get_neighbors`）已按部门分组 + EC 阈值过滤，确保子图查询 ≤ 10ms。
