import React, { useState, useRef } from 'react';
import { uploadCsv } from '../api/ona';

const DataUploadModal = ({ onClose }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  const handleFileChange = (e) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await uploadCsv(file);
      if (resp?.code === 200) {
        setResult(resp.data);
      } else {
        setError(resp?.message || '上传失败');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '上传请求失败');
    }
    setUploading(false);
  };

  return (
    <div onClick={onClose}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()}
        style={{ background: '#1a1a2e', borderRadius: 12, padding: '28px 32px', width: 480, maxWidth: '90vw', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 40px rgba(0,0,0,0.4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#f0f0f0' }}>📤 批量导入员工数据</h3>
          <button onClick={onClose} style={{ padding: '4px 10px', borderRadius: 4, border: 'none', background: 'rgba(255,255,255,0.05)', color: '#888', fontSize: 14, cursor: 'pointer' }}>✕</button>
        </div>

        {/* 拖拽区 */}
        <div style={{
          border: '2px dashed rgba(255,255,255,0.15)', borderRadius: 8, padding: '24px 16px',
          textAlign: 'center', cursor: 'pointer', marginBottom: 16,
          background: file ? 'rgba(24,144,255,0.06)' : 'transparent',
        }} onClick={() => fileRef.current?.click()}>
          <div style={{ fontSize: 12, color: file ? '#1890FF' : '#888', marginBottom: 4 }}>
            {file ? file.name : '拖拽或点击选择 CSV / Excel 文件'}
          </div>
          <div style={{ fontSize: 10, color: '#555' }}>支持 .csv / .xlsx 格式 · 表头需匹配标准字段</div>
          <input ref={fileRef} type="file" accept=".csv,.xlsx" onChange={handleFileChange} style={{ display: 'none' }} />
        </div>

        {/* 上传按钮 */}
        <button onClick={handleUpload} disabled={!file || uploading}
          style={{ width: '100%', padding: '10px 0', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: (!file || uploading) ? 'not-allowed' : 'pointer', border: 'none',
            background: (!file || uploading) ? 'rgba(255,255,255,0.05)' : 'linear-gradient(135deg, #1890FF, #096DD9)',
            color: (!file || uploading) ? '#555' : '#fff', marginBottom: 12 }}>
          {uploading ? '⏳ 上传中...' : '开始导入'}
        </button>

        {/* 结果 */}
        {result && (
          <div style={{ padding: '12px 14px', background: 'rgba(82,196,26,0.08)', borderRadius: 8, border: '1px solid rgba(82,196,26,0.2)' }}>
            <div style={{ fontSize: 13, color: '#52C41A', fontWeight: 600, marginBottom: 4 }}>✅ 导入完成</div>
            <div style={{ fontSize: 11, color: '#aaa', lineHeight: 1.6 }}>
              总行数: {result.total_rows}<br />
              成功插入: {result.inserted_rows}<br />
              跳过/错误: {result.skipped_rows}
            </div>
            {result.errors?.length > 0 && (
              <div style={{ marginTop: 6, fontSize: 10, color: '#FA8C16' }}>
                {result.errors.slice(0, 3).map((e, i) => <div key={i}>{e}</div>)}
              </div>
            )}
          </div>
        )}

        {/* 错误 */}
        {error && (
          <div style={{ padding: '12px 14px', background: 'rgba(255,77,79,0.08)', borderRadius: 8, border: '1px solid rgba(255,77,79,0.2)' }}>
            <div style={{ fontSize: 12, color: '#FF4D4F' }}>❌ {error}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataUploadModal;
