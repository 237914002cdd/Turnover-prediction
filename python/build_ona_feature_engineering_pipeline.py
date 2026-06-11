"""
多维特征工程自动化脚本（Feature Engineering Pipeline）

参考: 六大维度特征（基本属性、薪资、绩效、培训、升迁、敬业度）
输入: employee_static / comp_perf_history / behavioral_dynamics / ona_interaction_log
输出: 宽表 feature_matrix 用于 ML 模型训练
"""

import numpy as np
import pandas as pd
from typing import Optional


def build_ona_centrality(ona_log: pd.DataFrame) -> pd.DataFrame:
    """
    从 ONA 交互日志计算 Eigenvector Centrality（特征向量中心度）。

    参数:
        ona_log: columns=[sender_id, receiver_id, interaction_frequency]

    返回:
        centrality_df: columns=[employee_id, eigenvector_centrality, degree_centrality]
    """
    from collections import defaultdict

    # 构建带权邻接表
    adj = defaultdict(float)
    nodes = set()
    for _, row in ona_log.iterrows():
        s, r, w = row['sender_id'], row['receiver_id'], row['interaction_frequency']
        adj[(s, r)] += w
        adj[(r, s)] += w
        nodes.add(s)
        nodes.add(r)

    node_list = list(nodes)
    n = len(node_list)
    if n == 0:
        return pd.DataFrame(columns=['employee_id', 'eigenvector_centrality', 'degree_centrality'])

    idx = {uid: i for i, uid in enumerate(node_list)}
    # 邻接矩阵幂迭代（简化版 Eigenvector Centrality）
    vec = np.ones(n) / n
    for _ in range(30):
        new_vec = np.zeros(n)
        for (s, r), w in adj.items():
            new_vec[idx[s]] += w * vec[idx[r]]
        norm = np.linalg.norm(new_vec)
        if norm == 0:
            break
        new_vec /= norm
        if np.linalg.norm(new_vec - vec) < 1e-6:
            break
        vec = new_vec

    # Degree Centrality
    degree = np.zeros(n)
    for (s, r), w in adj.items():
        degree[idx[s]] += w

    max_deg = degree.max()
    return pd.DataFrame({
        'employee_id': node_list,
        'eigenvector_centrality': vec,
        'degree_centrality': degree / max_deg if max_deg > 0 else degree,
    })


def build_feature_pipeline(
    static: pd.DataFrame,
    comp: pd.DataFrame,
    behavior: pd.DataFrame,
    ona_log: pd.DataFrame,
    perf_period: Optional[str] = None,
) -> pd.DataFrame:
    """
    六大维度特征工程自动化管道。

    参数:
        static: employee_static 表数据
        comp: comp_perf_history 表数据
        behavior: behavioral_dynamics 表数据
        ona_log: ona_interaction_log 表数据
        perf_period: 绩效归属期，如 '2026-06-01'

    返回:
        宽表 DataFrame，列以特征前缀分组：
          base_* / salary_* / perf_* / training_* / promotion_* / engagement_*
    """
    result = static[['employee_id', 'age', 'tenure_years', 'education_level', 'marital_status']].copy()
    result = result.rename(columns={
        'age': 'base_age',
        'tenure_years': 'base_tenure_years',
        'education_level': 'base_education',
    })

    # ---- 1. 基本属性 (Base) ----
    result['base_education_score'] = result['base_education'].map({
        'High_School': 1, 'Bachelor': 2, 'Master': 3, 'PhD': 4,
    }).fillna(1)

    # ---- 2. 薪资维度 (Salary) ----
    latest_comp = comp.sort_values('data_period').groupby('employee_id').last().reset_index()
    merged = result.merge(latest_comp[['employee_id', 'monthly_income', 'salary_increase_pct']],
                          on='employee_id', how='left')
    result['salary_monthly'] = merged['monthly_income'].fillna(0)
    result['salary_growth_pct'] = merged['salary_increase_pct'].fillna(0)

    # ---- 3. 绩效维度 (Perf) ----
    if perf_period:
        perf = comp[comp['data_period'] == perf_period]
    else:
        perf = latest_comp
    merged2 = result.merge(perf[['employee_id', 'performance_score', 'target_completion_rate']],
                           on='employee_id', how='left')
    result['perf_score'] = merged2['performance_score'].fillna(0)
    result['perf_completion_rate'] = merged2['target_completion_rate'].fillna(0)

    # ---- 4. 培训维度 (Training) ----
    # 从行为表中提取培训时长的近似（仅当字段存在时）
    if 'training_hours' in behavior.columns:
        train_agg = behavior.groupby('employee_id')['training_hours'].sum().reset_index()
        merged3 = result.merge(train_agg, on='employee_id', how='left')
        result['training_hours'] = merged3['training_hours'].fillna(0)
    else:
        result['training_hours'] = 0

    # ---- 5. 升迁维度 (Promotion) ----
    # 从 comp 推断晋升：salary_increase_pct 突增作为晋升信号
    comp_sorted = comp.sort_values(['employee_id', 'data_period'])
    comp_sorted['prev_salary'] = comp_sorted.groupby('employee_id')['salary_increase_pct'].shift(1)
    comp_sorted['promotion_flag'] = (
        (comp_sorted['salary_increase_pct'] > 0.15) &
        (comp_sorted['prev_salary'] < 0.10)
    ).astype(int)
    promo_agg = comp_sorted.groupby('employee_id')['promotion_flag'].sum().reset_index()
    promo_agg.columns = ['employee_id', 'promotion_count']
    merged4 = result.merge(promo_agg, on='employee_id', how='left')
    result['promotion_count'] = merged4['promotion_count'].fillna(0)

    # ---- 6. 敬业度维度 (Engagement) ----
    beh_agg = behavior.groupby('employee_id').agg({
        'overtime_hours': 'mean',
        'leave_frequency': 'sum',
        'attendance_anomaly': 'sum',
    }).reset_index()
    merged5 = result.merge(beh_agg, on='employee_id', how='left')
    result['engagement_overtime_avg'] = merged5['overtime_hours'].fillna(0)
    result['engagement_leave_total'] = merged5['leave_frequency'].fillna(0)
    result['engagement_anomaly_total'] = merged5['attendance_anomaly'].fillna(0)

    # ---- 7. ONA 网络中心度 (ONA) ----
    centrality = build_ona_centrality(ona_log)
    merged6 = result.merge(centrality, on='employee_id', how='left')
    result['ona_eigenvector_centrality'] = merged6['eigenvector_centrality'].fillna(0)
    result['ona_degree_centrality'] = merged6['degree_centrality'].fillna(0)

    return result
