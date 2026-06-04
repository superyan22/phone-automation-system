/**
 * Phone Control Page - Chinese Version
 * Device selector + interactive screen + controls
 */

import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../../services/api';
import { Device } from '../../types/device';
import InteractiveScreen from '../../components/phone/InteractiveScreen';
import PhoneControls from '../../components/phone/PhoneControls';

interface PhonePageProps {
  apiKey: string;
}

const PhonePage: React.FC<PhonePageProps> = ({ apiKey }) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedSerial, setSelectedSerial] = useState<string>('');
  const [loadingDevices, setLoadingDevices] = useState(true);
  const [deviceError, setDeviceError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    try {
      setLoadingDevices(true);
      setDeviceError(null);
      const response = await apiService.getDevices({ page_size: 50 });
      setDevices(response.items || []);
      // Auto-select first device if available
      if (response.items?.length > 0 && !selectedSerial) {
        setSelectedSerial(response.items[0].serial);
      }
    } catch (err: any) {
      console.error('Failed to fetch devices:', err);
      setDeviceError(err.message || '加载设备失败');
    } finally {
      setLoadingDevices(false);
    }
  }, [selectedSerial]);

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const selectedDevice = devices.find((d) => d.serial === selectedSerial);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📱 手机控制</h1>
        <p className="mt-1 text-sm text-gray-500">
          实时交互控制您的设备
        </p>
      </div>

      {/* Device selector bar */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-4 space-y-3 sm:space-y-0">
          {/* Device dropdown */}
          <div className="flex-1">
            <label className="block text-xs font-medium text-gray-500 mb-1">
              选择设备
            </label>
            <select
              value={selectedSerial}
              onChange={(e) => setSelectedSerial(e.target.value)}
              disabled={loadingDevices}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
            >
              {loadingDevices && <option>加载设备中...</option>}
              {!loadingDevices && devices.length === 0 && (
                <option>未找到设备</option>
              )}
              {devices.map((device) => (
                <option key={device.serial} value={device.serial}>
                  {device.brand || ''} {device.model || device.serial} ({device.serial})
                  {device.status === 'online' ? ' 🟢' : ' 🔴'}
                </option>
              ))}
            </select>
            {deviceError && (
              <p className="text-xs text-red-500 mt-1">{deviceError}</p>
            )}
          </div>

          {/* Device info chips */}
          {selectedDevice && (
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {selectedDevice.screen_width} × {selectedDevice.screen_height}
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                  selectedDevice.status === 'online'
                    ? 'bg-green-100 text-green-800'
                    : selectedDevice.status === 'busy'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {selectedDevice.status === 'online' ? '在线' : selectedDevice.status === 'busy' ? '忙碌' : '离线'}
              </span>
              {selectedDevice.android_version && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                  Android {selectedDevice.android_version}
                </span>
              )}
              {selectedDevice.model && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                  {selectedDevice.brand} {selectedDevice.model}
                </span>
              )}
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                  selectedDevice.is_connected
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {selectedDevice.is_connected ? '🔗 已连接' : '⛓ 未连接'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main content: Screen + Controls */}
      {selectedSerial ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Screen (60% = 3/5) */}
          <div className="lg:col-span-3">
            <InteractiveScreen
              serial={selectedSerial}
              deviceWidth={selectedDevice?.screen_width || 1080}
              deviceHeight={selectedDevice?.screen_height || 2340}
              apiKey={apiKey}
            />
          </div>

          {/* Controls (40% = 2/5) */}
          <div className="lg:col-span-2">
            <PhoneControls serial={selectedSerial} apiKey={apiKey} />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="text-gray-400 text-4xl mb-4">📱</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            未选择设备
          </h3>
          <p className="text-sm text-gray-500">
            {loadingDevices
              ? '加载设备中...'
              : devices.length === 0
              ? '未找到设备。请先通过 USB 或 WiFi 连接设备。'
              : '从上方下拉菜单选择设备开始控制。'}
          </p>
        </div>
      )}
    </div>
  );
};

export default PhonePage;
