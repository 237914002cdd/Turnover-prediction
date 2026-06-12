import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { fetchOnaNodeDetails, createIntervention, simulateRoi, fetchPlaybook, fetchDiagnostic, fetchSubgraph } from '../api/ona';
import { riskLevelColor } from '../mock/mockData';
import { EMPLOYEE_REGISTRY } from '../mock/employeeRegistry';
import { debounce } from 'lodash';

const LoadingScreen = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0f0f1a', color: '#888' }}>
    <div style={{ fontSize: 14 }}>加载中...</div>
  </div>
);

const EmployeeDrillDown = ({ employeeId, onBack }) => {
  const [data, setData] = useState(null);
  const [diagnosticData, setDiagnosticData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [raisePct, setRaisePct] = useState(0);
  const [interventionDone, setInterventionDone] = useState(false);
  const [roiResult, setRoiResult] = useState(null);
  const fetchingRef = useRef(false);
  const [playbookLoading, setPlaybookLoading] = useState(false);
  const [playbookContent, setPlaybookContent] = useState(null);
  const [showPlaybook, setShowPlaybook] = useState(false);
  // 多重干预复选框
  const [interventions, setInterventions] = useState({
    salary: true,
    travel: false,
    workload: false,
    mentor: false,
  });
  const interventionLabels = {
    salary: '调薪',
    travel: '降低出差频率',
    workload: '负荷分流',
    mentor: '导师计划',
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchOnaNodeDetails(employeeId),
      fetchDiagnostic(employeeId).catch(() => null),
    ]).then(([onaResp, diagResp]) => {
      if (onaResp?.code === 200) setData(onaResp.data);
      if (diagResp?.code === 200) setDiagnosticData(diagResp.data);
      else if (onaResp?.data) {
        // Fallback: if diagnostic fails (e.g. generic hash), build minimal display from hover data
        setDiagnosticData({
          employee_info: onaResp.data.node_info,
          attribution_factors: onaResp.data.shap_risk_factors || [],
        });
      }
      setLoading(false);
    });
  }, [employeeId]);

  const empReg = EMPLOYEE_REGISTRY[employeeId];
  const currentSalary = empReg?.monthlyIncome || 13000;
  const replacementCost = useMemo(() => data?.risk_metrics?.total_replacement_cost_cny || (empReg ? empReg.monthlyIncome * 2 : 25000), [data, empReg]);
  const baseProb = useMemo(() => data?.risk_metrics?.base_turnover_probability || empReg?.originalRisk || 0, [data, empReg]);

  const debouncedSimulate = useCallback(
    debounce(async (empId, pct) => {
      if (fetchingRef.current) return;
      fetchingRef.current = true;
      try {
        const resp = await simulateRoi(empId, pct / 100);
        if (resp?.code === 200) setRoiResult(resp.data);
      } catch (err) { console.error('ROI simulate failed', err); }
      finally { fetchingRef.current = false; }
    }, 100), []
  );

  const handleSliderChange = (e) => {
    const newVal = Number(e.target.value);
    setRaisePct(newVal);
    if (newVal > 0) debouncedSimulate(employeeId, newVal);
    else setRoiResult(null);
  };

  const toggleIntervention = (key) => {
    setInterventions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // 多重干预 ROI 叠加效果
  const extraBoost = Object.entries(interventions)
    .filter(([, v]) => v)
    .reduce((acc, [k]) => {
      if (k === 'salary') return acc + 0;
      if (k === 'travel') return acc + 0.08;
      if (k === 'workload') return acc + 0.12;
      if (k === 'mentor') return acc + 0.10;
      return acc;
    }, 0);
  // 综合离职概率降幅：调薪 + 多重干预叠加
  const combinedProbDrop = roiResult
    ? Math.min(1, (baseProb - roiResult.data?.proposed_turnover_prob || 0) + extraBoost)
    : 0;

  const raiseAmount = currentSalary * (raisePct / 100);
  const newSalary = currentSalary + raiseAmount;

  if (loading || !data) return <LoadingScreen />;

  const { node_info, risk_metrics, shap_risk_factors } = data;
  const currentProbPct = (baseProb * 100).toFixed(0);
  const effectiveResult = roiResult || {
    proposed_turnover_prob: baseProb, investment_cost: 0, benefit: 0, net_savings: 0, is_preferred_decision: false,
  };
  const newProbPct = (effectiveResult.proposed_turnover_prob * 100).toFixed(0);
  const pctDrop = raisePct > 0 ? ((baseProb - effectiveResult.proposed_turnover_prob) / baseProb * 100).toFixed(0) : '0';

  const factors = diagnosticData?.attribution_factors || [];

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f0f1a', color: '#e0e0e0', fontFamily: 'inherit' }}>
      {/* LEFT PANEL */}
      <div style={{ flex: 1, padding: '32px 32px', overflowY: 'auto', borderRight: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <button onClick={onBack} style={{ background: 'rgba(255,255,255,0.06)', border: 'none', color: '#aaa', padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 12 }}
            onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.12)'}
            onMouseLeave={(e) => e.target.style.background = 'rgba(255,255,255,0.06)'}>
            ← 返回拓扑图
          </button>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600, color: '#f0f0f0' }}>员工诊断 & 留任决策沙盘</h2>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '16px 20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0f0' }}>{diagnosticData?.employee_info?.display_alias || node_info.display_alias}</div>
              <div style={{ fontSize: 12, color: '#777', marginTop: 2 }}>
                {diagnosticData?.employee_info?.age ?? '-'}岁 · {node_info.department}{node_info.job_level ? ` · ${node_info.job_level}` : ''}{node_info.tenure_years ? ` · 司龄${node_info.tenure_years}年` : ''}
                {diagnosticData?.employee_info?.education ? ` · ${diagnosticData.employee_info.education}` : ''}
              </div>
              <div style={{ marginTop: 6, display: 'flex', gap: 14, fontSize: 11 }}>
                <span style={{ color: '#888' }}>绩效: <strong style={{ color: '#FFA940' }}>{node_info.performance_score ?? '-'}</strong></span>
                <span style={{ color: '#888' }}>月薪: <strong style={{ color: '#FFA940' }}>¥{currentSalary.toLocaleString()}</strong></span>
                <span style={{ color: '#888' }}>替换成本: <strong style={{ color: '#FF4D4F' }}>¥{replacementCost.toLocaleString()}</strong></span>
                <span style={{ color: '#888' }}>离职概率: <strong style={{ color: '#FF4D4F' }}>{currentProbPct}%</strong></span>
              </div>
            </div>
            <div style={{ padding: '3px 12px', borderRadius: 5, fontSize: 12, fontWeight: 600,
              background: risk_metrics.final_risk_level === 'RED' ? 'rgba(255,77,79,0.2)' : 'rgba(250,140,22,0.2)',
              color: risk_metrics.final_risk_level === 'RED' ? '#FF4D4F' : '#FA8C16',
              border: `1px solid ${riskLevelColor(risk_metrics.final_risk_level)}33` }}>
              {risk_metrics.final_risk_level === 'RED' ? '高危' : risk_metrics.final_risk_level === 'ORANGE' ? '中危' : '关注'}
            </div>
          </div>
        </div>

        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#ccc', marginBottom: 12 }}>核心不满驱动因子矩阵</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, minWidth: 700 }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.04)' }}>
                {['序号', '指标名称', '指标值', '相关系数', '离职概率值', '指标值-调整', '离职概率值-调整', '变化值'].map(h => (
                  <th key={h} style={{ padding: '8px 8px', textAlign: 'center', color: '#999', fontWeight: 500, borderBottom: '1px solid rgba(255,255,255,0.08)', fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {factors.map((f, i) => {
                const isSalary = f.factor_name === 'salary_growth';
                let adjValue = f.current_value;
                let adjProb = null;
                let delta = null;
                if (isSalary && raisePct > 0) {
                  const oldPct = parseFloat(f.current_value.replace('%', '')) || 0;
                  adjValue = `${(oldPct + raisePct).toFixed(0)}%`;
                  const reduction = raisePct / 30;
                  adjProb = +(f.prob_contribution * Math.max(0, 1 - reduction * 1.5)).toFixed(3);
                  delta = +((adjProb - f.prob_contribution) * 100).toFixed(1);
                }
                return (
                  <tr key={f.factor_name} style={{
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    background: isSalary && raisePct > 0 ? 'rgba(24,144,255,0.06)' : 'transparent',
                  }}>
                    <td style={{ padding: '7px 6px', textAlign: 'center', color: '#666' }}>{i + 1}</td>
                    <td style={{ padding: '7px 6px', color: '#bbb', fontWeight: isSalary ? 600 : 400 }}>{f.factor_label}</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: '#ddd' }}>{f.current_value}</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: f.coefficient > 0 ? '#FF7A45' : '#52C41A' }}>{f.coefficient > 0 ? '+' : ''}{f.coefficient.toFixed(3)}</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: '#f0f0f0' }}>{(f.prob_contribution * 100).toFixed(1)}%</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: isSalary && raisePct > 0 ? '#1890FF' : '#666' }}>{adjValue}</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: adjProb !== null ? '#52C41A' : '#666' }}>{adjProb !== null ? `${(adjProb * 100).toFixed(1)}%` : '-'}</td>
                    <td style={{ padding: '7px 6px', textAlign: 'center', fontFamily: 'monospace', color: delta !== null ? (delta < 0 ? '#52C41A' : '#FF4D4F') : '#666' }}>
                      {delta !== null ? `${delta > 0 ? '+' : ''}${delta}%` : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 8, fontSize: 10, color: '#555' }}>拖动右侧调薪滑块 → 薪资增幅行实时联动刷新</div>

        {shap_risk_factors.length > 0 && (
          <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '14px 18px', border: '1px solid rgba(255,255,255,0.06)', marginTop: 16 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, color: '#bbb', marginBottom: 8 }}>核心不满驱动因子 (Top 3)</h3>
            {shap_risk_factors.map((f, i) => (
              <div key={f.factor_name} style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 2 }}>
                  <span style={{ color: '#ccc' }}>{i + 1}. {f.factor_label}</span>
                  <span style={{ color: '#888' }}>{f.current_value}</span>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.05)', height: 3, borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.min(f.shap_value * 100, 100)}%`, background: 'linear-gradient(90deg, #FF4D4F, #FF7A45)', borderRadius: 2 }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT PANEL */}
      <div style={{ width: 440, padding: '32px 28px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#ccc', marginBottom: 20 }}>
          留任决策财务模拟器 · ROI Sandbox
          <span style={{ fontSize: 10, color: '#555', fontWeight: 400, marginLeft: 8 }}>(后端引擎实时计算)</span>
        </h3>

        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: '20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontSize: 12, color: '#888' }}>拟调薪幅度</span>
            <span style={{ fontSize: 22, fontWeight: 700, color: '#1890FF', fontFamily: 'monospace' }}>+{raisePct}%</span>
          </div>
          <input type="range" min={0} max={30} step={1} value={raisePct} onChange={handleSliderChange}
            style={{ width: '100%', height: 6, borderRadius: 3, appearance: 'none', cursor: 'pointer', background: `linear-gradient(90deg, #1890FF ${raisePct / 30 * 100}%, rgba(255,255,255,0.1) ${raisePct / 30 * 100}%)` }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#555', marginTop: 4 }}>
            <span>0%</span><span>15%</span><span>30%</span>
          </div>
          <div style={{ marginTop: 12, padding: '8px 12px', background: 'rgba(24,144,255,0.08)', borderRadius: 6, fontSize: 12, color: '#889' }}>
            调薪金额: <strong style={{ color: '#1890FF' }}>+¥{raiseAmount.toFixed(0)}</strong>/月 → 新月薪: <strong style={{ color: '#1890FF' }}>¥{newSalary.toFixed(0)}</strong>/月
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: '20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 20 }}>
          <div style={{ fontSize: 12, color: '#888', marginBottom: 14 }}>实时联动看板</div>
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div style={{ flex: 1, textAlign: 'center', padding: '12px 8px', background: 'rgba(255,77,79,0.08)', borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>调薪前风险</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#FF4D4F', fontFamily: 'monospace' }}>{currentProbPct}%</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', color: '#555' }}>
              <svg width="20" height="12" viewBox="0 0 20 12"><path d="M0 6 L20 6 M14 2 L20 6 L14 10" stroke="#555" strokeWidth="1.5" fill="none" /></svg>
            </div>
            <div style={{ flex: 1, textAlign: 'center', padding: '12px 8px', background: `rgba(82,196,26,${effectiveResult.proposed_turnover_prob < 0.3 ? 0.12 : 0.06})`, borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: '#888', marginBottom: 4 }}>调薪后风险</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: effectiveResult.proposed_turnover_prob < 0.3 ? '#52C41A' : '#FA8C16', fontFamily: 'monospace' }}>{newProbPct}%</div>
            </div>
          </div>
          {raisePct > 0 && (
            <div style={{ textAlign: 'center', fontSize: 12, color: '#52C41A', marginBottom: 14 }}>
              ▼ 离职概率预计下降 <strong>{pctDrop}%</strong>
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: '企业即期投入', value: `¥${effectiveResult.investment_cost.toLocaleString()}`, color: '#FA8C16' },
              { label: '预期流失挽回收益', value: `+¥${effectiveResult.benefit.toLocaleString()}`, color: '#52C41A' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6, fontSize: 12 }}>
                <span style={{ color: '#888' }}>{item.label}</span>
                <span style={{ color: item.color, fontWeight: 600, fontFamily: 'monospace' }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: '20px', border: '1px solid rgba(255,255,255,0.06)', marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 10 }}>多重干预手段 <span style={{ fontSize: 9, color: '#555' }}>(勾选后叠加效果)</span></div>
          {Object.entries(interventionLabels).map(([key, label]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0', fontSize: 12, cursor: 'pointer', color: interventions[key] ? '#ccc' : '#666' }}>
              <input type="checkbox" checked={interventions[key]} onChange={() => toggleIntervention(key)}
                style={{ accentColor: '#1890FF' }} />
              {label}
            </label>
          ))}
          {extraBoost > 0 && (
            <div style={{ marginTop: 6, fontSize: 11, color: '#52C41A' }}>
              + 非调薪手段预计额外降低离职概率 <strong>{(extraBoost * 100).toFixed(0)}%</strong>
            </div>
          )}
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 12, padding: '24px 20px', border: `1px solid ${effectiveResult.is_preferred_decision ? 'rgba(82,196,26,0.3)' : 'rgba(250,140,22,0.3)'}`, textAlign: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 8 }}>最终判定：净节约金额 (Net Savings)</div>
          <div style={{ fontSize: 32, fontWeight: 700, fontFamily: 'monospace', color: effectiveResult.is_preferred_decision ? '#52C41A' : '#FA8C16' }}>
            ¥{effectiveResult.net_savings.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
          <div style={{ marginTop: 12, padding: '8px 16px', borderRadius: 6, display: 'inline-block', fontSize: 13, fontWeight: 600, letterSpacing: 1,
            background: effectiveResult.is_preferred_decision ? 'rgba(82,196,26,0.12)' : 'rgba(250,140,22,0.12)',
            border: `1px solid ${effectiveResult.is_preferred_decision ? '#52C41A44' : '#FA8C1644'}`,
            color: effectiveResult.is_preferred_decision ? '#52C41A' : '#FA8C16' }}>
            {effectiveResult.is_preferred_decision ? '⭐ 优选执行决策' : '建议调和：财务性价比低，请尝试非财务手段'}
          </div>
        </div>

        <div style={{ marginTop: 'auto' }}>
          {interventionDone ? (
            <div>
              <div style={{ padding: '16px', background: 'rgba(82,196,26,0.08)', borderRadius: 8, border: '1px solid rgba(82,196,26,0.2)', textAlign: 'center', marginBottom: 12 }}>
                <div style={{ fontSize: 16, marginBottom: 4 }}>✅</div>
                <div style={{ fontSize: 13, color: '#52C41A', fontWeight: 600 }}>调薪预案已确认，状态机已冻结</div>
                <div style={{ fontSize: 11, color: '#666', marginTop: 4 }}>记录状态: NEW → IN_PROGRESS · 沉默期: 30 天</div>
              </div>
              <button onClick={() => setShowPlaybook(true)}
                style={{ width: '100%', padding: '10px 0', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', border: '1px solid #1890FF44', background: 'rgba(24,144,255,0.1)', color: '#1890FF' }}>
                📋 查看定制化留任行动剧本
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 12 }}>
              <button onClick={async () => {
                if (raisePct === 0) return;
                try { await createIntervention(employeeId, raisePct / 100); } catch {}
                setInterventionDone(true);
                setPlaybookLoading(true);
                try {
                  const resp = await fetchPlaybook(employeeId);
                  if (resp?.code === 200) setPlaybookContent(resp.data.markdown_content);
                } catch {}
                setPlaybookLoading(false);
              }} disabled={raisePct === 0}
                style={{ flex: 1, padding: '12px 0', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', border: 'none',
                  background: raisePct === 0 ? 'rgba(255,255,255,0.05)' : 'linear-gradient(135deg, #52C41A, #389E0D)',
                  color: raisePct === 0 ? '#555' : '#fff' }}>
                确认执行调薪预案并冻结快照
              </button>
              <button onClick={onBack} style={{ padding: '12px 16px', borderRadius: 8, fontSize: 12, cursor: 'pointer', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#888' }}>返回</button>
            </div>
          )}
          {/* PDF 导出按钮 */}
          <button onClick={() => window.open(`${window.location.hostname === 'localhost' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`}/api/v1/ona/report/${employeeId}`, '_blank')}
            style={{ width: '100%', marginTop: 12, padding: '10px 0', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
              border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.04)', color: '#aaa' }}>
            📄 导出留任建议书 (PDF)
          </button>
        </div>
      </div>

      {/* Playbook Drawer */}
      {showPlaybook && (
        <div onClick={() => setShowPlaybook(false)}
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200, display: 'flex', justifyContent: 'flex-end', animation: 'fadeIn 0.15s' }}>
          <div onClick={(e) => e.stopPropagation()}
            style={{ width: 520, maxWidth: '90vw', height: '100%', background: '#161624', overflowY: 'auto', padding: '24px 28px', boxShadow: '-4px 0 32px rgba(0,0,0,0.4)', animation: 'slideIn 0.2s' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, position: 'sticky', top: 0, background: '#161624', zIndex: 10, paddingBottom: 12, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#f0f0f0' }}>📋 定制化留任行动剧本</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => { navigator.clipboard.writeText(playbookContent || ''); }}
                  style={{ padding: '6px 12px', borderRadius: 6, fontSize: 11, cursor: 'pointer', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#aaa' }}>一键复制</button>
                <button onClick={() => setShowPlaybook(false)}
                  style={{ padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer', border: 'none', background: 'rgba(255,255,255,0.05)', color: '#888' }}>✕</button>
              </div>
            </div>
            {playbookLoading && !playbookContent ? (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#666' }}>
                <div style={{ fontSize: 24, marginBottom: 12 }}>⏳</div>
                <div>正在基于员工画像生成定制化剧本...</div>
              </div>
            ) : playbookContent ? (
              <PlaybookMarkdown content={playbookContent} />
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#666' }}>暂无剧本数据</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const PlaybookMarkdown = ({ content }) => {
  const rendered = content.split('\n').map((line, i) => {
    if (!line.trim()) return <div key={i} style={{ height: 8 }} />;
    if (line.startsWith('## ')) return <h4 key={i} style={{ color: '#f0f0f0', fontSize: 15, fontWeight: 600, margin: '16px 0 8px' }}>{line.slice(3)}</h4>;
    if (line.startsWith('### ')) return <div key={i} style={{ color: '#ccc', fontSize: 13, fontWeight: 600, margin: '12px 0 6px' }}>{line.slice(4)}</div>;
    if (line.startsWith('> ')) return <blockquote key={i} style={{ margin: '6px 0', padding: '6px 12px', borderLeft: '3px solid #1890FF44', background: 'rgba(24,144,255,0.04)', borderRadius: 4, fontSize: 12, color: '#bbb' }}>{line.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</blockquote>;
    if (line.startsWith('|')) {
      const cells = line.split('|').filter(Boolean).map((c, ci) => <td key={ci} style={{ padding: '6px 8px', fontSize: 11, color: '#ccc', border: '1px solid rgba(255,255,255,0.06)' }}>{c.trim().replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</td>);
      if (line.includes('---')) return null;
      return <table key={i} style={{ width: '100%', borderCollapse: 'collapse', margin: '6px 0', fontSize: 11 }}><tr>{cells}</tr></table>;
    }
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      return <div key={i} style={{ fontSize: 12, color: '#bbb', lineHeight: 1.7, paddingLeft: 16, display: 'flex', gap: 6 }}>
        <span style={{ color: '#1890FF' }}>•</span>
        <span dangerouslySetInnerHTML={{ __html: line.trim().slice(2).replace(/\*\*(.*?)\*\*/g, '<strong style="color:#e0e0e0">$1</strong>') }} />
      </div>;
    }
    if (line.startsWith('---')) return <hr key={i} style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.06)', margin: '12px 0' }} />;
    return <div key={i} style={{ fontSize: 12, color: '#bbb', lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#e0e0e0">$1</strong>') }} />;
  });
  return <div>{rendered}</div>;
};

export default EmployeeDrillDown;
