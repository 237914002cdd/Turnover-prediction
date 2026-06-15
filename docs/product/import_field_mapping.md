# 员工数据导入 - 必填字段中英文对照表

**说明**: 下载的 Excel 模板包含两行表头：第 1 行为中文引导（供您对照填写），第 2 行为英文列名（供系统自动解析）。
您只需在第 3 行起填入数据，无需关注英文列名。

### 模板结构预览

```
┌──────┬──────┬──────────┬──────────┬──────┬──────────────┬──────┬──────┐
│ 年龄 │ 状态 │ 出差频率 │ 部门     │ 学历 │ 专业         │ 性别 │ 职级 │  ← 中文引导行
├──────┼──────┼──────────┼──────────┼──────┼──────────────┼──────┼──────┤
│ 35   │ No   │ Trav...  │ Res...   │  4   │Computer Sc.. │ Male │  3   │  ← 从这行开始填数据
└──────┴──────┴──────────┴──────────┴──────┴──────────────┴──────┴──────┘
```

### 字段对照表

| 第1行中文引导 | 第2行英文列名 | 填写格式 | 示例值 | 可选值 / 备注 |
|-------------|-------------|---------|--------|-------------|
| 年龄 | `Age` | 整数 | `35` | 18 – 70 |
| 状态 | `Attrition` | 枚举 | `No` | `No` 在岗 · `Yes` 已离职 |
| 出差频率 | `BusinessTravel` | 枚举 | `Travel_Frequently` | `Travel_Frequently` 频繁 · `Travel_Rarely` 偶尔 · `Non-Travel` 不出差 |
| 部门 | `Department` | 枚举/文本 | `Research & Development` | `Research & Development` → 数智人力事业部 · `Sales` → 数智营销事业部 · `Human Resources` → 人力资源中心；直接填中文也保留 |
| 学历 | `Education` | 整数 | `4` | 1=高中 · 2=大专 · 3=本科 · 4=硕士 · 5=博士 |
| 专业 | `EducationField` | 文本 | `Computer Science` | 直接填写即可 |
| 性别 | `Gender` | 枚举 | `Male` | `Male` 男 · `Female` 女 |
| 职级 | `JobLevel` | 整数 | `3` | 1=P1–P3 · 2=P4–P5 · 3=P6–P7 · 4=P8–P9 · 5=P10+ |
| 岗位 | `JobRole` | 枚举/文本 | `Research Scientist` | `Research Scientist` → 高级算法工程师 · `Laboratory Technician` → 实验室技术员 · `Manager` → 高级产品经理 · `Sales Executive` → 高级销售顾问 · `Manufacturing Director` → 制造总监 · `Sales Representative` → 售前顾问 · `Research Director` → 技术总监 · `Human Resources` → HRBP · `Healthcare Representative` → 医疗行业顾问；直接填中文也保留 |
| 婚姻 | `MaritalStatus` | 枚举 | `Married` | `Married` 已婚 · `Single` 未婚 · `Divorced` 离异 |
| 月薪(元) | `MonthlyIncome` | 整数 | `32000` | 税前月薪 |
| 常加班? | `OverTime` | 枚举 | `No` | `No` 不常加班 · `Yes` 经常加班 |
| 涨薪% | `PercentSalaryHike` | 整数 | `15` | 如 15 表示涨薪 15% |
| 绩效 | `PerformanceRating` | 整数 | `4` | 1=不及格 · 2=中等 · 3=良好 · 4=优秀 · 5=卓越 |
| 总工龄 | `TotalWorkingYears` | 小数 | `12` | 可带小数 |
| 本公司工龄 | `YearsAtCompany` | 小数 | `6` | 可带小数 |
| 现岗年限 | `YearsInCurrentRole` | 小数 | `4` | 可带小数 |
| 距晋升年数 | `YearsSinceLastPromotion` | 整数 | `3` | — |

## 常见问题

**Q: 第1行中文行可以删掉吗？**
A: 不可以。第2行英文列名是系统解析用的，但第1行必须保留（系统自动跳过第1行）。删除第1行会导致系统将中文行当作数据解析而报错。

**Q: 部门/岗位可以直接填中文吗？**
A: 可以。系统优先匹配内置映射表，没有匹配的会原样保留。例如填「产研中心」→ 入库后就是「产研中心」。

**Q: 有空值会怎样？**
A: 该行会跳过并被计入错误计数，不影响其他行。

**Q: 可以批量上传重复数据吗？**
A: 系统自动去重，重复上传的数据会覆盖更新。
