/**
 * Task Store
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Task, TaskStatus, TaskCreateParams } from '../types/task';
import { apiService } from '../services/api';

interface TaskState {
  // State
  tasks: Task[];
  selectedTask: Task | null;
  taskLogs: Record<string, any[]>;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchTasks: (params?: any) => Promise<void>;
  fetchTask: (taskId: string) => Promise<void>;
  createTask: (params: TaskCreateParams) => Promise<Task>;
  updateTask: (taskId: string, params: Partial<Task>) => Promise<void>;
  deleteTask: (taskId: string | number) => Promise<void>;
  startTask: (taskId: string | number) => Promise<void>;
  pauseTask: (taskId: string) => Promise<void>;
  resumeTask: (taskId: string) => Promise<void>;
  cancelTask: (taskId: string | number) => Promise<void>;
  selectTask: (taskId: string) => void;
  updateTaskProgress: (taskId: string, progress: number, currentStep: number) => void;
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
  addTaskLog: (taskId: string, log: any) => void;
  clearError: () => void;
}

export const useTaskStore = create<TaskState>()(
  devtools(
    (set, get) => ({
      // Initial state
      tasks: [],
      selectedTask: null,
      taskLogs: {},
      isLoading: false,
      error: null,

      // Fetch tasks
      fetchTasks: async (params = {}) => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiService.getTasks(params);
          set({ tasks: response.items, isLoading: false });
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || error.message,
            isLoading: false,
          });
        }
      },

      // Fetch single task
      fetchTask: async (taskId: string) => {
        try {
          const task = await apiService.getTask(taskId);
          set({ selectedTask: task });
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Create task
      createTask: async (params: TaskCreateParams) => {
        set({ isLoading: true });
        try {
          const task = await apiService.createTask(params);
          set((state) => ({
            tasks: [task, ...state.tasks],
            isLoading: false,
          }));
          return task;
        } catch (error: any) {
          set({
            error: error.response?.data?.detail || error.message,
            isLoading: false,
          });
          throw error;
        }
      },

      // Update task
      updateTask: async (taskId: string, params: Partial<Task>) => {
        try {
          const task = await apiService.updateTask(taskId, params);
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.task_id === taskId ? task : t
            ),
            selectedTask:
              state.selectedTask?.task_id === taskId
                ? task
                : state.selectedTask,
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Delete task
      deleteTask: async (taskId: string | number) => {
        try {
          await apiService.deleteTask(taskId);
          set((state) => ({
            tasks: state.tasks.filter((t) => t.task_id !== taskId),
            selectedTask:
              state.selectedTask?.task_id === taskId
                ? null
                : state.selectedTask,
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Start task
      startTask: async (taskId: string | number) => {
        try {
          await apiService.startTask(taskId);
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.task_id === taskId
                ? { ...t, status: 'running' as TaskStatus }
                : t
            ),
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Pause task
      pauseTask: async (taskId: string) => {
        try {
          await apiService.pauseTask(taskId);
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.task_id === taskId
                ? { ...t, status: 'paused' as TaskStatus }
                : t
            ),
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Resume task
      resumeTask: async (taskId: string) => {
        try {
          await apiService.resumeTask(taskId);
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.task_id === taskId
                ? { ...t, status: 'running' as TaskStatus }
                : t
            ),
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Cancel task
      cancelTask: async (taskId: string | number) => {
        try {
          await apiService.cancelTask(taskId);
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.task_id === taskId
                ? { ...t, status: 'cancelled' as TaskStatus }
                : t
            ),
          }));
        } catch (error: any) {
          set({ error: error.response?.data?.detail || error.message });
        }
      },

      // Select task
      selectTask: (taskId: string) => {
        const task = get().tasks.find((t) => t.task_id === taskId);
        set({ selectedTask: task || null });
      },

      // Update task progress (from WebSocket)
      updateTaskProgress: (taskId: string, progress: number, currentStep: number) => {
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.task_id === taskId
              ? { ...t, progress, current_step: currentStep }
              : t
          ),
          selectedTask:
            state.selectedTask?.task_id === taskId
              ? { ...state.selectedTask, progress, current_step: currentStep }
              : state.selectedTask,
        }));
      },

      // Update task status (from WebSocket)
      updateTaskStatus: (taskId: string, status: TaskStatus) => {
        set((state) => ({
          tasks: state.tasks.map((t) =>
            t.task_id === taskId ? { ...t, status } : t
          ),
          selectedTask:
            state.selectedTask?.task_id === taskId
              ? { ...state.selectedTask, status }
              : state.selectedTask,
        }));
      },

      // Add task log (from WebSocket)
      addTaskLog: (taskId: string, log: any) => {
        set((state) => ({
          taskLogs: {
            ...state.taskLogs,
            [taskId]: [...(state.taskLogs[taskId] || []), log],
          },
        }));
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },
    })
  )
);
