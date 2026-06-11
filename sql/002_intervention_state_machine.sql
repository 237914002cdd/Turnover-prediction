-- =============================================================================
-- 员工离职风险预测与管理平台
-- 干预状态机 DDL + 流转触发器
-- 依据: Master PRD V4.0 第五章第 2 节 + 第四章第 4 节 (Human-in-the-loop)
-- 状态机: New → In Progress → Resolved | False Positive | Turnover
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. 干预状态机 — 枚举类型
-- ---------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE intervention_status AS ENUM (
        'NEW',             -- 未处理：系统首次标记为高危，待 HRBP 认领
        'IN_PROGRESS',     -- 干预中：HRBP 已启动干预，30 天内不重复告警
        'RESOLVED',        -- 留任成功：干预措施生效，员工确认留任
        'FALSE_POSITIVE',  -- 误报排除：HR 确认原因为不可控因素(家庭搬迁等)
        'TURNOVER'         -- 干预失败：员工最终离职
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE feedback_source AS ENUM (
        'HR_MANUAL',       -- HR 手动在后台勾选
        'SYSTEM_IMPORT',   -- 系统批量导入（离职数据回传）
        'API_SYNC'         -- 第三方 HRIS 同步记录
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ---------------------------------------------------------------------------
-- 2. 干预记录主表 (intervention_records)
--    每条记录代表一个员工在某次风险判定后的干预跟踪
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS intervention_records (
    record_id            BIGSERIAL           PRIMARY KEY,
    employee_id          VARCHAR(64)         NOT NULL,

    -- 风险快照（创建时冻结，不随后续模型更新而变）
    snapshot_risk_level     intervention_status NOT NULL DEFAULT 'NEW',
    snapshot_risk_score     NUMERIC(6,4)        NOT NULL,       -- 创建时的综合排序分
    snapshot_base_prob      NUMERIC(5,4)        NOT NULL,       -- 创建时的基础离职概率
    snapshot_ona_centrality NUMERIC(5,4)        DEFAULT NULL,   -- 创建时的 ONA 中心度

    -- 状态机
    current_status          intervention_status NOT NULL DEFAULT 'NEW',
    status_changed_at       TIMESTAMPTZ         DEFAULT NULL,
    status_changed_by       VARCHAR(64)         DEFAULT NULL,   -- HRBP 工号

    -- 沉默期：IN_PROGRESS 状态下 N 天内不重复告警
    silence_until           DATE                DEFAULT NULL,

    -- 干预方案快照（ROI 测算数据）
    proposed_raise_pct      NUMERIC(5,4)        DEFAULT NULL,   -- 拟调薪幅度
    pre_expected_cost       NUMERIC(12,2)       DEFAULT NULL,   -- 调薪前预期离职花费
    post_expected_cost      NUMERIC(12,2)       DEFAULT NULL,   -- 调薪后预期离职花费
    total_investment        NUMERIC(12,2)       DEFAULT NULL,   -- 企业投入资金
    net_savings             NUMERIC(12,2)       DEFAULT NULL,   -- 净节约金额（决策判定值）
    is_positive_roi         BOOLEAN             DEFAULT NULL,   -- ROI 是否为正

    -- 审计
    created_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_intervention_employee FOREIGN KEY (employee_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE intervention_records IS
    '干预记录主表。每产生一条红色/橙色预警，系统自动创建一条 NEW 状态记录。'
    'IN_PROGRESS 状态下的员工在 silence_until 前不会被重复告警。';

COMMENT ON COLUMN intervention_records.snapshot_risk_level IS
    '创建时的风险等级快照，冻结历史，防止模型重算后历史标签漂移。';
COMMENT ON COLUMN intervention_records.silence_until IS
    '沉默截止日期。IN_PROGRESS 状态下默认当前日期 + 30 天，此间仪表盘不再重复告警。';
COMMENT ON COLUMN intervention_records.net_savings IS
    '【决策判定值】> 0 表示干预方案择优；= 字段值从 ROI 引擎 compute_roi_kpi() 写入。';


-- ---------------------------------------------------------------------------
-- 3. 人机闭环反馈归档表 (feedback_history)
--    存储 HR 人工标注的最终结果，用于模型重训的 ground truth
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback_history (
    feedback_id          BIGSERIAL           PRIMARY KEY,
    record_id            BIGINT              NOT NULL,           -- 关联 intervention_records
    employee_id          VARCHAR(64)         NOT NULL,

    -- 人工标注结果
    final_status         intervention_status NOT NULL,           -- RESOLVED / FALSE_POSITIVE / TURNOVER
    source               feedback_source     NOT NULL DEFAULT 'HR_MANUAL',
    feedback_notes       TEXT                DEFAULT NULL,       -- HR 备注（如"员工因家庭搬迁离职"）

    -- 标注时的上下文快照（用于分析标注偏差）
    context_risk_score       NUMERIC(6,4)    NOT NULL,
    context_base_prob        NUMERIC(5,4)    NOT NULL,
    context_ona_centrality   NUMERIC(5,4)    DEFAULT NULL,
    context_net_savings      NUMERIC(12,2)   DEFAULT NULL,

    -- 审计
    created_by           VARCHAR(64)         NOT NULL,           -- 标注人 HRBP 工号
    created_at           TIMESTAMPTZ         NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_feedback_record FOREIGN KEY (record_id)
        REFERENCES intervention_records(record_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_feedback_employee FOREIGN KEY (employee_id)
        REFERENCES employee_static(employee_id)
        ON DELETE CASCADE
);

COMMENT ON TABLE feedback_history IS
    '人机闭环反馈归档表 (Human-in-the-loop)。最终标注结果在模型定期重训(retraining)时'
    '作为高权重 ground truth 重新喂入算法，修正 SHAP 特征相关性参数。';

COMMENT ON COLUMN feedback_history.final_status IS
    '最终结果：RESOLVED(留任成功) / FALSE_POSITIVE(误报) / TURNOVER(已离职)。'
    '只有这三种状态会触发模型重训。IN_PROGRESS 记录不在归档范围。';


-- ---------------------------------------------------------------------------
-- 4. 索引
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_intervention_employee   ON intervention_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_intervention_status     ON intervention_records(current_status);
CREATE INDEX IF NOT EXISTS idx_intervention_silence    ON intervention_records(silence_until)
    WHERE current_status = 'IN_PROGRESS';                         -- 沉默期查询专用
CREATE INDEX IF NOT EXISTS idx_feedback_record         ON feedback_history(record_id);
CREATE INDEX IF NOT EXISTS idx_feedback_final_status   ON feedback_history(final_status);


-- ---------------------------------------------------------------------------
-- 5. 状态机约束与触发器
-- ---------------------------------------------------------------------------

-- 5.1 约束：只允许合法的状态转换
--    NEW → IN_PROGRESS
--    IN_PROGRESS → RESOLVED | FALSE_POSITIVE | TURNOVER
--    其余组合一律拒绝
CREATE OR REPLACE FUNCTION check_status_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- 首次创建（NEW）允许
    IF TG_OP = 'INSERT' THEN
        IF NEW.current_status != 'NEW' THEN
            RAISE EXCEPTION '新干预记录只能以 NEW 状态创建。当前状态: %', NEW.current_status;
        END IF;
        RETURN NEW;
    END IF;

    -- 更新时校验
    IF OLD.current_status = 'NEW' AND NEW.current_status = 'IN_PROGRESS' THEN
        -- ✅ 合法
        NEW.status_changed_at := NOW();
        NEW.silence_until := (CURRENT_DATE + INTERVAL '30 days')::DATE;
        RETURN NEW;
    END IF;

    IF OLD.current_status = 'IN_PROGRESS'
       AND NEW.current_status IN ('RESOLVED', 'FALSE_POSITIVE', 'TURNOVER') THEN
        -- ✅ 合法
        NEW.status_changed_at := NOW();
        NEW.silence_until := NULL;  -- 关闭沉默期
        RETURN NEW;
    END IF;

    -- ❌ 非法转换
    RAISE EXCEPTION '非法状态转换: % → %', OLD.current_status, NEW.current_status;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS trg_intervention_status ON intervention_records;
CREATE TRIGGER trg_intervention_status
    BEFORE INSERT OR UPDATE OF current_status
    ON intervention_records
    FOR EACH ROW
    EXECUTE FUNCTION check_status_transition();


-- 5.2 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_intervention_updated_at ON intervention_records;
CREATE TRIGGER trg_intervention_updated_at
    BEFORE UPDATE ON intervention_records
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();


-- ---------------------------------------------------------------------------
-- 6. 视图：高危员工活跃干预看板
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_active_interventions AS
SELECT
    ir.record_id,
    ir.employee_id,
    es.display_alias,
    es.department,
    es.job_level,
    ir.current_status,
    ir.snapshot_risk_score,
    ir.snapshot_base_prob,
    ir.net_savings,
    ir.is_positive_roi,
    ir.silence_until,
    ir.created_at AS alerted_at,
    CASE
        WHEN ir.current_status = 'NEW' THEN '待处理'
        WHEN ir.current_status = 'IN_PROGRESS' THEN '干预中'
        WHEN ir.current_status = 'RESOLVED' THEN '已留任'
        WHEN ir.current_status = 'FALSE_POSITIVE' THEN '误报排除'
        WHEN ir.current_status = 'TURNOVER' THEN '已离职'
    END AS status_label
FROM intervention_records ir
LEFT JOIN employee_static es ON ir.employee_id = es.employee_id
WHERE ir.current_status NOT IN ('RESOLVED', 'FALSE_POSITIVE', 'TURNOVER')
ORDER BY ir.snapshot_risk_score DESC;
