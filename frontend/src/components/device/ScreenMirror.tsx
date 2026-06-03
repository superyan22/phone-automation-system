/**
 * Screen Mirror Component
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketService, createDeviceWebSocket } from '../../services/websocket';

interface ScreenMirrorProps {
  serial: string;
  width?: number;
  height?: number;
  enableTouch?: boolean;
  onScreenshot?: (image: string) => void;
}

export const ScreenMirror: React.FC<ScreenMirrorProps> = ({
  serial,
  width = 360,
  height = 640,
  enableTouch = true,
  onScreenshot,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [fps, setFps] = useState(0);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(Date.now());

  useEffect(() => {
    // Create WebSocket service
    const service = createDeviceWebSocket(serial);
    setWsService(service);

    // Connect
    service.connect().catch(console.error);

    // Subscribe to messages
    service.subscribe('screenshot', (message) => {
      const { image } = message.data || {};
      if (image) {
        drawFrame(image);
        onScreenshot?.(image);
      }
    });

    service.subscribe('screen_stream', (message) => {
      const { frame } = message.data || {};
      if (frame) {
        drawFrame(frame);

        // Calculate FPS
        frameCountRef.current++;
        const now = Date.now();
        if (now - lastTimeRef.current >= 1000) {
          setFps(frameCountRef.current);
          frameCountRef.current = 0;
          lastTimeRef.current = now;
        }
      }
    });

    // Cleanup
    return () => {
      service.disconnect();
    };
  }, [serial, onScreenshot]);

  // Draw frame
  const drawFrame = useCallback(
    (base64Image: string) => {
      const canvas = canvasRef.current;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const img = new Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
      img.src = `data:image/jpeg;base64,${base64Image}`;
    },
    []
  );

  // Start/stop streaming
  const toggleStream = useCallback(() => {
    if (!wsService) return;

    if (isStreaming) {
      wsService.send({ type: 'stop_stream' });
    } else {
      wsService.send({ type: 'start_stream' });
    }
    setIsStreaming(!isStreaming);
  }, [isStreaming, wsService]);

  // Request screenshot
  const requestScreenshot = useCallback(() => {
    wsService?.send({ type: 'screenshot' });
  }, [wsService]);

  // Handle touch events
  const handleTap = useCallback(
    (x: number, y: number) => {
      wsService?.send({
        type: 'tap',
        params: { x: x / width, y: y / height },
      });
    },
    [wsService, width, height]
  );

  const handleSwipe = useCallback(
    (x1: number, y1: number, x2: number, y2: number) => {
      wsService?.send({
        type: 'swipe',
        params: {
          x1: x1 / width,
          y1: y1 / height,
          x2: x2 / width,
          y2: y2 / height,
          duration: 300,
        },
      });
    },
    [wsService, width, height]
  );

  return (
    <div className="screen-mirror">
      <div className="screen-mirror-header flex justify-between items-center mb-2">
        <span className="fps text-sm text-gray-500">FPS: {fps}</span>
        <div className="flex gap-2">
          <button
            onClick={toggleStream}
            className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600"
          >
            {isStreaming ? 'Stop' : 'Start'} Stream
          </button>
          <button
            onClick={requestScreenshot}
            className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
          >
            Screenshot
          </button>
        </div>
      </div>

      <div
        className="screen-mirror-container relative"
        style={{ width, height }}
      >
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          style={{ width: '100%', height: '100%' }}
          className="border border-gray-300"
        />

        {enableTouch && (
          <TouchOverlay
            width={width}
            height={height}
            onTap={handleTap}
            onSwipe={handleSwipe}
          />
        )}
      </div>
    </div>
  );
};

// Touch Overlay Component
interface TouchOverlayProps {
  width: number;
  height: number;
  onTap: (x: number, y: number) => void;
  onSwipe: (x1: number, y1: number, x2: number, y2: number) => void;
}

const TouchOverlay: React.FC<TouchOverlayProps> = ({
  width,
  height,
  onTap,
  onSwipe,
}) => {
  const startPosRef = useRef<{ x: number; y: number } | null>(null);
  const isSwipeRef = useRef(false);

  const getPosition = useCallback((e: React.MouseEvent) => {
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      startPosRef.current = getPosition(e);
      isSwipeRef.current = false;
    },
    [getPosition]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!startPosRef.current) return;

      const currentPos = getPosition(e);
      const distance = Math.sqrt(
        Math.pow(currentPos.x - startPosRef.current.x, 2) +
          Math.pow(currentPos.y - startPosRef.current.y, 2)
      );

      // If moved more than 10px, it's a swipe
      if (distance > 10) {
        isSwipeRef.current = true;
      }
    },
    [getPosition]
  );

  const handleMouseUp = useCallback(
    (e: React.MouseEvent) => {
      if (!startPosRef.current) return;

      const endPos = getPosition(e);

      if (isSwipeRef.current) {
        onSwipe(
          startPosRef.current.x,
          startPosRef.current.y,
          endPos.x,
          endPos.y
        );
      } else {
        onTap(endPos.x, endPos.y);
      }

      startPosRef.current = null;
      isSwipeRef.current = false;
    },
    [getPosition, onTap, onSwipe]
  );

  return (
    <div
      className="touch-overlay"
      style={{
        width,
        height,
        position: 'absolute',
        top: 0,
        left: 0,
        cursor: 'pointer',
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => {
        startPosRef.current = null;
        isSwipeRef.current = false;
      }}
    />
  );
};

export default ScreenMirror;
