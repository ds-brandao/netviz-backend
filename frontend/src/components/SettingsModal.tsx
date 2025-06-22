import React from 'react';
import { X, Sun, Moon, Monitor, Palette, Zap } from 'lucide-react';
import { SimpleLiquidGlass } from './SimpleLiquidGlass/SimpleLiquidGlass';
import { useTheme } from '../contexts/ThemeContext';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { theme, setTheme } = useTheme();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center " onClick={onClose}>
      <div className="pointer-events-auto" onClick={(e) => e.stopPropagation()}>
        <SimpleLiquidGlass
          padding="0"
          textColor={theme === 'light' ? '#1f2937' : 'white'}
        >
      <div className="w-96 bg-transparent">
          {/* Header */}
          <div className={`flex items-center justify-between p-6 border-b ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                <Palette className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className={`text-xl font-semibold ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Settings</h2>
                <p className={`text-sm ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>Customize your experience</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Theme Selection */}
            <div>
              <h3 className={`font-medium text-lg mb-3 flex items-center gap-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                <Palette className="w-5 h-5 text-purple-400" />
                Appearance
              </h3>
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setTheme('light')}
                    className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                      theme === 'light'
                        ? 'border-blue-500 bg-blue-500/20'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }`}
                  >
                    <Sun className="w-6 h-6 text-yellow-400" />
                    <span className={`text-sm font-medium ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Light</span>
                  </button>
                  
                  <button
                    onClick={() => setTheme('dark')}
                    className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                      theme === 'dark'
                        ? 'border-blue-500 bg-blue-500/20'
                        : theme === 'light'
                        ? 'border-gray-300 hover:border-gray-400 hover:bg-gray-100'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }`}
                  >
                    <Moon className="w-6 h-6 text-blue-400" />
                    <span className={`text-sm font-medium ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Dark</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      // Auto theme based on system preference
                      const systemTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
                      setTheme(systemTheme);
                    }}
                    className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                      theme === 'light'
                        ? 'border-gray-300 hover:border-gray-400 hover:bg-gray-100'
                        : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                    }`}
                  >
                    <Monitor className="w-6 h-6 text-gray-400" />
                    <span className={`text-sm font-medium ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Auto</span>
                  </button>
                </div>
                <p className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                  Choose your preferred color scheme. Auto will match your system preference.
                </p>
              </div>
            </div>

            {/* Performance Settings */}
            <div>
              <h3 className={`font-medium text-lg mb-3 flex items-center gap-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                <Zap className="w-5 h-5 text-yellow-400" />
                Performance
              </h3>
              <div className="space-y-3">
                <div className={`flex items-center justify-between p-3 rounded-lg ${theme === 'light' ? 'bg-gray-100' : 'bg-white/5'}`}>
                  <div>
                    <p className={`font-medium text-sm ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>High Performance Mode</p>
                    <p className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>Enhanced visual effects and animations</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                
                <div className={`flex items-center justify-between p-3 rounded-lg ${theme === 'light' ? 'bg-gray-100' : 'bg-white/5'}`}>
                  <div>
                    <p className={`font-medium text-sm ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Reduce Motion</p>
                    <p className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>Minimize animations for better accessibility</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* About */}
            <div className={`pt-4 border-t ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
              <div className="text-center space-y-2">
                <p className={`text-sm ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>Network Visualization Tool</p>
                <p className={`text-xs ${theme === 'light' ? 'text-gray-500' : 'text-gray-500'}`}>Built with React Flow & Liquid Glass</p>
                <div className="flex justify-center gap-4 pt-2">
                  <span className={`text-xs ${theme === 'light' ? 'text-gray-500' : 'text-gray-500'}`}>v1.0.0</span>
                  <span className={`text-xs ${theme === 'light' ? 'text-gray-500' : 'text-gray-500'}`}>•</span>
                  <span className={`text-xs ${theme === 'light' ? 'text-gray-500' : 'text-gray-500'}`}>MIT License</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        </SimpleLiquidGlass>
      </div>
    </div>
  );
}; 