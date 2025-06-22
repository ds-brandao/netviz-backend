import React from 'react';
import { X, Moon, Sun, Zap, Shield, Globe } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EnhancedSettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { theme, setTheme } = useTheme();

  if (!isOpen) return null;

  const themes = [
    { key: 'light' as const, label: 'Light', icon: Sun },
    { key: 'dark' as const, label: 'Dark', icon: Moon },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className={`w-96 max-h-[80vh] rounded-2xl shadow-2xl overflow-hidden ${
        theme === 'light' ? 'bg-white' : 'bg-gray-900'
      }`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-6 border-b ${
          theme === 'light' ? 'border-gray-200' : 'border-gray-700'
        }`}>
          <h2 className={`text-xl font-semibold ${
            theme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            Settings
          </h2>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${
              theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-gray-800'
            }`}
          >
            <X className={`w-5 h-5 ${
              theme === 'light' ? 'text-gray-500' : 'text-gray-400'
            }`} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Theme Selection */}
          <div>
            <h3 className={`text-sm font-medium mb-3 flex items-center gap-2 ${
              theme === 'light' ? 'text-gray-900' : 'text-white'
            }`}>
              <Moon className="w-4 h-4 text-blue-500" />
              Appearance
            </h3>
                         <div className="grid grid-cols-2 gap-2">
              {themes.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setTheme(key)}
                  className={`flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                    theme === key
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : theme === 'light'
                      ? 'border-gray-200 hover:border-gray-300'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <Icon className={`w-5 h-5 ${
                    theme === key ? 'text-blue-500' : theme === 'light' ? 'text-gray-600' : 'text-gray-400'
                  }`} />
                  <span className={`text-xs font-medium ${
                    theme === key ? 'text-blue-600 dark:text-blue-400' : theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                  }`}>
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Network Settings */}
          <div>
            <h3 className={`text-sm font-medium mb-3 flex items-center gap-2 ${
              theme === 'light' ? 'text-gray-900' : 'text-white'
            }`}>
              <Globe className="w-4 h-4 text-green-500" />
              Network
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  Auto-refresh data
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  Show connection details
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
            </div>
          </div>

          {/* Performance */}
          <div>
            <h3 className={`text-sm font-medium mb-3 flex items-center gap-2 ${
              theme === 'light' ? 'text-gray-900' : 'text-white'
            }`}>
              <Zap className="w-4 h-4 text-yellow-500" />
              Performance
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  Enable animations
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  High quality rendering
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
            </div>
          </div>

          {/* AI Assistant */}
          <div>
            <h3 className={`text-sm font-medium mb-3 flex items-center gap-2 ${
              theme === 'light' ? 'text-gray-900' : 'text-white'
            }`}>
              <Shield className="w-4 h-4 text-purple-500" />
              AI Assistant
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  Context memory
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
              <label className="flex items-center justify-between">
                <span className={`text-sm ${
                  theme === 'light' ? 'text-gray-700' : 'text-gray-300'
                }`}>
                  Proactive suggestions
                </span>
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${
          theme === 'light' ? 'border-gray-200 bg-gray-50' : 'border-gray-700 bg-gray-800'
        }`}>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}; 