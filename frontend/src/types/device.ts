/**
 * Device types
 */

export interface Device {
  id: number;
  serial: string;
  device_type: 'usb' | 'wifi';
  ip_address?: string;
  port: number;
  model?: string;
  brand?: string;
  android_version?: string;
  screen_width?: number;
  screen_height?: number;
  screen_density: number;
  status: 'online' | 'offline' | 'busy' | 'error';
  is_connected: boolean;
  last_heartbeat?: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
  connected_at?: string;
}

export interface DeviceListResponse {
  items: Device[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeviceCommandRequest {
  command: string;
  args?: string[];
  timeout?: number;
}

export interface DeviceCommandResponse {
  success: boolean;
  output: string;
  error?: string;
}
