/**
 * Task types
 */

export type TaskStatus = 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';

export type StepType = 'tap' | 'swipe' | 'input' | 'wait' | 'screenshot' | 'check' | 'launch' | 'back' | 'home' | 'key';

export interface TaskStep {
  name: string;
  type: StepType;
  params: Record<string, any>;
  timeout?: number;
  retry_count?: number;
}

export interface Task {
  id: number;
  task_id: string;
  name: string;
  description?: string;
  task_type: string;
  status: TaskStatus;
  priority: number;
  progress: number;
  steps: TaskStep[];
  params: Record<string, any>;
  config: Record<string, any>;
  device_serial?: string;
  current_step: number;
  retry_count: number;
  max_retries: number;
  result?: Record<string, any>;
  error_message?: string;
  scheduled_at?: string;
  timeout_seconds: number;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
}

export interface TaskCreateParams {
  name: string;
  description?: string;
  task_type?: string;
  steps: TaskStep[];
  params?: Record<string, any>;
  config?: Record<string, any>;
  device_serial?: string;
  priority?: number;
  max_retries?: number;
  scheduled_at?: string;
  timeout_seconds?: number;
}

export interface TaskStatistics {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  success_rate: number;
  avg_duration_seconds?: number;
}

export interface TaskLog {
  id: number;
  level: string;
  step_index?: number;
  step_name?: string;
  message: string;
  details?: Record<string, any>;
  screenshot_path?: string;
  duration_ms?: number;
  created_at: string;
}
