/**
 * Devices Page - Chinese Version
 */

import React, { useEffect, useState } from 'react';
import { useDeviceStore } from '../../store/deviceSlice';
import { Device } from '../../types/device';

const DevicesPage: React.FC = () => {
  const { devices, isLoading, error, fetchDevices, scanDevices, connectDevice, disconnectDevice, selectDevice } = useDeviceStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [scanType, setScanType] = useState<'usb' | 'wifi' | 'all'>('usb');

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const handleScan = async () => {
    await scanDevices(scanType);
  };

  const handleConnect = async (serial: string) => {
    await connectDevice(serial);
  };

  const handleDisconnect = async (serial: string) => {
    await disconnectDevice(serial);
  };

  const handleSelectDevice = (serial: string) => {
    selectDevice(serial);
  };

  const filteredDevices = devices.filter(
    (device) =>
      device.serial.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.model?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'bg-green-100 text-green-800';
      case 'offline':
        return 'bg-gray-100 text-gray-800';
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'online': return '在线';
      case 'offline': return '离线';
      case 'busy': return '忙碌';
      case 'error': return '错误';
      default: return status;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">📱 设备管理</h1>

      {/* Search and Scan */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            placeholder="搜索设备..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={scanType}
            onChange={(e) => setScanType(e.target.value as 'usb' | 'wifi' | 'all')}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="usb">USB 扫描</option>
            <option value="wifi">WiFi 扫描</option>
            <option value="all">全部扫描</option>
          </select>
          <button
            onClick={handleScan}
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? '扫描中...' : '扫描设备'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* Devices List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                设备
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                状态
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                型号
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                分辨率
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredDevices.map((device) => (
              <tr key={device.serial} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <span className="text-2xl">📱</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {device.brand} {device.model}
                      </div>
                      <div className="text-sm text-gray-500">{device.serial}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(device.status)}`}>
                    {getStatusText(device.status)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {device.model}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {device.screen_width} × {device.screen_height}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => handleSelectDevice(device.serial)}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                  >
                    选择
                  </button>
                  {device.status === 'online' ? (
                    <button
                      onClick={() => handleDisconnect(device.serial)}
                      className="text-red-600 hover:text-red-900"
                    >
                      断开
                    </button>
                  ) : (
                    <button
                      onClick={() => handleConnect(device.serial)}
                      className="text-green-600 hover:text-green-900"
                    >
                      连接
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {filteredDevices.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  {isLoading ? '加载设备中...' : '未找到设备'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DevicesPage;
