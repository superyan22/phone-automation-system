/**
 * Tasks Page
 */

import React, { useEffect, useState } from 'react';
import { useTaskStore } from '../../store/taskSlice';
import { Task, TaskStatus } from '../../types/task';

const TasksPage: React.FC = () => {
  const { tasks, isLoading, error, fetchTasks, deleteTask, startTask, cancelTask } = useTaskStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | ''>('');

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleDelete = async (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      await deleteTask(taskId);
    }
  };

  const handleStart = async (taskId: string) => {
    await startTask(taskId);
  };

  const handleCancel = async (taskId: string) => {
    if (window.confirm('Are you sure you want to cancel this task?')) {
      await cancelTask(taskId);
    }
  };

  const filteredTasks = tasks.filter(
    (task) =>
      task.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (!statusFilter || task.status === statusFilter)
  );

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'queued':
        return 'bg-blue-100 text-blue-800';
      case 'running':
        return 'bg-yellow-100 text-yellow-800';
      case 'paused':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-500';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <a
          href="/tasks/create"
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          Create Task
        </a>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Search tasks..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-lg"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as TaskStatus | '')}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="paused">Paused</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {/* Task List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Device
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTasks.map((task) => (
              <TaskRow
                key={task.task_id}
                task={task}
                onDelete={handleDelete}
                onStart={handleStart}
                onCancel={handleCancel}
              />
            ))}
          </tbody>
        </table>

        {filteredTasks.length === 0 && !isLoading && (
          <div className="text-center py-8 text-gray-500">
            No tasks found. Click "Create Task" to create a new task.
          </div>
        )}
      </div>
    </div>
  );
};

// Task Row Component
interface TaskRowProps {
  task: Task;
  onDelete: (taskId: string) => void;
  onStart: (taskId: string) => void;
  onCancel: (taskId: string) => void;
}

const TaskRow: React.FC<TaskRowProps> = ({ task, onDelete, onStart, onCancel }) => {
  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'queued':
        return 'bg-blue-100 text-blue-800';
      case 'running':
        return 'bg-yellow-100 text-yellow-800';
      case 'paused':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-500';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">{task.name}</div>
        <div className="text-sm text-gray-500">{task.task_id.slice(0, 8)}...</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(task.status)}`}>
          {task.status}
        </span>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full"
            style={{ width: `${task.progress}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-1">{task.progress}%</div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {task.device_serial || 'Not assigned'}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {new Date(task.created_at).toLocaleDateString()}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
        <div className="flex gap-2">
          {task.status === 'pending' && (
            <button
              onClick={() => onStart(task.task_id)}
              className="text-green-600 hover:text-green-900"
            >
              Start
            </button>
          )}
          {task.status === 'running' && (
            <button
              onClick={() => onCancel(task.task_id)}
              className="text-red-600 hover:text-red-900"
            >
              Cancel
            </button>
          )}
          {['pending', 'completed', 'failed', 'cancelled'].includes(task.status) && (
            <button
              onClick={() => onDelete(task.task_id)}
              className="text-red-600 hover:text-red-900"
            >
              Delete
            </button>
          )}
          <a
            href={`/tasks/${task.task_id}`}
            className="text-blue-600 hover:text-blue-900"
          >
            View
          </a>
        </div>
      </td>
    </tr>
  );
};

export default TasksPage;
