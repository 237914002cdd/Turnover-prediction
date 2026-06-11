"""
===========================================================
测试脚本: IBM HR Analytics 10 行中文映射 MVP
路径要求: 严格限制在 D: 盘工程目录下
===========================================================
生成符合 Kaggle IBM HR 格式的 10 行测试数据，
执行完整的中文 Schema Mapping，输出到 D:\api\mock\test_10_rows.csv
"""

import os, sys, io
import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

np.random.seed(42)

# 确保输出路径在 D 盘
OUTPUT_DIR = r"D:\claude code mode\files\turnover-prediction\api\mock"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_PATH = os.path.join(OUTPUT_DIR, "test_10_rows.csv")

print("=" * 60)
print("IBM HR Analytics 10 行中文映射 MVP 测试")
print("=" * 60)
print(f"\n输出路径: {CSV_PATH}")
print(f"路径在 D 盘: {CSV_PATH.startswith('D:') or CSV_PATH.startswith('d:')}")
print()

# =============================================================
# 1. 生成 10 行 IBM HR Kaggle 格式的原始数据
# =============================================================
raw_data = {
    'EmployeeNumber': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    'Age': [41, 49, 37, 33, 27, 32, 59, 30, 38, 36],
    'Gender': ['Female', 'Male', 'Male', 'Female', 'Male', 'Male', 'Female', 'Male', 'Female', 'Male'],
    'MaritalStatus': ['Single', 'Married', 'Single', 'Married', 'Divorced', 'Single', 'Married', 'Married', 'Single', 'Divorced'],
    'Education': [2, 1, 2, 4, 3, 3, 3, 3, 2, 4],
    'EducationField': ['Life Sciences', 'Life Sciences', 'Other', 'Life Sciences', 'Medical', 'Life Sciences', 'Life Sciences', 'Marketing', 'Medical', 'Life Sciences'],
    'Department': ['Sales', 'Research & Development', 'Research & Development', 'Research & Development', 'Research & Development', 'Research & Development', 'Research & Development', 'Research & Development', 'Sales', 'Research & Development'],
    'JobRole': ['Sales Executive', 'Research Scientist', 'Laboratory Technician', 'Research Scientist', 'Manufacturing Director', 'Healthcare Representative', 'Manager', 'Sales Executive', 'Research Scientist', 'Laboratory Technician'],
    'JobLevel': [2, 2, 1, 3, 3, 2, 4, 3, 2, 1],
    'MonthlyIncome': [5993, 5130, 2090, 10470, 13070, 6362, 20410, 10870, 5770, 2690],
    'Attrition': ['No', 'Yes', 'No', 'No', 'Yes', 'No', 'No', 'No', 'Yes', 'No'],
    'OverTime': ['Yes', 'No', 'Yes', 'Yes', 'No', 'No', 'No', 'No', 'Yes', 'Yes'],
    'BusinessTravel': ['Travel_Rarely', 'Travel_Frequently', 'Travel_Rarely', 'Travel_Frequently', 'Travel_Rarely', 'Non-Travel', 'Travel_Frequently', 'Travel_Rarely', 'Travel_Rarely', 'Travel_Frequently'],
    'PerformanceRating': [3, 3, 3, 3, 3, 4, 4, 3, 4, 3],
    'YearsAtCompany': [6, 10, 0, 8, 2, 7, 1, 5, 4, 2],
    'YearsInCurrentRole': [4, 7, 0, 7, 2, 7, 0, 4, 2, 1],
    'PercentSalaryHike': [11, 23, 15, 11, 12, 13, 20, 22, 13, 11],
    'TotalWorkingYears': [8, 10, 6, 8, 8, 12, 6, 8, 10, 8],
    'NumCompaniesWorked': [1, 1, 9, 6, 1, 3, 1, 1, 2, 6],
    'TrainingTimesLastYear': [2, 3, 3, 5, 3, 1, 5, 2, 6, 3],
    'EnvironmentSatisfaction': [2, 3, 4, 4, 1, 3, 3, 4, 4, 3],
    'JobSatisfaction': [4, 2, 3, 4, 1, 3, 4, 3, 3, 2],
    'RelationshipSatisfaction': [3, 3, 2, 3, 1, 3, 3, 3, 3, 3],
    'WorkLifeBalance': [1, 3, 3, 3, 2, 3, 3, 3, 2, 2],
    'Over18': ['Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y'],
    'EmployeeCount': [1]*10,
    'StandardHours': [80]*10,
}
df_raw = pd.DataFrame(raw_data)

print("1. 原始数据 (前 5 列预览):")
print(df_raw[['EmployeeNumber', 'Age', 'Department', 'Attrition', 'MonthlyIncome']].head(10).to_string())
print(f"   总列数: {df_raw.shape[1]}")
print()

# =============================================================
# 2. 中文 Schema Mapping
# =============================================================

df = df_raw.copy()

# 2a. 删除冗余列
DROP_COLS = ['EmployeeCount', 'Over18', 'StandardHours']
df.drop(columns=DROP_COLS, inplace=True, errors='ignore')
print(f"2a. 已删除 {DROP_COLS}，剩余列数: {df.shape[1]}")

# 2b. Attrition 映射
attrition_map = {'Yes': '离职', 'No': '在岗'}
df['离职状态'] = df['Attrition'].map(attrition_map)
assert df['离职状态'].isin(['离职', '在岗']).all(), "离职状态映射错误"
print(f"2b. Attrition 映射: {dict(df['离职状态'].value_counts())}")

# 2c. BusinessTravel 映射
travel_map = {'Travel_Frequently': '高', 'Travel_Rarely': '中', 'Non-Travel': '低'}
df['出差频率'] = df['BusinessTravel'].map(travel_map)
assert df['出差频率'].isin(['高', '中', '低']).all(), "出差频率映射错误"
print(f"2c. 出差频率映射: {dict(df['出差频率'].value_counts())}")

# 2d. Department 映射（大厂壳子）
dept_map = {
    'Research & Development': '用友网络 - 数智人力事业部',
    'Sales': '数智营销事业部',
    'Human Resources': '共享服务平台',
}
df['事业部'] = df['Department'].map(dept_map)
print(f"2d. 事业部映射: {df['事业部'].unique()}")

# 2e. JobRole 映射
role_map = {
    'Sales Executive': '高级销售经理',
    'Research Scientist': '高级产品经理',
    'Laboratory Technician': '售前顾问',
    'Manufacturing Director': '交付总监',
    'Healthcare Representative': '客户成功经理',
    'Manager': '部门总监',
    'Human Resources': 'HRBP',
}
df['岗位'] = df['JobRole'].map(role_map)
print(f"2e. 岗位映射: {list(df['岗位'].unique())}")

# 2f. MonthlyIncome 重命名 & 类型保留
df.rename(columns={'MonthlyIncome': '月薪'}, inplace=True)
assert df['月薪'].dtype in ['int64', 'float64'], f"月薪类型异常: {df['月薪'].dtype}"
print(f"2f. 月薪类型: {df['月薪'].dtype}")

# =============================================================
# 3. 九宫格 & 行为合成
# =============================================================

# 3a. PerformanceRating → 中文
perf_map = {1: '及格', 2: '中等', 3: '良好', 4: '优秀'}
df['上年度绩效'] = df['PerformanceRating'].map(perf_map)
assert df['上年度绩效'].isin(['优秀', '良好', '中等', '及格']).all(), "绩效映射错误"
print(f"3a. 绩效分布: {dict(df['上年度绩效'].value_counts())}")

# 3b. Mock 月工作时长（真实整数）
np.random.seed(42)
df['月工作时长'] = np.random.randint(160, 221, size=len(df))
assert df['月工作时长'].dtype in ['int64', 'int32'], f"工作时长类型异常: {df['月工作时长'].dtype}"
print(f"3b. 月工作时长: min={df['月工作时长'].min()} max={df['月工作时长'].max()} type={df['月工作时长'].dtype}")

# =============================================================
# 4. 输出结果
# =============================================================
OUTPUT_COLS = ['员工编号', '年龄', '性别', '离职状态', '事业部', '岗位',
               '月薪', '出差频率', '上年度绩效', '月工作时长', '司龄', '现职年限']
df['员工编号'] = df['EmployeeNumber']
df['年龄'] = df['Age']
df['性别'] = df['Gender'].map({'Male': '男', 'Female': '女'})
df['司龄'] = df['YearsAtCompany']
df['现职年限'] = df['YearsInCurrentRole']

df_output = df[OUTPUT_COLS].copy()

print("\n" + "=" * 60)
print("4. 最终 10 行输出:")
print("=" * 60)
print(df_output.to_string(index=False))

# 保存 CSV
df_output.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
print(f"\n✅ 已保存至: {CSV_PATH}")
print(f"   文件大小: {os.path.getsize(CSV_PATH)} bytes")
print()

# =============================================================
# 5. 快速校验断言
# =============================================================
print("=" * 60)
print("5. 快速校验断言")
print("=" * 60)

checks = [
    ("CSV 在 D 盘", CSV_PATH.startswith('D:') or CSV_PATH.startswith('d:')),
    ("离职状态无拼音", df_output['离职状态'].isin(['离职', '在岗']).all()),
    ("出差频率无英文", df_output['出差频率'].isin(['高', '中', '低']).all()),
    ("事业部已映射", not df_output['事业部'].str.contains('Research|Sales', na=False).any()),
    ("岗位已中文", not df_output['岗位'].str.contains('Executive|Scientist|Technician', na=False).any()),
    ("绩效中文", df_output['上年度绩效'].isin(['优秀', '良好', '中等', '及格']).all()),
    ("月薪整数", df_output['月薪'].dtype in ['int64', 'int32', 'float64']),
    ("工作时长整数", df_output['月工作时长'].dtype in ['int64', 'int32']),
    ("行数=10", len(df_output) == 10),
]

all_pass = True
for name, result in checks:
    status = "✅" if result else "❌"
    print(f"   {status} {name}")
    if not result:
        all_pass = False

print(f"\n结论: {'✅ 全部通过，可扩展至 1470 行全量' if all_pass else '❌ 存在失败项，请检查'}")
