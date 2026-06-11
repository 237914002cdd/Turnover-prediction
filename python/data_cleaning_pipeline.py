"""
员工离职风险预测与管理平台 —— 数据清洗与异常治理 Pipeline
================================================================
依据: Master PRD V4.0 第六章第二节《数据清洗、治理与异常截断规则》

功能:
  1. 数值类缺失值 -> GroupBy(部门, 职级) 中位数填充
  2. 行为类缺失值 -> 补零
  3. 3σ Winsorization 截断 -> 对 Overtime_Hours 等离群值做上边界拉回
  4. 逻辑矛盾拦截(DQ) -> 年龄-司龄<16 / 调薪幅度<-100% 等打入隔离区

用法:
  from data_cleaning_pipeline import build_pipeline
  df_clean, df_quarantine = build_pipeline(df_raw, dept_col, level_col)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# 常量 / 配置
# ---------------------------------------------------------------------------
# 行为类特征列表 —— 缺失时默认补零
BEHAVIORAL_FEATURES = [
    "Overtime_Hours",
    "Leave_Frequency",
    "Attendance_Anomaly",
]

# 数值类特征列表 —— 缺失时使用 GroupBy 中位数填充
NUMERIC_FEATURES = [
    "Performance_Score",
    "Target_Completion_Rate",
    "Monthly_Income",
    "Salary_Increase_Pct",
]

# 逻辑矛盾拦截规则
DQ_RULES = {
    "age_minus_tenure_lt_16": (
        "年龄(Age) - 司龄(Tenure_Years) < 16 → 逻辑不可能(16岁前无法全职工作)"
    ),
    "salary_increase_below_minus_100": (
        "调薪幅度(Salary_Increase_Pct) < -100% → 薪资不可能降为负数"
    ),
    "hire_date_in_future": (
        "入职日期 > 当前日期 → 未来数据错误"
    ),
}


def winsorize_3sigma(
    series: pd.Series,
    lower: bool = False,
    upper: bool = True,
) -> pd.Series:
    """
    3σ (Winsorization) 截断函数。

    PRD 规定：
      系统强制运行三倍标准差（3σ）校验，对超出上边界的极端离群值
      执行截断拉回，将其强制修正为 μ + 3σ 的边界值。

    Parameters
    ----------
    series : pd.Series
        待处理的数值列。
    lower : bool
        是否截断下边界（默认 False，PRD 只要求上边界）。
    upper : bool
        是否截断上边界（默认 True）。

    Returns
    -------
    pd.Series
        截断后的列。
    """
    mu = series.mean()
    sigma = series.std(ddof=0)

    if sigma == 0 or pd.isna(sigma):
        return series  # 无波动时跳过，避免除零

    result = series.copy(deep=True)

    if upper:
        upper_bound = mu + 3.0 * sigma
        result[result > upper_bound] = upper_bound

    if lower:
        lower_bound = mu - 3.0 * sigma
        result[result < lower_bound] = lower_bound

    return result


def detect_dq_violations(df: pd.DataFrame) -> pd.DataFrame:
    """
    数据逻辑矛盾检测（DQ 引擎）。

    依据 PRD 第六章第二节：
      - 年龄 - 司龄 < 16  → 逻辑不可能
      - 调薪幅度 < -100%  → 数据错误
      - 入职日期 > 当前日期 → 未来数据

    Parameters
    ----------
    df : pd.DataFrame
        原始数据。

    Returns
    -------
    pd.DataFrame
        包含违例行索引、违例规则、描述的 DataFrame。
    """
    violations = []

    # 规则 1: 年龄 - 司龄 < 16
    if "Age" in df.columns and "Tenure_Years" in df.columns:
        mask = (df["Age"] - df["Tenure_Years"]) < 16
        for idx in df.index[mask]:
            violations.append({
                "row_index": idx,
                "rule": "age_minus_tenure_lt_16",
                "description": DQ_RULES["age_minus_tenure_lt_16"],
                "employee_id": df.loc[idx, "Employee_ID"]
                               if "Employee_ID" in df.columns else None,
            })

    # 规则 2: 调薪幅度 < -100%
    if "Salary_Increase_Pct" in df.columns:
        mask = df["Salary_Increase_Pct"] < -1.0  # -100%
        for idx in df.index[mask]:
            violations.append({
                "row_index": idx,
                "rule": "salary_increase_below_minus_100",
                "description": DQ_RULES["salary_increase_below_minus_100"],
                "employee_id": df.loc[idx, "Employee_ID"]
                               if "Employee_ID" in df.columns else None,
            })

    return pd.DataFrame(violations)


def build_pipeline(
    df: pd.DataFrame,
    dept_col: str = "Department",
    level_col: str = "Job_Level",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    通用数据预处理流水线（Pipeline）。

    Pipeline 步骤:
      1. 逻辑矛盾检测 → 隔离脏数据
      2. 数值类缺失值 → GroupBy(部门+职级) 中位数填充
      3. 行为类缺失值 → 补零
      4. 3σ Winsorization 截断 → Overtime_Hours 等

    Parameters
    ----------
    df : pd.DataFrame
        包含员工属性的原始数据框。必须含 Employee_ID（用于追踪隔离）。
    dept_col : str
        部门列名（用于 GroupBy 分组）。
    level_col : str
        职级列名（用于 GroupBy 分组）。

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        (clean_data, quarantined_data)
        - clean_data: 通过 DQ 检验且清洗完毕的数据
        - quarantined_data: 触发 DQ 报警被隔离的数据
    """
    df = df.copy()

    # -------------------------------------------------------------------
    # Step 1: DQ 逻辑矛盾拦截
    # -------------------------------------------------------------------
    dq_report = detect_dq_violations(df)
    violated_indices = set(dq_report["row_index"].unique())
    clean_idx = [i for i in df.index if i not in violated_indices]
    quarantine_idx = list(violated_indices)

    df_clean: pd.DataFrame = df.loc[clean_idx].copy()
    df_quarantine: pd.DataFrame = df.loc[quarantine_idx].copy() if quarantine_idx else pd.DataFrame()

    # -------------------------------------------------------------------
    # Step 2: 数值类缺失值 → GroupBy(部门, 职级) 中位数填充
    # -------------------------------------------------------------------
    for col in NUMERIC_FEATURES:
        if col not in df_clean.columns:
            continue
        # 按部门+职级分组计算中位数，并填充
        df_clean[col] = df_clean.groupby([dept_col, level_col])[col].transform(
            lambda g: g.fillna(g.median())
        )
        # 如果分组后仍有空（孤立的组全为 NaN），再用全局中位数兜底
        global_median = df_clean[col].median()
        if pd.notna(global_median):
            df_clean[col] = df_clean[col].fillna(global_median)
        else:
            df_clean[col] = df_clean[col].fillna(0)

    # -------------------------------------------------------------------
    # Step 3: 行为类缺失值 → 补零
    # -------------------------------------------------------------------
    for col in BEHAVIORAL_FEATURES:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna(0)

    # -------------------------------------------------------------------
    # Step 4: 3σ Winsorization 截断（上边界拉回）
    # -------------------------------------------------------------------
    # 按 PRD 要求，对 Overtime_Hours 等离群行为数据强制执行
    for col in ["Overtime_Hours", "Attendance_Anomaly", "Leave_Frequency"]:
        if col in df_clean.columns:
            df_clean[col] = winsorize_3sigma(df_clean[col], lower=False, upper=True)

    return df_clean, df_quarantine
