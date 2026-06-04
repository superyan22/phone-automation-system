/**
 * Main App Component - Mobile Optimized Chinese Version
 */

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import DashboardPage from './pages/Dashboard';
import DevicesPage from './pages/Devices';
import TasksPage from './pages/Tasks';
import PhonePage from './pages/Phone';
import PublishPage from './pages/Publish';

// 底部导航栏组件
const BottomNav: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: '📊', label: '仪表盘' },
    { path: '/devices', icon: '📱', label: '设备' },
    { path: '/publish', icon: '🚀', label: '一键发布' },
    { path: '/phone', icon: '🎮', label: '控制' },
    { path: '/tasks', icon: '📋', label: '任务' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 md:hidden z-50">
      <div className="flex justify-around items-center h-16">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center flex-1 h-full ${
                isActive ? 'text-blue-600' : 'text-gray-500'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-xs mt-1">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

// 桌面端顶部导航
const DesktopNav: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  return (
    <nav className="bg-white shadow hidden md:block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-blue-600">
                📱 手机自动化控制
              </Link>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link to="/" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                仪表盘
              </Link>
              <Link to="/devices" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                设备管理
              </Link>
              <Link to="/tasks" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                任务管理
              </Link>
              <Link to="/phone" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                手机控制
              </Link>
              <Link to="/publish" className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300">
                一键发布
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <button onClick={onLogout} className="text-sm text-gray-500 hover:text-gray-700">
              退出登录
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

const App: React.FC = () => {
  const [apiKey, setApiKey] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const savedKey = localStorage.getItem('phone_auto_api_key');
    if (savedKey) {
      setApiKey(savedKey);
      setIsAuthenticated(true);
    }
  }, []);

  const handleApiKeySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKey.trim()) {
      localStorage.setItem('phone_auto_api_key', apiKey.trim());
      setIsAuthenticated(true);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('phone_auto_api_key');
    setApiKey('');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="bg-white p-6 sm:p-8 rounded-lg shadow-md w-full max-w-sm">
          <h1 className="text-xl sm:text-2xl font-bold text-center mb-6 text-blue-600">
            📱 手机自动化控制系统
          </h1>
          <form onSubmit={handleApiKeySubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 text-sm font-bold mb-2">
                API 密钥
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-base"
                placeholder="请输入您的 API 密钥"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 transition-colors text-base font-medium"
            >
              登录
            </button>
          </form>
          <p className="mt-4 text-sm text-gray-500 text-center">
            首次使用？请联系管理员获取 API 密钥
          </p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <DesktopNav onLogout={handleLogout} />
        
        {/* 移动端顶部标题栏 */}
        <div className="md:hidden bg-white shadow sticky top-0 z-40">
          <div className="px-4 py-3 flex justify-between items-center">
            <h1 className="text-lg font-bold text-blue-600">📱 手机自动化控制</h1>
            <button onClick={handleLogout} className="text-sm text-gray-500">
              退出
            </button>
          </div>
        </div>

        {/* 主内容区域 - 移动端留出底部导航空间 */}
        <main className="pb-20 md:pb-0">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/devices" element={<DevicesPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/phone" element={<PhonePage apiKey={apiKey} />} />
            <Route path="/publish" element={<PublishPage />} />
          </Routes>
        </main>

        <BottomNav />
      </div>
    </Router>
  );
};

export default App;
