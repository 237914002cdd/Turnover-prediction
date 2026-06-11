-- =============================================================================
-- 员工离职风险预测与管理平台
-- PostgreSQL DDL 建表脚本
-- 依据: Master PRD V4.0 第六章第一节《全量核心字段映射与采集规范表》
-- 说明: 所有 Employee_ID 相关字段入库前已执行 irreversible MD5 哈希脱敏
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. 员工静态属性表 (employee_static)
-- 存储个人属性静态数据，全量覆盖 > 98%
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employee_static (
    employee_id      VARCHAR(64)    PRIMARY KEY,                  -- 脱敏工号：原始工号入库前经 irreversible MD5 哈希处理
    age              INTEGER        NOT NULL,                      -- 当前绝对周岁年龄
    tenure_years     NUMERIC(5,2)   NOT NULL,                      -- 司龄：(当前日期 - 入职日期) / 365，保留两位小数
    marital_status   VARCHAR(20)    DEFAULT NULL,                  -- 婚姻状况枚举：Single, Married, Divorced, Others
    education_level  VARCHAR(20)    NOT NULL,                      -- 最高学历枚举：High_School, Bachelor, Master, PhD
    job_level        VARCHAR(20)    NOT NULL,                      -- 当前行政职级序列代码
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN employee_static.employee_id IS '员工唯一标识，明文工号入库前强制 irreversible MD5 脱敏；前端不可逆显示，仅用于系统内联表关联';
COMMENT ON COLUMN employee_static.age IS '绝对周岁年龄，同辈隐私保护：仅允许聚合统计使用，禁止输出个体精确年龄';
COMMENT ON COLUMN employee_static.marital_status IS '婚姻状况非必填，允许 NULL（员工未填报场景），枚举校验在应用层完成';


-- ---------------------------------------------------------------------------
-- 2. 薪酬绩效历史表 (comp_perf_history)
-- 存储月度/季度薪酬与绩效考核数据，支持 T+7 更新窗口
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comp_perf_history (
    perf_id                 BIGSERIAL       PRIMARY KEY,
    employee_id             VARCHAR(64)     NOT NULL,
    data_period             DATE            NOT NULL,               -- 数据归属期（按月粒度，取当月1日）
    monthly_income          NUMERIC(12,2)   NOT NULL,               -- 【敏感】月基本薪资：前端仅 HRD 权限可见；普通业务层按中位数区间模糊化展示
    salary_increase_pct     NUMERIC(6,4)    DEFAULT NULL,           -- 年同比调薪幅度：(当前月薪 - 一年前月薪) / 一年前月薪
    performance_score       NUMERIC(5,2)    DEFAULT NULL,           -- 最近一期绩效考核绝对得分
    target_completion_rate  NUMERIC(5,2)    DEFAULT NULL,           -- 业务核心 KPI 目标实际完成百分比（%）
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_comp_employee FOREIGN KEY (employee_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE,

    -- 同一员工同一个月只能有一条薪酬记录
    CONSTRAINT uq_employee_period UNIQUE (employee_id, data_period)
);

COMMENT ON COLUMN comp_perf_history.monthly_income IS '【高敏感字段】依据 PRD 第七章隐私条款：(1) 存储层不做明文加密(交由列级 TDE 或全库加密)；(2) 前端应用层根据角色权限控制可见性——非 HRD 角色需模糊化展示';
COMMENT ON COLUMN comp_perf_history.salary_increase_pct IS '可为 NULL（新入职不满一年无同比基准），应用层填充逻辑归入「数值类缺失 → 部门+职级中位数」管道';
COMMENT ON COLUMN comp_perf_history.data_period IS '取当月1日 DATE 值，例如 2026-06-01 代表 2026 年 6 月整月数据；禁止存储未来期';


-- ---------------------------------------------------------------------------
-- 3. 动态行为表 (behavioral_dynamics)
-- 按月度粒度记录员工工作行为/考勤动态数据
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS behavioral_dynamics (
    behavior_id          BIGSERIAL       PRIMARY KEY,
    employee_id          VARCHAR(64)     NOT NULL,
    data_period          DATE            NOT NULL,
    overtime_hours       NUMERIC(6,2)    DEFAULT 0,                 -- 月度累计加班总小时数；缺失时默认补 0
    leave_frequency      INTEGER         DEFAULT 0,                 -- 月度请假总次数(事假+病假+年假)；缺失时默认补 0
    attendance_anomaly   INTEGER         DEFAULT 0,                 -- 月度打卡异常(忘打卡/迟到/早退)累计次数；缺失时默认补 0
    created_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_behavior_employee FOREIGN KEY (employee_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_behavior_period UNIQUE (employee_id, data_period)
);

COMMENT ON COLUMN behavioral_dynamics.overtime_hours IS '行为类特征；缺失时应用层强制补 0（PRD 第六章第二节空值规则）；入离线检测管道前需经 3σ Winsorization 截断';
COMMENT ON COLUMN behavioral_dynamics.leave_frequency IS '行为类特征；缺失时默认补 0';
COMMENT ON COLUMN behavioral_dynamics.attendance_anomaly IS '行为类特征；缺失时默认补 0；月度异常数环比激增 > 40% 将作为 SHAP 归因证据输出';


-- ---------------------------------------------------------------------------
-- 4. ONA 交互日志元数据表 (ona_interaction_log)
-- 存储脱敏后的组织社交网络交互元数据
-- 依据 PRD 第七章：严禁存储聊天文本/语音/文档内容，仅存元数据
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ona_interaction_log (
    log_id                BIGSERIAL      PRIMARY KEY,
    sender_id             VARCHAR(64)    NOT NULL,                   -- 互动发起人脱敏 ID（对应 employee_id 哈希值）
    receiver_id           VARCHAR(64)    NOT NULL,                   -- 互动接收人脱敏 ID（对应 employee_id 哈希值）
    interaction_type      VARCHAR(20)    NOT NULL,                   -- 互动媒介枚举：Private_Chat, Group_Mention, Doc_CoEdit
    interaction_frequency INTEGER        NOT NULL DEFAULT 0,         -- 统计周期(月度)内该链路累计交互频次
    data_period           DATE           NOT NULL,                   -- 统计归属期
    created_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_ona_sender FOREIGN KEY (sender_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ona_receiver FOREIGN KEY (receiver_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE,

    -- 同一对交互关系在同一个月内只能有一条汇总记录
    CONSTRAINT uq_ona_link_period UNIQUE (sender_id, receiver_id, interaction_type, data_period)
);

COMMENT ON TABLE ona_interaction_log IS '【隐私合规关键表】仅存储交互元数据(谁+何时+与谁+频次+媒介类型)，严禁存储任何聊天文本、语音、文档具体内容。依据 PRD 第七章合规条款设计';
COMMENT ON COLUMN ona_interaction_log.sender_id IS '脱敏 ID，与 employee_static.employee_id 同源(MD5 哈希)';
COMMENT ON COLUMN ona_interaction_log.receiver_id IS '脱敏 ID，与 employee_static.employee_id 同源(MD5 哈希)';
COMMENT ON COLUMN ona_interaction_log.interaction_type IS '枚举值约束：Private_Chat / Group_Mention / Doc_CoEdit；应用层强制执行';


-- ---------------------------------------------------------------------------
-- 5. 索引建议
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_comp_employee_period   ON comp_perf_history(employee_id, data_period DESC);
CREATE INDEX IF NOT EXISTS idx_behavior_employee_period ON behavioral_dynamics(employee_id, data_period DESC);
CREATE INDEX IF NOT EXISTS idx_ona_sender_period       ON ona_interaction_log(sender_id, data_period DESC);
CREATE INDEX IF NOT EXISTS idx_ona_receiver_period     ON ona_interaction_log(receiver_id, data_period DESC);
CREATE INDEX IF NOT EXISTS idx_ona_link                ON ona_interaction_log(sender_id, receiver_id, interaction_type);
