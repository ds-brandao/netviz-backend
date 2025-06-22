import React, { createContext, useContext, useState, ReactNode } from 'react';

export type DataMode = 'realtime' | 'fake';

interface DataModeContextType {
  dataMode: DataMode;
  setDataMode: (mode: DataMode) => void;
  isUsingFakeData: boolean;
}

const DataModeContext = createContext<DataModeContextType | undefined>(undefined);

interface DataModeProviderProps {
  children: ReactNode;
}

export const DataModeProvider: React.FC<DataModeProviderProps> = ({ children }) => {
  const [dataMode, setDataMode] = useState<DataMode>('realtime');

  const value: DataModeContextType = {
    dataMode,
    setDataMode,
    isUsingFakeData: dataMode === 'fake'
  };

  return (
    <DataModeContext.Provider value={value}>
      {children}
    </DataModeContext.Provider>
  );
};

export const useDataMode = (): DataModeContextType => {
  const context = useContext(DataModeContext);
  if (context === undefined) {
    throw new Error('useDataMode must be used within a DataModeProvider');
  }
  return context;
}; 