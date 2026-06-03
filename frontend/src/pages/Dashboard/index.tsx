/**
 * Dashboard Page
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
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Devices"
          value={devices.length}
          subtitle={`${onlineDevices} online`}
          color="blue"
        />
        <StatCard
          title="Total Tasks"
          value={tasks.length}
          subtitle={`${runningTasks} running`}
          color="green"
        />
        <StatCard
          title="Success Rate"
          value={statistics ? `${statistics.success_rate}%` : 'N/A'}
          subtitle={`${statistics?.completed || 0} completed`}
          color="purple"
        />
        <StatCard
          title="Avg Duration"
          value={statistics?.avg_duration_seconds 
            ? `${Math.round(statistics.avg_duration_seconds)}s`
            : 'N/A'
          }
          subtitle="per task"
          color="orange"
        />
      </div>

      {/* Recent Devices */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Recent Devices</h2>
        <div className="space-y-3">
          {devices.slice(0, 5).map((device) => (
            <div
              key={device.serial}
              className="flex justify-between items-center p-3 bg-gray-50 rounded"
            >
              <div>
                <p className="font-medium">{device.model || device.serial}</p>
                <p className="text-sm text-gray-500">{device.serial}</p>
              </div>
              <StatusBadge status={device.status} />
            </div>
          ))}
          {devices.length === 0 && (
            <p className="text-gray-500 text-center py-4">No devices connected</p>
          )}
        </div>
      </div>

      {/* Recent Tasks */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Tasks</h2>
        <div className="space-y-3">
          {tasks.slice(0, 5).map((task) => (
            <div
              key={task.task_id}
              className="flex justify-between items-center p-3 bg-gray-50 rounded"
            >
              <div>
                <p className="font-medium">{task.name}</p>
                <p className="text-sm text-gray-500">
                  {new Date(task.created_at).toLocaleDateString()}
                </p>
              </div>
              <StatusBadge status={task.status} />
            </div>
          ))}
          {tasks.length === 0 && (
            <p className="text-gray-500 text-center py-4">No tasks created</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Stat Card Component
interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`w-12 h-12 ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
          <span className="text-white text-xl font-bold">
            {typeof value === 'number' ? value : value.charAt(0)}
          </span>
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

// Status Badge Component
interface StatusBadgeProps {
  status: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'offline':
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'running':
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'paused':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(status)}`}>
      {status}
    </span>
  );
};

export default DashboardPage;
