import { useEffect, useCallback, useRef } from 'react';
import { useMarketStore } from '../store/marketStore';

export const useMarketWebSocket = () => {
  const { setMarketData, setConnectionStatus, addLog } = useMarketStore();
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/market');

    setConnectionStatus('connecting');

    ws.onopen = () => {
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
      console.log('Connected to market feed');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'initial' || message.type === 'update') {
          setMarketData(message.data);
        } else if (message.type === 'event') {
          addLog(message.data.msg, message.data.eventType);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('error');
    };

    ws.onclose = () => {
      setConnectionStatus('disconnected');

      // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;

      console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current})...`);

      reconnectTimerRef.current = setTimeout(() => {
        console.log(`Reconnecting (attempt ${reconnectAttempts.current})...`);
        connect();
      }, delay);
    };

    wsRef.current = ws;
  }, [setMarketData, setConnectionStatus, addLog]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [connect]);

  return {
    connectionStatus: useMarketStore(state => state.connectionStatus)
  };
};
