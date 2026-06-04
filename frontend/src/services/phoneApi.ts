/**
 * Phone Control API Service
 * Direct phone interaction functions (tap, swipe, type, etc.)
 */

import axios, { AxiosInstance } from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const phoneApiInstance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
phoneApiInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
phoneApiInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Phone API Error:', error);
    return Promise.reject(error);
  }
);

export interface TapParams {
  serial: string;
  x: number;
  y: number;
}

export interface SwipeParams {
  serial: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  duration?: number;
}

export interface LongPressParams {
  serial: string;
  x: number;
  y: number;
  duration?: number;
}

export interface TypeTextParams {
  serial: string;
  text: string;
}

export interface PressKeyParams {
  serial: string;
  key: string;
}

export interface LaunchAppParams {
  serial: string;
  package_name: string;
}

export interface ShellCommandParams {
  serial: string;
  command: string;
}

export interface UIHierarchyNode {
  class: string;
  resource_id: string;
  text: string;
  content_desc: string;
  bounds: { left: number; top: number; right: number; bottom: number };
  clickable: boolean;
  enabled: boolean;
  focused: boolean;
  selected: boolean;
  children: UIHierarchyNode[];
}

export interface DeviceInfoResponse {
  serial: string;
  model: string;
  brand: string;
  android_version: string;
  screen_width: number;
  screen_height: number;
  screen_density: number;
  battery_level?: number;
  battery_status?: string;
  wifi_connected?: boolean;
  ip_address?: string;
}

export interface ApiResponse {
  success: boolean;
  message?: string;
  error?: string;
}

/**
 * Tap on device screen at coordinates
 */
export async function tapDevice(
  serial: string,
  x: number,
  y: number
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/tap`, {
    x,
    y,
  });
  return response.data;
}

/**
 * Swipe on device screen from (x1,y1) to (x2,y2)
 */
export async function swipeDevice(
  serial: string,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  duration: number = 300
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/swipe`, {
    x1,
    y1,
    x2,
    y2,
    duration,
  });
  return response.data;
}

/**
 * Long press on device screen at coordinates
 */
export async function longPressDevice(
  serial: string,
  x: number,
  y: number,
  duration: number = 500
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/longpress`, {
    x,
    y,
    duration,
  });
  return response.data;
}

/**
 * Type text on device
 */
export async function typeText(
  serial: string,
  text: string
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/type`, {
    text,
  });
  return response.data;
}

/**
 * Press a hardware/system key
 */
export async function pressKey(
  serial: string,
  key: string
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/key`, {
    key,
  });
  return response.data;
}

/**
 * Launch an app by package name
 */
export async function launchApp(
  serial: string,
  package_name: string
): Promise<ApiResponse> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/launch`, {
    package_name,
  });
  return response.data;
}

/**
 * Get UI hierarchy (accessibility tree)
 */
export async function getUIHierarchy(serial: string): Promise<UIHierarchyNode> {
  const response = await phoneApiInstance.get(`/api/v1/devices/${serial}/ui-hierarchy`);
  return response.data;
}

/**
 * Get current screenshot as base64 image
 */
export async function getScreenshot(serial: string): Promise<{ image: string }> {
  const response = await phoneApiInstance.get(`/api/v1/devices/${serial}/screenshot`);
  return response.data;
}

/**
 * Execute a shell command on the device
 */
export async function shellCommand(
  serial: string,
  command: string
): Promise<ApiResponse & { output?: string }> {
  const response = await phoneApiInstance.post(`/api/v1/devices/${serial}/shell`, {
    command,
  });
  return response.data;
}

/**
 * Get device info
 */
export async function getDeviceInfo(serial: string): Promise<DeviceInfoResponse> {
  const response = await phoneApiInstance.get(`/api/v1/devices/${serial}/info`);
  return response.data;
}
