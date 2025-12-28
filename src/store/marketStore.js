import { create } from 'zustand';

export const useMarketStore = create((set) => ({
  // Market data
  stocks: [],
  marketState: null,
  regime: 'GROWTH',
  time: 0,
  phase: 'TRADING',
  periodReturns: { return60: null, return180: null, return365: null },
  logs: [],
  analytics: null,

  // UI state
  activeTab: 'market', // 'market' | 'analytics'

  // Connection status
  connectionStatus: 'disconnected', // 'disconnected' | 'connecting' | 'connected' | 'error'

  // Actions
  setMarketData: (data) => set({
    stocks: data.stocks || [],
    marketState: data.market_state || null,
    regime: data.regime || 'GROWTH',
    time: data.time || 0,
    phase: data.phase || 'TRADING',
    periodReturns: data.period_returns || { return60: null, return180: null, return365: null },
    logs: data.logs || [],
    analytics: data.analytics || null
  }),

  setConnectionStatus: (status) => set({ connectionStatus: status }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  addLog: (msg, type = 'info') => set((state) => ({
    logs: [
      { id: Date.now(), msg, type, time: new Date().toLocaleTimeString() },
      ...state.logs
    ].slice(0, 5)
  }))
}));
