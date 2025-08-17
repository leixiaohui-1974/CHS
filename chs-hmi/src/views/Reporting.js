import React, { useState, useEffect } from 'react';
import { generateReport, fetchReportStatus } from '../services/apiService';

const Reporting = () => {
  const [reportType, setReportType] = useState('daily_summary');
  const [dateRange, setDateRange] = useState('2025-08-15');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [taskInfo, setTaskInfo] = useState(null);

  useEffect(() => {
    let intervalId = null;

    if (taskInfo && taskInfo.taskId && taskInfo.status === 'PENDING') {
      intervalId = setInterval(async () => {
        try {
          const statusResult = await fetchReportStatus(taskInfo.taskId);
          setTaskInfo(prev => ({ ...prev, status: statusResult.status }));

          if (statusResult.status === 'SUCCESS') {
            setTaskInfo(prev => ({ ...prev, downloadUrl: statusResult.download_url }));
            clearInterval(intervalId);
          } else if (statusResult.status === 'FAILED') {
            setError('Report generation failed.');
            clearInterval(intervalId);
          }
        } catch (err) {
          setError(err.message);
          clearInterval(intervalId);
        }
      }, 3000); // Poll every 3 seconds
    }

    return () => clearInterval(intervalId);
  }, [taskInfo]);

  const handleGenerateReport = async () => {
    setIsLoading(true);
    setError('');
    setTaskInfo(null);
    try {
      const result = await generateReport(reportType, dateRange);
      setTaskInfo({ taskId: result.task_id || `mock-task-${Date.now()}`, status: 'PENDING', downloadUrl: null });
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formContainerStyle = {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '30px',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    backgroundColor: 'white',
  };

  const formGroupStyle = {
    marginBottom: '20px',
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 'bold',
  };

  const selectStyle = {
    width: '100%',
    padding: '10px',
    borderRadius: '4px',
    border: '1px solid #ccc',
  };

  const inputStyle = {
    width: '100%',
    padding: '10px',
    borderRadius: '4px',
    border: '1px solid #ccc',
    boxSizing: 'border-box',
  };

  const buttonStyle = {
    width: '100%',
    padding: '12px',
    borderRadius: '4px',
    border: 'none',
    backgroundColor: '#0056b3',
    color: 'white',
    fontSize: '16px',
    cursor: 'pointer',
    opacity: (isLoading || (taskInfo && taskInfo.status === 'PENDING')) ? 0.7 : 1,
  };

  const infoStyle = {
    marginTop: '20px',
    padding: '15px',
    borderRadius: '4px',
    backgroundColor: '#e9ecef',
    borderLeft: '5px solid #007bff'
  };

  const downloadLinkStyle = {
    display: 'inline-block',
    marginTop: '10px',
    padding: '10px 15px',
    backgroundColor: '#28a745',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px',
    fontWeight: 'bold',
  };

  return (
    <div style={formContainerStyle}>
      <h2>报告中心</h2>
      <div style={formGroupStyle}>
        <label htmlFor="reportType" style={labelStyle}>报告类型</label>
        <select
          id="reportType"
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
          style={selectStyle}
        >
          <option value="daily_summary">每日运行摘要</option>
          <option value="monthly_alarms">月度告警统计</option>
        </select>
      </div>
      <div style={formGroupStyle}>
        <label htmlFor="dateRange" style={labelStyle}>日期范围</label>
        <input
          type="text"
          id="dateRange"
          value={dateRange}
          onChange={(e) => setDateRange(e.target.value)}
          style={inputStyle}
        />
      </div>
      <button onClick={handleGenerateReport} disabled={isLoading || (taskInfo && taskInfo.status === 'PENDING')} style={buttonStyle}>
        {isLoading ? '正在请求...' : (taskInfo && taskInfo.status === 'PENDING' ? '正在生成报告...' : '生成报告')}
      </button>
      {error && <p style={{ color: 'red', marginTop: '15px' }}>{error}</p>}
      {taskInfo && (
        <div style={infoStyle}>
          <p><strong>报告任务已启动</strong></p>
          <p>任务ID: {taskInfo.taskId}</p>
          <p>状态: <strong>{taskInfo.status}</strong></p>
          {taskInfo.downloadUrl && (
            <a href={taskInfo.downloadUrl} style={downloadLinkStyle} target="_blank" rel="noopener noreferrer">
              下载报告
            </a>
          )}
        </div>
      )}
    </div>
  );
};

export default Reporting;
