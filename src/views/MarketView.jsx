import React, { useMemo } from 'react';
import {
  Activity,
  Waves,
  LayoutGrid
} from 'lucide-react';
import { useMarketStore } from '../store/marketStore';

// --- Helper Functions ---
const formatCurrency = (val) => {
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  return `$${val.toFixed(2)}`;
};

// Regime configuration for UI display
const REGIMES = {
  GROWTH: {
    label: 'Bull Market',
    color: 'text-green-400',
  },
  STAGNATION: {
    label: 'Sideways Market',
    color: 'text-yellow-400',
  },
  CONTRACTION: {
    label: 'Correction',
    color: 'text-orange-500',
  },
  CRISIS: {
    label: 'Bear Market',
    color: 'text-red-500',
  }
};

// --- Components ---

const TreemapTile = ({ stock, x, y, width, height }) => {
  // Calculate 60-period total return
  const startPrice = stock.history[0] || stock.price;
  const totalReturn = ((stock.price - startPrice) / startPrice) * 100;

  // Professional heatmap colors (finviz-style)
  const getColor = (val) => {
    const absVal = Math.abs(val);
    if (val >= 3) return '#1a9641'; // Strong green
    if (val >= 2) return '#4fa83d';
    if (val >= 1) return '#7fb83e';
    if (val >= 0.5) return '#a6d854';
    if (val >= 0) return '#c9e75d';
    if (val >= -0.5) return '#fee08b';
    if (val >= -1) return '#fdae61';
    if (val >= -2) return '#f46d43';
    if (val >= -3) return '#d73027';
    return '#a50026'; // Strong red
  };

  const getBorderColor = (val) => {
    if (val >= 0) return 'rgba(0, 0, 0, 0.3)';
    return 'rgba(0, 0, 0, 0.4)';
  };

  // Smart positioning: determine which side to show the modal
  const getModalPosition = () => {
    const isLeftSide = x < 50;
    const isTopSide = y < 50;

    if (isLeftSide && isTopSide) {
      return 'left-0 top-full mt-2';
    } else if (!isLeftSide && isTopSide) {
      return 'right-0 top-full mt-2';
    } else if (isLeftSide && !isTopSide) {
      return 'left-0 bottom-full mb-2';
    } else {
      return 'right-0 bottom-full mb-2';
    }
  };

  const isSmall = width < 8 || height < 6;
  const isMedium = width < 12 || height < 9;
  const isLarge = width >= 15 && height >= 12;

  return (
    <div
      className="absolute transition-all duration-700 ease-in-out overflow-visible hover:z-50 hover:ring-2 hover:ring-yellow-400/80 group cursor-pointer"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: `${width}%`,
        height: `${height}%`,
        backgroundColor: getColor(totalReturn),
        border: `1px solid ${getBorderColor(totalReturn)}`
      }}
    >
      {!isSmall && (
        <div className="absolute top-1 left-1 right-1 flex flex-col gap-0.5">
          <div className={`font-black text-white leading-none tracking-tight ${
            isMedium ? 'text-[9px]' : isLarge ? 'text-base' : 'text-xs'
          }`}>
            {stock.ticker}
          </div>

          {!isMedium && (
            <div className={`font-bold leading-none ${
              totalReturn >= 0 ? 'text-white/95' : 'text-white/90'
            } ${isLarge ? 'text-sm' : 'text-[10px]'}`}>
              {totalReturn > 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </div>
          )}

          {isLarge && (
            <>
              <div className="text-[9px] text-white/70 leading-tight mt-0.5 truncate">
                {stock.name}
              </div>
              <div className="text-[8px] text-white/60 leading-none mt-auto">
                {formatCurrency(stock.currentMarketCap)}
              </div>
            </>
          )}
        </div>
      )}

      <div className={`absolute ${getModalPosition()} opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50`}>
        <div className="bg-slate-900/95 backdrop-blur-sm border-2 border-yellow-400/80 rounded-lg p-4 shadow-2xl w-[220px]">
          <div className="text-white font-black text-xl mb-1 text-center">{stock.ticker}</div>
          <div className="text-white/80 text-sm mb-2 text-center truncate">{stock.name}</div>
          <div className="h-px bg-white/20 mb-2"></div>
          <div className={`font-bold text-2xl mb-3 text-center ${totalReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalReturn > 0 ? '+' : ''}{totalReturn.toFixed(2)}%
          </div>
          <div className="text-white/90 text-sm space-y-1.5">
            <div className="flex justify-between">
              <span className="text-white/60">Price:</span>
              <span className="font-bold">${stock.price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/60">Market Cap:</span>
              <span className="font-bold">{formatCurrency(stock.currentMarketCap)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/60">Health:</span>
              <span className="font-bold">{(stock.metabolicHealth * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/60">Sector:</span>
              <span className="font-bold text-xs">{stock.sector}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TreemapLayout = ({ stocks, phase }) => {
  const layoutTreemap = (items, x, y, w, h, vertical = true) => {
    if (items.length === 0) return [];
    if (items.length === 1) return [{ ...items[0], x, y, w, h }];

    const totalWeight = items.reduce((acc, item) => acc + (item.currentMarketCap || 1), 0);
    let halfWeight = 0;
    let mid = 0;

    for (let i = 0; i < items.length; i++) {
      halfWeight += items[i].currentMarketCap;
      if (halfWeight >= totalWeight / 2 || i === items.length - 1) {
        mid = i + 1;
        break;
      }
    }

    const ratio = totalWeight > 0 ? halfWeight / totalWeight : 0.5;
    const partA = items.slice(0, mid);
    const partB = items.slice(mid);

    if (vertical) {
      const splitW = w * ratio;
      return [
        ...layoutTreemap(partA, x, y, splitW, h, !vertical),
        ...layoutTreemap(partB, x + splitW, y, w - splitW, h, !vertical)
      ];
    } else {
      const splitH = h * ratio;
      return [
        ...layoutTreemap(partA, x, y, w, splitH, !vertical),
        ...layoutTreemap(partB, x, y + splitH, w, h - splitH, !vertical)
      ];
    }
  };

  const sectorGroups = useMemo(() => {
    const groups = {};
    stocks.forEach(s => {
      if (!groups[s.sector]) groups[s.sector] = { name: s.sector, weight: 0, items: [] };
      groups[s.sector].weight += s.currentMarketCap;
      groups[s.sector].items.push(s);
    });

    const sortedSectors = Object.values(groups).sort((a, b) => b.weight - a.weight);
    const sectorRects = layoutTreemap(sortedSectors.map(g => ({ ...g, currentMarketCap: g.weight })), 0, 0, 100, 100);

    return sectorRects.map(rect => ({
      ...rect,
      tiles: layoutTreemap(rect.items.sort((a, b) => b.currentMarketCap - a.currentMarketCap), 0, 0, 100, 100)
    }));
  }, [stocks]);

  return (
    <div className={`relative w-full h-full bg-slate-950 border-2 border-slate-800 rounded overflow-hidden transition-all duration-300 ${
      phase === 'CLOSED' ? 'opacity-50 grayscale' : ''
    }`}>
      {sectorGroups.map(sector => (
        <div
          key={sector.name}
          className="absolute"
          style={{
            left: `${sector.x}%`,
            top: `${sector.y}%`,
            width: `${sector.w}%`,
            height: `${sector.h}%`,
            border: '2px solid rgba(0, 0, 0, 0.5)'
          }}
        >
          {sector.w > 5 && sector.h > 3 && (
            <div className="absolute top-0 left-0 z-30 pointer-events-none px-1.5 py-0.5 bg-black/30">
              <span className={`uppercase font-black text-white tracking-wider ${
                sector.w > 15 ? 'text-xs' : 'text-[9px]'
              }`}>
                {sector.name}
              </span>
            </div>
          )}
          <div className="relative w-full h-full">
            {sector.tiles.map(tile => (
              <TreemapTile key={tile.id} stock={tile} x={tile.x} y={tile.y} width={tile.w} height={tile.h} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// --- Main Market View ---

export default function MarketView() {
  // Get state from Zustand store
  const { stocks, marketState, regime, phase, periodReturns, logs } = useMarketStore();

  // Calculate derived values
  const activeStocks = stocks.filter(s => s.status === 'active');
  const marketCapTotal = activeStocks.reduce((sum, s) => sum + s.currentMarketCap, 0);
  const avgHealth = activeStocks.length > 0
    ? activeStocks.reduce((sum, s) => sum + s.metabolicHealth, 0) / activeStocks.length
    : 0;

  if (!marketState) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading market data...</div>
      </div>
    );
  }

  const regimeConfig = REGIMES[regime] || REGIMES.GROWTH;

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Header */}
      <header className="grid grid-cols-3 gap-2 shrink-0">
        {/* Regime Indicator */}
        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-center relative">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-1">
            <Activity className="w-3 h-3" /> MARKET REGIME
          </span>
          <h2 className={`text-3xl font-black ${regimeConfig.color} tracking-tight`}>
            {regimeConfig.label}
          </h2>
          <div className="text-xs text-slate-500 mt-1">
            IR: {marketState.interestRate.toFixed(2)}% | VIX: {marketState.vix.toFixed(1)}
          </div>
        </div>

        {/* System Biomass */}
        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-center">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-2">
            <Waves className="w-3 h-3" /> SYSTEM BIOMASS
          </span>

          <div className="flex items-center justify-between mb-3">
            <h2 className="text-2xl font-black text-white tracking-tighter">{formatCurrency(marketCapTotal)}</h2>

            <div className="flex gap-4">
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">60T</div>
                <div className={`text-xs font-black ${
                  periodReturns.return60 === null ? 'text-slate-600' : periodReturns.return60 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {periodReturns.return60 === null ? '—' : `${periodReturns.return60 > 0 ? '+' : ''}${periodReturns.return60.toFixed(1)}%`}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">180T</div>
                <div className={`text-xs font-black ${
                  periodReturns.return180 === null ? 'text-slate-600' : periodReturns.return180 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {periodReturns.return180 === null ? '—' : `${periodReturns.return180 > 0 ? '+' : ''}${periodReturns.return180.toFixed(1)}%`}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">365T</div>
                <div className={`text-xs font-black ${
                  periodReturns.return365 === null ? 'text-slate-600' : periodReturns.return365 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {periodReturns.return365 === null ? '—' : `${periodReturns.return365 > 0 ? '+' : ''}${periodReturns.return365.toFixed(1)}%`}
                </div>
              </div>
            </div>
          </div>

          {/* Health Bar */}
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-500"
              style={{ width: `${avgHealth * 100}%` }}
            />
          </div>
          <span className="text-[9px] text-slate-500 font-bold mt-1">AVG HEALTH: {(avgHealth * 100).toFixed(1)}%</span>
        </div>

        {/* Event Log */}
        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-between">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-2">
            <LayoutGrid className="w-3 h-3" /> MARKET EVENTS
          </span>
          <div className="space-y-1 overflow-hidden">
            {logs.slice(0, 3).map((log, i) => (
              <div key={i} className={`text-[10px] font-mono truncate ${
                log.type === 'error' ? 'text-red-400' : log.type === 'success' ? 'text-green-400' : 'text-yellow-400'
              }`}>
                {log.msg}
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* Main Treemap */}
      <main className="flex-1 min-h-0 flex flex-col gap-2">
        <div className="bg-slate-900 border border-white/5 rounded-lg px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${phase === 'TRADING' ? 'bg-green-400 animate-pulse' : 'bg-slate-600'}`}></div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              {phase === 'TRADING' ? 'Market Open' : 'Market Closed'}
            </span>
          </div>
          <div className="text-xs text-slate-500 font-mono">
            {activeStocks.length} active companies
          </div>
        </div>

        <div className="flex-1 relative">
          <TreemapLayout stocks={activeStocks} phase={phase} />
        </div>
      </main>

      {/* CRASH Overlay */}
      {marketState.vix > 50 && (
        <div className="fixed inset-0 pointer-events-none bg-red-600/5 animate-pulse z-50 flex items-center justify-center">
          <div className="bg-red-600 text-white px-12 py-6 rounded-sm font-black text-7xl shadow-2xl uppercase tracking-tighter opacity-80 -rotate-2 border-8 border-white">
            CRASH
          </div>
        </div>
      )}
    </div>
  );
}
