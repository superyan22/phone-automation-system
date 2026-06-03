/**
 * Devices Page
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

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Devices</h1>
        <div className="flex gap-2">
          <select
            value={scanType}
            onChange={(e) => setScanType(e.target.value as 'usb' | 'wifi' | 'all')}
            className="px-4 py-2 border rounded-lg"
          >
            <option value="usb">USB</option>
            <option value="wifi">WiFi</option>
            <option value="all">All</option>
          </select>
          <button
            onClick={handleScan}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Scanning...' : 'Scan Devices'}
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search devices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg"
        />
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      {/* Device List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDevices.map((device) => (
          <DeviceCard
            key={device.serial}
            device={device}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onSelect={handleSelectDevice}
          />
        ))}
      </div>

      {filteredDevices.length === 0 && !isLoading && (
        <div className="text-center py-8 text-gray-500">
          No devices found. Click "Scan Devices" to discover connected phones.
        </div>
      )}
    </div>
  );
};

// Device Card Component
interface DeviceCardProps {
  device: Device;
  onConnect: (serial: string) => void;
  onDisconnect: (serial: string) => void;
  onSelect: (serial: string) => void;
}

const DeviceCard: React.FC<DeviceCardProps> = ({
  device,
  onConnect,
  onDisconnect,
  onSelect,
}) => {
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

  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-lg">{device.model || 'Unknown Device'}</h3>
          <p className="text-sm text-gray-500">{device.serial}</p>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(device.status)}`}>
          {device.status}
        </span>
      </div>

      <div className="text-sm text-gray-600 mb-4">
        <p>Type: {device.device_type.toUpperCase()}</p>
        {device.brand && <p>Brand: {device.brand}</p>}
        {device.android_version && <p>Android: {device.android_version}</p>}
        {device.screen_width && device.screen_height && (
          <p>Screen: {device.screen_width}x{device.screen_height}</p>
        )}
      </div>

      <div className="flex gap-2">
        {device.status === 'offline' ? (
          <button
            onClick={() => onConnect(device.serial)}
            className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
          >
            Connect
          </button>
        ) : (
          <button
            onClick={() => onDisconnect(device.serial)}
            className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
          >
            Disconnect
          </button>
        )}
        <button
          onClick={() => onSelect(device.serial)}
          className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
        >
          Select
        </button>
      </div>
    </div>
  );
};

export default DevicesPage;
