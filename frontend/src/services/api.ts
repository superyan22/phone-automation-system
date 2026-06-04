/**
 * API Service
 */

import axios, { AxiosInstance } from 'axios';
import { Device, DeviceListResponse, DeviceCommandResponse } from '../types/device';
import { Task, TaskListResponse, TaskCreateParams, TaskStatistics, TaskLog } from '../types/task';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || '/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        return Promise.reject(error);
      }
    );
  }

  // ========== Device API ==========

  async getDevices(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    device_type?: string;
    search?: string;
  }): Promise<DeviceListResponse> {
    const response = await this.api.get('/devices', { params });
    return response.data;
  }

  async getDevice(serial: string): Promise<Device> {
    const response = await this.api.get(`/devices/${serial}`);
    return response.data;
  }

  async scanDevices(scanType: string = 'usb', subnet?: string): Promise<Device[]> {
    const response = await this.api.post('/devices/scan', null, {
      params: { scan_type: scanType, subnet },
    });
    return response.data;
  }

  async connectDevice(serial: string): Promise<Device> {
    const response = await this.api.post(`/devices/${serial}/connect`);
    return response.data;
  }

  async disconnectDevice(serial: string): Promise<Device> {
    const response = await this.api.post(`/devices/${serial}/disconnect`);
    return response.data;
  }

  async executeCommand(
    serial: string,
    command: string,
    args?: string[],
    timeout?: number
  ): Promise<DeviceCommandResponse> {
    const response = await this.api.post(`/devices/${serial}/command`, {
      command,
      args: args || [],
      timeout: timeout || 30,
    });
    return response.data;
  }

  async getScreenshot(serial: string, format?: string): Promise<{ image: string }> {
    const response = await this.api.get(`/devices/${serial}/screenshot`, {
      params: { format },
    });
    return response.data;
  }

  // ========== Task API ==========

  async getTasks(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    task_type?: string;
    device_serial?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
  }): Promise<TaskListResponse> {
    const response = await this.api.get('/tasks', { params });
    return response.data;
  }

  async getTask(taskId: string): Promise<Task> {
    const response = await this.api.get(`/tasks/${taskId}`);
    return response.data;
  }

  async createTask(params: TaskCreateParams): Promise<Task> {
    const response = await this.api.post('/tasks', params);
    return response.data;
  }

  async updateTask(taskId: string, params: Partial<Task>): Promise<Task> {
    const response = await this.api.put(`/tasks/${taskId}`, params);
    return response.data;
  }

  async deleteTask(taskId: string | number): Promise<void> {
    await this.api.delete(`/tasks/${taskId}`);
  }

  async startTask(taskId: string | number): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tasks/${taskId}/start`);
    return response.data;
  }

  async pauseTask(taskId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tasks/${taskId}/pause`);
    return response.data;
  }

  async resumeTask(taskId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tasks/${taskId}/resume`);
    return response.data;
  }

  async cancelTask(taskId: string | number): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tasks/${taskId}/cancel`);
    return response.data;
  }

  async retryTask(taskId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.api.post(`/tasks/${taskId}/retry`);
    return response.data;
  }

  async getTaskStatistics(): Promise<TaskStatistics> {
    const response = await this.api.get('/tasks/statistics');
    return response.data;
  }

  async getTaskLogs(
    taskId: string,
    params?: {
      level?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<{ items: TaskLog[]; total: number }> {
    const response = await this.api.get(`/tasks/${taskId}/logs`, { params });
    return response.data;
  }
}

export const apiService = new ApiService();
