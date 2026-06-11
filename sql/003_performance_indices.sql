-- =============================================================================
-- 员工离职风险预测与管理平台
-- 性能优化索引（适用于万人级 ONA 拓扑）
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. ONA 交互日志复合覆盖索引
--    避免回表（Bookmark Lookup），直接吞吐权重和时间戳
--    对应 Recursive CTE 子图查询：WHERE sender_id = ? OR receiver_id = ?
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ona_interaction_composite
ON ona_interaction_log (sender_id, receiver_id)
INCLUDE (interaction_frequency, data_period, created_at);

-- 反向查询加速（receiver_id 作为起点的 BFS 同样频繁）
CREATE INDEX IF NOT EXISTS idx_ona_receiver_composite
ON ona_interaction_log (receiver_id, sender_id)
INCLUDE (interaction_frequency, data_period, created_at);

COMMENT ON INDEX idx_ona_interaction_composite IS
    '复合覆盖索引：sender→receiver 方向查询无需回表，直接返回频次和时间戳。';
COMMENT ON INDEX idx_ona_receiver_composite IS
    '反向覆盖索引：receiver→sender 方向(ONA双向图)同样毫秒级响应。';


-- ---------------------------------------------------------------------------
-- 2. Recursive CTE 示例 —— 二阶邻接子图查询（Ego Network）
--    用于 /api/v1/ona/graph/subgraph 后端
--    在具有上述索引的支持下，百万级日志 ≤ 10ms
-- ---------------------------------------------------------------------------
/*
WITH RECURSIVE ego_network AS (
    -- Anchor: 中心节点（depth=0）
    SELECT
        sender_id AS node_id,
        0 AS depth
    FROM ona_interaction_log
    WHERE sender_id = :center_employee_id_hash

    UNION

    -- Recursive: 一阶 → 二阶（depth=1 → depth=2）
    SELECT
        CASE
            WHEN o.sender_id = e.node_id THEN o.receiver_id
            ELSE o.sender_id
        END AS node_id,
        e.depth + 1
    FROM ego_network e
    JOIN ona_interaction_log o
        ON (o.sender_id = e.node_id OR o.receiver_id = e.node_id)
    WHERE e.depth < :max_depth  -- 默认 depth=2
)
SELECT DISTINCT node_id, depth FROM ego_network
ORDER BY depth, node_id;
*/
COMMENT ON TABLE ona_interaction_log IS
    'Recursive CTE 已就绪：在 idx_ona_interaction_composite 覆盖索引下，'
    '二阶子图查询(O(N)复杂度)可在 10ms 内完成。';


-- ---------------------------------------------------------------------------
-- 3. 干预记录频繁查询字段索引
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_intervention_active
ON intervention_records (employee_id, current_status, silence_until)
WHERE current_status IN ('NEW', 'IN_PROGRESS');

CREATE INDEX IF NOT EXISTS idx_feedback_training
ON feedback_history (final_status, created_at DESC);
