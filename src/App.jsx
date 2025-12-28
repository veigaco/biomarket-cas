import React from 'react';
import { useMarketStore } from './store/marketStore';
import { useMarketWebSocket } from './hooks/useMarketWebSocket';
import TabNavigation from './components/TabNavigation';
import MarketView from './views/MarketView';
import AnalyticsView from './views/AnalyticsView';

/**
 * BIOMARKET CAS: High-Density Treemap Simulation
 * Frontend: Pure display layer consuming WebSocket market data
 * Backend: FastAPI simulation engine @ 500ms ticks, 1s broadcasts
 */

export default function App() {
  // Connect to WebSocket backend
  useMarketWebSocket();

  // Get state from Zustand store
  const { stocks, marketState, activeTab, connectionStatus, setActiveTab } = useMarketStore();

  // Show loading screen until we have data
  if (!marketState || stocks.length === 0) {
    return (
      <div className="fixed inset-0 bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-black text-slate-400 mb-4">BIOMARKET CAS</div>
          <div className="text-slate-500 mb-2">
            {connectionStatus === 'connecting' && 'Connecting to simulation engine...'}
            {connectionStatus === 'connected' && 'Loading market data...'}
            {connectionStatus === 'error' && 'Connection Error'}
            {connectionStatus === 'disconnected' && 'Disconnected from server'}
          </div>
          {connectionStatus === 'error' && (
            <div className="text-sm text-red-400 mt-2">
              Please ensure backend is running at localhost:8000
            </div>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="text-sm text-yellow-400 mt-2">
              Attempting to reconnect...
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-slate-950 text-slate-200 font-sans flex flex-col overflow-hidden">
      {/* Tab Navigation */}
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 min-h-0 p-4">
        {activeTab === 'market' && <MarketView />}
        {activeTab === 'analytics' && <AnalyticsView />}
      </div>

      {/* Connection Status Indicator */}
      {connectionStatus !== 'connected' && (
        <div className="fixed top-4 right-4 z-50 bg-yellow-500 text-black px-4 py-2 rounded-lg font-bold shadow-lg animate-pulse">
          {connectionStatus === 'connecting' && 'Connecting...'}
          {connectionStatus === 'disconnected' && 'Reconnecting...'}
          {connectionStatus === 'error' && 'Connection Error'}
        </div>
      )}
    </div>
  );
}
