import React from 'react';
import { NetworkVisualization } from './components/NetworkVisualization';
import { ThemeProvider } from './contexts/ThemeContext';
import { DataModeProvider } from './contexts/DataModeContext';

function App() {
  return (
    <ThemeProvider>
      <DataModeProvider>
        <div className="min-h-screen bg-gray-900 dark:bg-gray-900 light:bg-gray-100 transition-colors duration-300">
          <NetworkVisualization />
        </div>
      </DataModeProvider>
    </ThemeProvider>
  );
}

export default App;