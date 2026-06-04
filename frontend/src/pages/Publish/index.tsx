/**
 * 一键发布小红书页面 - Mobile Optimized
 */

import React, { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '/api/v1';

interface PublishTask {
  id: string;
  status: string;
  progress: number;
  current_step: string | null;
  title: string | null;
  images: string[];
  screenshot: string | null;
  error: string | null;
}

const STATUS_MAP: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  pending: { label: '等待中', color: 'text-gray-600', bg: 'bg-gray-100', icon: '⏳' },
  data_fetching: { label: '抓取数据', color: 'text-blue-600', bg: 'bg-blue-100', icon: '📊' },
  image_generating: { label: '生成图片', color: 'text-purple-600', bg: 'bg-purple-100', icon: '🖼️' },
  pushing_to_phone: { label: '推送手机', color: 'text-yellow-600', bg: 'bg-yellow-100', icon: '📱' },
  publishing: { label: '发布中', color: 'text-orange-600', bg: 'bg-orange-100', icon: '🚀' },
  completed: { label: '已完成', color: 'text-green-600', bg: 'bg-green-100', icon: '✅' },
  failed: { label: '失败', color: 'text-red-600', bg: 'bg-red-100', icon: '❌' },
};

const PublishPage: React.FC = () => {
  const [task, setTask] = useState<PublishTask | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connectWebSocket = useCallback((taskId: string) => {
    const wsUrl = API_URL.replace('http', 'ws').replace('/api/v1', '') + `/ws/publish/${taskId}`;
    const newWs = new WebSocket(wsUrl);

    newWs.onopen = () => console.log('WebSocket connected');
    newWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        setTask(prev => prev ? {
          ...prev,
          status: data.status,
          progress: data.progress,
          current_step: data.current_step,
          screenshot: data.screenshot || prev.screenshot
        } : null);
      } else if (data.type === 'complete') {
        setTask(prev => prev ? {
          ...prev,
          status: data.status,
          screenshot: data.screenshot,
          error: data.error
        } : null);
      }
    };
    newWs.onerror = (error) => console.error('WebSocket error:', error);
    newWs.onclose = () => console.log('WebSocket closed');
    setWs(newWs);
    return newWs;
  }, []);

  useEffect(() => {
    return () => { if (ws) ws.close(); };
  }, [ws]);

  const handleStartPublish = async () => {
    setIsStarting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/publish/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': localStorage.getItem('phone_auto_api_key') || ''
        },
        body: JSON.stringify({
          data_source: 'latest',
          phone_serial: '192.168.31.177:37107'
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || '启动失败');
      }

      const result = await response.json();
      setTask({
        id: result.task_id,
        status: 'pending',
        progress: 0,
        current_step: '准备中...',
        title: null,
        images: [],
        screenshot: null,
        error: null
      });
      connectWebSocket(result.task_id);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsStarting(false);
    }
  };

  const statusInfo = task ? (STATUS_MAP[task.status] || STATUS_MAP.pending) : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部标题区域 - 突出一键发布 */}
      <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white p-6 text-center">
        <h1 className="text-2xl font-bold mb-2">🚀 一键发布小红书</h1>
        <p className="text-red-100 text-sm">自动抓取 · 生成图片 · 一键发布</p>
      </div>

      <div className="p-4 max-w-lg mx-auto">
        {/* 主操作卡片 */}
        <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
          <p className="text-gray-600 mb-4 text-sm">
            点击按钮，系统将自动完成：
          </p>
          <div className="grid grid-cols-2 gap-3 mb-5">
            {[
              { icon: '📊', label: '抓取数据' },
              { icon: '🖼️', label: '生成图片' },
              { icon: '📱', label: '推送手机' },
              { icon: '🚀', label: '自动发布' },
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2">
                <span className="text-lg">{step.icon}</span>
                <span className="text-sm text-gray-700">{step.label}</span>
              </div>
            ))}
          </div>

          {/* 发布按钮 - 大按钮，触摸友好 */}
          <button
            onClick={handleStartPublish}
            disabled={isStarting || (task !== null && !['completed', 'failed'].includes(task.status))}
            className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all ${
              isStarting || (task !== null && !['completed', 'failed'].includes(task.status))
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-red-500 to-pink-500 text-white shadow-lg hover:shadow-xl active:scale-95'
            }`}
          >
            {isStarting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                启动中...
              </span>
            ) : '🚀 一键发布'}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              ❌ {error}
            </div>
          )}
        </div>

        {/* 任务进度卡片 */}
        {task && (
          <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
            {/* 状态头部 */}
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-full ${statusInfo?.bg} flex items-center justify-center text-xl`}>
                {statusInfo?.icon}
              </div>
              <div className="flex-1">
                <div className={`font-semibold ${statusInfo?.color}`}>{statusInfo?.label}</div>
                {task.current_step && (
                  <div className="text-sm text-gray-500 mt-0.5">{task.current_step}</div>
                )}
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-800">{task.progress}%</div>
              </div>
            </div>

            {/* 进度条 */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${task.progress}%` }}
              />
            </div>

            {/* 步骤列表 */}
            <div className="space-y-2">
              {[
                { key: 'data_fetching', label: '数据抓取', icon: '📊' },
                { key: 'image_generating', label: '图片生成', icon: '🖼️' },
                { key: 'pushing_to_phone', label: 'ADB推送', icon: '📱' },
                { key: 'publishing', label: '小红书发布', icon: '🚀' },
              ].map((step, index) => {
                const currentIndex = ['data_fetching', 'image_generating', 'pushing_to_phone', 'publishing'].indexOf(task.status);
                const isCompleted = index < currentIndex || task.status === 'completed';
                const isCurrent = step.key === task.status;

                return (
                  <div
                    key={step.key}
                    className={`flex items-center gap-3 p-3 rounded-lg ${
                      isCompleted ? 'bg-green-50' :
                      isCurrent ? 'bg-blue-50' :
                      'bg-gray-50'
                    }`}
                  >
                    <span className="text-lg">{step.icon}</span>
                    <span className={`flex-1 text-sm font-medium ${
                      isCompleted ? 'text-green-700' :
                      isCurrent ? 'text-blue-700' :
                      'text-gray-500'
                    }`}>
                      {step.label}
                    </span>
                    <span className="text-lg">
                      {isCompleted ? '✅' : isCurrent ? '🔄' : '⏳'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 截图预览 */}
        {task?.screenshot && (
          <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <span>📱</span> 发布截图
            </h3>
            <div className="border rounded-lg overflow-hidden">
              <img
                src={`${API_URL.replace('/api/v1', '')}/screenshots/${task.screenshot.split('/').pop()}`}
                alt="发布截图"
                className="w-full"
              />
            </div>
          </div>
        )}

        {/* 失败信息 */}
        {task?.error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
            <p className="text-red-700 font-semibold">❌ 发布失败</p>
            <p className="text-red-600 text-sm mt-1">{task.error}</p>
          </div>
        )}

        {/* 重新发布按钮 */}
        {task?.status === 'completed' && (
          <button
            onClick={() => { setTask(null); setError(null); }}
            className="w-full py-3 px-4 border-2 border-gray-300 rounded-xl text-gray-700 font-medium hover:bg-gray-50 active:bg-gray-100 transition-colors"
          >
            🔄 发布新内容
          </button>
        )}
      </div>
    </div>
  );
};

export default PublishPage;
