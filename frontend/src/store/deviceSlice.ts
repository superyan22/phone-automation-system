/**
 * Device Store
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Device, DeviceStatus } from '../types/device';
import { apiService } from '../services/api';

interface DeviceState {
  // State
  devices: Device[];
  selectedDevice: Device | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchDevices: (params?: any) => Promise<void>;
  scanDevices: (scanType?: string) => Promise<void>;
  selectDevice: (serial: string) => void;
  connectDevice: (serial: string) => Promise<void>;
  disconnectDevice: (serial: string) => Promise<void>;
  updateDeviceStatus: (serial: string, status: DeviceStatus) => void;
  removeDevice: (serial: string) => void;
  clearError: () => void;
}

export const useDeviceStore = create<DeviceState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        devices: [],
        selectedDevice: null,
        isLoading: false,
        error: null,

        // Fetch devices
        fetchDevices: async (params = {}) => {
          set({ isLoading: true, error: null });
          try {
            const response = await apiService.getDevices(params);
            set({ devices: response.items, isLoading: false });
          } catch (error: any) {
            set({
              error: error.response?.data?.detail || error.message,
              isLoading: false,
            });
          }
        },

        // Scan devices
        scanDevices: async (scanType = 'all') => {
          set({ isLoading: true, error: null });
          try {
            const devices = await apiService.scanDevices(scanType);
            set({ devices: devices || [], isLoading: false });
          } catch (error: any) {
            set({
              error: error.response?.data?.detail || error.message,
              isLoading: false,
            });
          }
        },

        // Select device
        selectDevice: (serial: string) => {
          const device = get().devices.find((d) => d.serial === serial);
          set({ selectedDevice: device || null });
        },

        // Connect device
        connectDevice: async (serial: string) => {
          try {
            const device = await apiService.connectDevice(serial);
            set((state) => ({
              devices: state.devices.map((d) =>
                d.serial === serial ? device : d
              ),
              selectedDevice:
                state.selectedDevice?.serial === serial
                  ? device
                  : state.selectedDevice,
            }));
          } catch (error: any) {
            set({ error: error.response?.data?.detail || error.message });
          }
        },

        // Disconnect device
        disconnectDevice: async (serial: string) => {
          try {
            const device = await apiService.disconnectDevice(serial);
            set((state) => ({
              devices: state.devices.map((d) =>
                d.serial === serial ? device : d
              ),
              selectedDevice:
                state.selectedDevice?.serial === serial
                  ? device
                  : state.selectedDevice,
            }));
          } catch (error: any) {
            set({ error: error.response?.data?.detail || error.message });
          }
        },

        // Update device status (from WebSocket)
        updateDeviceStatus: (serial: string, status: DeviceStatus) => {
          set((state) => ({
            devices: state.devices.map((d) =>
              d.serial === serial ? { ...d, status } : d
            ),
            selectedDevice:
              state.selectedDevice?.serial === serial
                ? { ...state.selectedDevice, status }
                : state.selectedDevice,
          }));
        },

        // Remove device
        removeDevice: (serial: string) => {
          set((state) => ({
            devices: state.devices.filter((d) => d.serial !== serial),
            selectedDevice:
              state.selectedDevice?.serial === serial
                ? null
                : state.selectedDevice,
          }));
        },

        // Clear error
        clearError: () => {
          set({ error: null });
        },
      }),
      {
        name: 'device-storage',
        partialize: (state) => ({
          selectedDevice: state.selectedDevice,
        }),
      }
    )
  )
);
