/**
 * Interactive Screen Component
 * Shows phone screenshot with click-to-tap interaction
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { getScreenshot, tapDevice } from '../../services/phoneApi';

interface InteractiveScreenProps {
  serial: string;
  deviceWidth: number;
  deviceHeight: number;
}

const InteractiveScreen: React.FC<InteractiveScreenProps> = ({
  serial,
  deviceWidth,
  deviceHeight,
}) => {
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const imageRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchScreenshot = useCallback(async () => {
    if (!serial) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getScreenshot(serial);
      if (data.image) {
        setScreenshot(`data:image/png;base64,${data.image}`);
        setLastUpdate(new Date());
      }
    } catch (err: any) {
      console.error('Screenshot fetch error:', err);
      setError(err.message || 'Failed to fetch screenshot');
    } finally {
      setLoading(false);
    }
  }, [serial]);

  // Initial fetch
  useEffect(() => {
    fetchScreenshot();
  }, [fetchScreenshot]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchScreenshot, 2000);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh, fetchScreenshot]);

  const handleImageClick = useCallback(
    async (e: React.MouseEvent<HTMLImageElement>) => {
      const img = imageRef.current;
      if (!img) return;

      const rect = img.getBoundingClientRect();
      const displayX = e.clientX - rect.left;
      const displayY = e.clientY - rect.top;

      // Scale from displayed size to actual device coordinates
      const scaleX = deviceWidth / rect.width;
      const scaleY = deviceHeight / rect.height;
      const deviceX = Math.round(displayX * scaleX);
      const deviceY = Math.round(displayY * scaleY);

      try {
        await tapDevice(serial, deviceX, deviceY);
        // Refresh screenshot after tap to show result
        setTimeout(fetchScreenshot, 500);
      } catch (err: any) {
        console.error('Tap failed:', err);
      }
    },
    [serial, deviceWidth, deviceHeight, fetchScreenshot]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-900 rounded-t-lg">
        <div className="flex items-center space-x-3">
          <h3 className="text-sm font-semibold text-white">Screen</h3>
          {lastUpdate && (
            <span className="text-xs text-gray-400">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-1 text-xs text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded bg-gray-700 border-gray-600 text-blue-500 focus:ring-blue-500"
            />
            <span>Auto</span>
          </label>
          <button
            onClick={fetchScreenshot}
            disabled={loading}
            className="px-3 py-1 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Screen area */}
      <div
        ref={containerRef}
        className="flex-1 flex items-center justify-center bg-gray-950 rounded-b-lg p-4 relative overflow-hidden"
        style={{ minHeight: 400 }}
      >
        {error && (
          <div className="text-center">
            <div className="text-red-400 text-sm mb-2">⚠️ {error}</div>
            <button
              onClick={fetchScreenshot}
              className="text-xs text-blue-400 hover:text-blue-300 underline"
            >
              Retry
            </button>
          </div>
        )}

        {!error && !screenshot && !loading && (
          <div className="text-gray-500 text-sm">
            No screenshot available. Click Refresh to load.
          </div>
        )}

        {loading && !screenshot && (
          <div className="flex items-center justify-center space-x-2 text-gray-400">
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Loading screenshot...</span>
          </div>
        )}

        {screenshot && (
          <div className="relative inline-block">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/30 z-10 rounded">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            <img
              ref={imageRef}
              src={screenshot}
              alt="Phone Screen"
              onClick={handleImageClick}
              className="max-h-[600px] max-w-full rounded-lg cursor-pointer shadow-2xl border border-gray-700"
              style={{ objectFit: 'contain' }}
              draggable={false}
            />
            {/* Coordinate indicator on hover */}
            <div className="absolute bottom-2 left-2 text-xs text-gray-500 bg-black/50 px-2 py-1 rounded">
              {deviceWidth} × {deviceHeight}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractiveScreen;
