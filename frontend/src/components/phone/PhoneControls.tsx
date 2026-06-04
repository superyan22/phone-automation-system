/**
 * Phone Controls Component
 * Navigation buttons, text input, swipe, quick actions, shell commands
 */

import React, { useState, useCallback } from 'react';
import {
  pressKey,
  typeText,
  swipeDevice,
  launchApp,
  shellCommand,
} from '../../services/phoneApi';

interface PhoneControlsProps {
  serial: string;
}

const PHONE_KEYS = {
  HOME: 'home',
  BACK: 'back',
  RECENT: 'recent_apps',
  VOLUME_UP: 'volume_up',
  VOLUME_DOWN: 'volume_down',
  POWER: 'power',
  ENTER: 'enter',
};

const QUICK_APPS = [
  { name: 'WeChat', package: 'com.tencent.mm', icon: '💬' },
  { name: 'XiaoHongShu', package: 'com.xingin.xhs', icon: '📕' },
  { name: 'Camera', package: 'com.android.camera', icon: '📷' },
  { name: 'Settings', package: 'com.android.settings', icon: '⚙️' },
  { name: 'Browser', package: 'com.android.browser', icon: '🌐' },
  { name: 'File Manager', package: 'com.android.filemanager', icon: '📁' },
];

const PhoneControls: React.FC<PhoneControlsProps> = ({ serial }) => {
  // Text input
  const [textInput, setTextInput] = useState('');
  const [textLoading, setTextLoading] = useState(false);

  // Swipe
  const [swipeX1, setSwipeX1] = useState('500');
  const [swipeY1, setSwipeY1] = useState('1500');
  const [swipeX2, setSwipeX2] = useState('500');
  const [swipeY2, setSwipeY2] = useState('500');
  const [swipeDuration, setSwipeDuration] = useState('300');
  const [swipeLoading, setSwipeLoading] = useState(false);

  // Shell
  const [shellCmd, setShellCmd] = useState('');
  const [shellOutput, setShellOutput] = useState('');
  const [shellLoading, setShellLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Button feedback
  const [lastAction, setLastAction] = useState<string | null>(null);

  const showFeedback = useCallback((msg: string) => {
    setLastAction(msg);
    setTimeout(() => setLastAction(null), 1500);
  }, []);

  const handleKeyPress = useCallback(
    async (key: string) => {
      try {
        await pressKey(serial, key);
        showFeedback(`${key} pressed`);
      } catch (err) {
        console.error('Key press failed:', err);
      }
    },
    [serial, showFeedback]
  );

  const handleTypeText = useCallback(async () => {
    if (!textInput.trim()) return;
    try {
      setTextLoading(true);
      await typeText(serial, textInput);
      showFeedback('Text sent');
      setTextInput('');
    } catch (err) {
      console.error('Type text failed:', err);
    } finally {
      setTextLoading(false);
    }
  }, [serial, textInput, showFeedback]);

  const handleSwipe = useCallback(async () => {
    try {
      setSwipeLoading(true);
      await swipeDevice(
        serial,
        parseInt(swipeX1),
        parseInt(swipeY1),
        parseInt(swipeX2),
        parseInt(swipeY2),
        parseInt(swipeDuration)
      );
      showFeedback('Swipe executed');
    } catch (err) {
      console.error('Swipe failed:', err);
    } finally {
      setSwipeLoading(false);
    }
  }, [serial, swipeX1, swipeY1, swipeX2, swipeY2, swipeDuration, showFeedback]);

  const handleLaunchApp = useCallback(
    async (packageName: string, appName: string) => {
      try {
        await launchApp(serial, packageName);
        showFeedback(`Launched ${appName}`);
      } catch (err) {
        console.error('Launch app failed:', err);
      }
    },
    [serial, showFeedback]
  );

  const handleShellCommand = useCallback(async () => {
    if (!shellCmd.trim()) return;
    try {
      setShellLoading(true);
      const result = await shellCommand(serial, shellCmd);
      setShellOutput(result.output || result.message || 'Command executed');
      showFeedback('Command sent');
    } catch (err: any) {
      setShellOutput(`Error: ${err.message || 'Command failed'}`);
    } finally {
      setShellLoading(false);
    }
  }, [serial, shellCmd, showFeedback]);

  const buttonBase =
    'px-3 py-2 rounded-lg font-medium text-sm transition-all duration-150 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed';

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Feedback toast */}
      {lastAction && (
        <div className="fixed top-4 right-4 bg-green-600 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50 animate-pulse">
          ✓ {lastAction}
        </div>
      )}

      {/* Navigation buttons */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Navigation
        </h4>
        <div className="grid grid-cols-3 gap-2">
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.HOME)}
            className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white`}
          >
            🏠 Home
          </button>
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.BACK)}
            className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white`}
          >
            ◀ Back
          </button>
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.RECENT)}
            className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white`}
          >
            ▢ Recent
          </button>
        </div>
        <div className="grid grid-cols-3 gap-2 mt-2">
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.VOLUME_UP)}
            className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white`}
          >
            🔊 Vol+
          </button>
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.VOLUME_DOWN)}
            className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white`}
          >
            🔉 Vol-
          </button>
          <button
            onClick={() => handleKeyPress(PHONE_KEYS.POWER)}
            className={`${buttonBase} bg-red-700 hover:bg-red-600 text-white`}
          >
            ⏻ Power
          </button>
        </div>
      </div>

      {/* Text input */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Text Input
        </h4>
        <div className="flex space-x-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleTypeText()}
            placeholder="Type text to send..."
            className="flex-1 bg-gray-700 text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:border-blue-500 focus:outline-none placeholder-gray-500"
          />
          <button
            onClick={handleTypeText}
            disabled={!textInput.trim() || textLoading}
            className={`${buttonBase} bg-blue-600 hover:bg-blue-500 text-white whitespace-nowrap`}
          >
            {textLoading ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {/* Swipe controls */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Swipe Gesture
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-gray-500">Start X</label>
            <input
              type="number"
              value={swipeX1}
              onChange={(e) => setSwipeX1(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500">Start Y</label>
            <input
              type="number"
              value={swipeY1}
              onChange={(e) => setSwipeY1(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500">End X</label>
            <input
              type="number"
              value={swipeX2}
              onChange={(e) => setSwipeX2(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-gray-500">End Y</label>
            <input
              type="number"
              value={swipeY2}
              onChange={(e) => setSwipeY2(e.target.value)}
              className="w-full bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>
        <div className="mt-2">
          <label className="text-xs text-gray-500">Duration (ms)</label>
          <input
            type="number"
            value={swipeDuration}
            onChange={(e) => setSwipeDuration(e.target.value)}
            className="w-full bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleSwipe}
          disabled={swipeLoading}
          className={`${buttonBase} w-full mt-3 bg-purple-600 hover:bg-purple-500 text-white`}
        >
          {swipeLoading ? 'Swiping...' : '↻ Swipe'}
        </button>
      </div>

      {/* Quick actions */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Quick Actions
        </h4>
        <div className="grid grid-cols-3 gap-2">
          {QUICK_APPS.map((app) => (
            <button
              key={app.package}
              onClick={() => handleLaunchApp(app.package, app.name)}
              className={`${buttonBase} bg-gray-700 hover:bg-gray-600 text-white flex flex-col items-center space-y-1 py-3`}
            >
              <span className="text-lg">{app.icon}</span>
              <span className="text-xs">{app.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Shell command (advanced) */}
      <div className="bg-gray-800 rounded-lg">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full px-4 py-3 flex items-center justify-between text-sm text-gray-400 hover:text-gray-300"
        >
          <span className="font-semibold uppercase tracking-wider">
            Shell Command (Advanced)
          </span>
          <span>{showAdvanced ? '▼' : '▶'}</span>
        </button>

        {showAdvanced && (
          <div className="px-4 pb-4">
            <div className="flex space-x-2">
              <input
                type="text"
                value={shellCmd}
                onChange={(e) => setShellCmd(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleShellCommand()}
                placeholder="adb shell command..."
                className="flex-1 bg-gray-700 text-green-400 text-sm font-mono rounded px-3 py-2 border border-gray-600 focus:border-green-500 focus:outline-none placeholder-gray-500"
              />
              <button
                onClick={handleShellCommand}
                disabled={!shellCmd.trim() || shellLoading}
                className={`${buttonBase} bg-green-700 hover:bg-green-600 text-white whitespace-nowrap`}
              >
                {shellLoading ? '...' : 'Run'}
              </button>
            </div>
            {shellOutput && (
              <pre className="mt-2 bg-gray-900 text-green-300 text-xs p-3 rounded-lg overflow-auto max-h-40 border border-gray-700">
                {shellOutput}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PhoneControls;
