/**
 * Dashboard Page - Chinese Version
 */

import React, { useEffect, useState } from 'react';
import { useDeviceStore } from '../../store/deviceSlice';
import { useTaskStore } from '../../store/taskSlice';
import { apiService } from '../../services/api';
import { TaskStatistics } from '../../types/task';

const DashboardPage: React.FC = () => {
  const { devices, fetchDevices } = useDeviceStore();
  const { tasks, fetchTasks } = useTaskStore();
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);

  useEffect(() => {
    fetchDevices();
    fetchTasks();
    loadStatistics();
  }, [fetchDevices, fetchTasks]);

  const loadStatistics = async () => {
    try {
      const stats = await apiService.getTaskStatistics();
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const onlineDevices = devices.filter((d) => d.status === 'online').length;
  const runningTasks = tasks.filter((t) => t.status === 'running').length;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">📊 仪表盘</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="设备总数"
          value={devices.length}
          subtitle={`${onlineDevices} 在线`}
          color="blue"
        />
        <StatCard
          title="任务总数"
          value={tasks.length}
          subtitle={`${runningTasks} 运行中`}
          color="green"
        />
        <StatCard
          title="成功率"
          value={statistics ? `${statistics.success_rate || 0}%` : '-'}
          subtitle="任务完成率"
          color="purple"
        />
        <StatCard
          title="系统状态"
          value="正常"
          subtitle="所有服务运行中"
          color="emerald"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">最近活动</h2>
        <div className="space-y-3">
          {tasks.slice(0, 5).map((task) => (
            <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">{task.name}</p>
                <p className="text-sm text-gray-500">{task.device_serial}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                task.status === 'completed' ? 'bg-green-100 text-green-800' :
                task.status === 'running' ? 'bg-blue-100 text-blue-800' :
                task.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {task.status === 'completed' ? '已完成' :
                 task.status === 'running' ? '运行中' :
                 task.status === 'failed' ? '失败' : '等待中'}
              </span>
            </div>
          ))}
          {tasks.length === 0 && (
            <p className="text-center text-gray-500 py-4">暂无活动记录</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle: string;
  color: string;
}> = ({ title, value, subtitle, color }) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    emerald: 'bg-emerald-500',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`w-12 h-12 ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          <span className="text-white text-xl">📱</span>
        </div>
        <div className="ml-4">
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-gray-400">{subtitle}</p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
