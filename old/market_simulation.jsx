import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Zap, 
  ShieldAlert, 
  Droplets, 
  Wind,
  Clock,
  Waves,
  LayoutGrid,
  Maximize2,
  BarChart4
} from 'lucide-react';

/**
 * BIOMARKET CAS: High-Density Treemap Simulation
 * Features:
 * - 60-period Total Return Heatmap
 * - Dynamic Market Cap Area Scaling (Expanding/Contracting Tiles)
 * - Trophic Cascade Macro Engine
 */

// --- Constants & Config ---
const SECTORS = {
  Technology: ['Cloud', 'Semiconductors', 'AI Hardware', 'SaaS', 'Cybersecurity'],
  Healthcare: ['Biotech', 'Pharmaceuticals', 'Medical Devices', 'Payors'],
  Energy: ['E&P', 'Renewables', 'Midstream', 'Services'],
  Financials: ['Banks', 'Fintech', 'Asset Management', 'Insurance'],
  Consumer: ['Retail', 'Luxury', 'Staples', 'E-commerce'],
  Industrials: ['Aerospace', 'Logistics', 'Infrastructure', 'Manufacturing'],
  Communication: ['Telco', 'Social Media', 'Streaming', 'Advertising'],
  Materials: ['Mining', 'Chemicals', 'Forestry', 'Steel']
};

const REGIMES = {
  GROWTH: { label: 'Green World (Expansion)', color: 'text-green-400', rateRange: [0, 1.5], vixBase: 12 },
  STAGNATION: { label: 'Punctuated Stasis', color: 'text-yellow-400', rateRange: [1.5, 3.5], vixBase: 20 },
  CONTRACTION: { label: 'Resource Scarcity', color: 'text-orange-500', rateRange: [3.5, 5.0], vixBase: 28 },
  CRISIS: { label: 'Sporulation (Crises)', color: 'text-red-500', rateRange: [4.0, 5.5], vixBase: 45 }
};

const HISTORY_LENGTH = 60; // 60-period window for returns
const TRADING_WINDOW_SECONDS = 60;
const CLOSE_WINDOW_SECONDS = 10;

// --- Helper Functions ---
const logNormalRandom = (mean, stdDev) => {
  const u1 = Math.random();
  const u2 = Math.random();
  const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return Math.exp(mean + stdDev * z0);
};

const formatCurrency = (val) => {
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  return `$${val.toFixed(2)}`;
};

const generateInitialStocks = () => {
  const stocks = [];
  let idCounter = 0;
  Object.entries(SECTORS).forEach(([sector, subIndustries]) => {
    subIndustries.forEach((sub) => {
      const count = Math.floor(Math.random() * 2) + 2;
      for (let i = 0; i < count; i++) {
        const isLargeCap = Math.random() > 0.85;
        const baseCap = isLargeCap 
          ? (Math.random() * 2e12 + 1e12) 
          : (Math.random() * 400e9 + 50e9);
        
        const initialPrice = logNormalRandom(Math.log(100), 0.5);
        
        stocks.push({
          id: `stock-${idCounter++}`,
          ticker: `${sector.substring(0, 2).toUpperCase()}${sub.substring(0, 1).toUpperCase()}${String.fromCharCode(65 + i)}`,
          name: `${sub} ${['Corp', 'Systems', 'Global'][Math.floor(Math.random() * 3)]}`,
          sector,
          subIndustry: sub,
          price: initialPrice,
          sharesOutstanding: baseCap / initialPrice,
          currentMarketCap: baseCap,
          volatility: isLargeCap ? (Math.random() * 0.15 + 0.15) : (Math.random() * 0.6 + 0.30),
          valueScore: Math.min(1, Math.max(0.1, baseCap / 3e12 + Math.random() * 0.2)),
          metabolicHealth: 1.0,
          history: Array(HISTORY_LENGTH).fill(initialPrice), // Fill buffer
          status: 'active'
        });
      }
    });
  });
  return stocks;
};

// --- Components ---

const TreemapTile = ({ stock, x, y, width, height }) => {
  // Calculate 60-period total return
  const startPrice = stock.history[0] || stock.price;
  const totalReturn = ((stock.price - startPrice) / startPrice) * 100;
  
  // Heatmap: 60-period performance gradient
  const getColor = (val) => {
    const intensity = Math.min(Math.abs(val) * 8, 100); 
    if (val >= 0) return `rgb(10, ${60 + intensity * 1.8}, 50)`; // Healthier greens
    return `rgb(${80 + intensity * 1.5}, 20, 30)`; // Stressed reds
  };

  const isSmall = width < 40 || height < 30;
  const isMicro = width < 15 || height < 12;

  return (
    <div 
      className="absolute border border-black/40 transition-all duration-700 ease-in-out flex flex-col items-center justify-center overflow-hidden hover:z-20 hover:ring-2 hover:ring-white/60 group cursor-crosshair"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        width: `${width}%`,
        height: `${height}%`,
        backgroundColor: getColor(totalReturn)
      }}
    >
      {!isMicro && (
        <span className={`font-black text-white leading-none ${isSmall ? 'text-[8px]' : 'text-xs md:text-sm'} drop-shadow-md select-none`}>
          {stock.ticker}
        </span>
      )}
      {!isSmall && (
        <span className="text-[10px] text-white/90 font-bold drop-shadow-sm select-none">
          {totalReturn > 0 ? '+' : ''}{totalReturn.toFixed(1)}%
        </span>
      )}
      {/* Tooltip on hover */}
      <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-1">
        <div className="bg-slate-900/90 text-[8px] px-1 rounded text-white hidden group-hover:block whitespace-nowrap">
          {formatCurrency(stock.currentMarketCap)}
        </div>
      </div>
    </div>
  );
};

const TreemapLayout = ({ stocks }) => {
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
    <div className="relative w-full h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {sectorGroups.map(sector => (
        <div 
          key={sector.name}
          className="absolute border border-black/20"
          style={{ left: `${sector.x}%`, top: `${sector.y}%`, width: `${sector.w}%`, height: `${sector.h}%` }}
        >
          {sector.w > 6 && sector.h > 4 && (
            <div className="absolute top-1 left-2 z-30 pointer-events-none">
              <span className="text-[10px] uppercase font-black text-white tracking-widest drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
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

// --- Main App ---

export default function App() {
  const [stocks, setStocks] = useState(() => generateInitialStocks());
  const [regime, setRegime] = useState('GROWTH');
  const [interestRate, setInterestRate] = useState(1.25);
  const [vix, setVix] = useState(15.5);
  const [time, setTime] = useState(0);
  const [phase, setPhase] = useState('TRADING');
  const [logs, setLogs] = useState([]);
  
  const simulationRef = useRef(null);
  const logIdCounter = useRef(0);
  const stockIdCounter = useRef(5000);

  const addLog = (msg, type = 'info') => {
    const id = `${Date.now()}-${logIdCounter.current++}`;
    setLogs(prev => [{ id, msg, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 5));
  };

  const updateSimulation = () => {
    setTime(prev => {
      const nextTime = prev + 1;
      if (phase === 'TRADING' && nextTime >= TRADING_WINDOW_SECONDS) {
        setPhase('CLOSED');
        addLog("Vertical rebalancing initiated.", "warning");
        return 0;
      }
      if (phase === 'CLOSED' && nextTime >= CLOSE_WINDOW_SECONDS) {
        setPhase('TRADING');
        addLog("New metabolic cycle active.", "success");
        return 0;
      }
      return nextTime;
    });

    if (phase === 'CLOSED') return;

    // Macro Updates
    setRegime(prev => {
      if (Math.random() < 0.005) {
        const regimes = Object.keys(REGIMES);
        const next = regimes[Math.floor(Math.random() * regimes.length)];
        if (next !== prev) {
          addLog(`Regime Shift: ${REGIMES[next].label}`, "error");
          return next;
        }
      }
      return prev;
    });

    setInterestRate(prev => {
      const target = (REGIMES[regime].rateRange[0] + REGIMES[regime].rateRange[1]) / 2;
      return prev + (target - prev) * 0.05 + (Math.random() - 0.5) * 0.02;
    });

    setVix(prev => {
      const base = REGIMES[regime].vixBase;
      const spike = Math.random() > 0.98 ? Math.random() * 30 : 0;
      const decay = (prev - base) * 0.15;
      return Math.max(10, prev - decay + spike + (Math.random() - 0.5));
    });

    // Stock & Area Updates
    setStocks(prevStocks => {
      const updated = prevStocks.map(stock => {
        if (stock.status === 'bankrupt') return stock;

        const metabolicCost = (interestRate / 5.0) * 0.0015 + (vix / 90.0) * 0.002;
        let health = stock.metabolicHealth - metabolicCost;
        
        const isSporulating = vix > 45;
        const shock = isSporulating ? (Math.random() * -0.08) : 0;
        
        const drift = (stock.valueScore * 0.0015) - metabolicCost + shock;
        const vol = (stock.volatility / 35) * (vix / 14);
        const change = Math.exp(drift + vol * (Math.random() - 0.5));
        
        const newPrice = Math.max(0.1, stock.price * change);
        
        // Extinction Logic
        if (newPrice < 0.5 || health <= 0) {
          addLog(`Extinction: ${stock.ticker}`, 'error');
          return { ...stock, status: 'bankrupt', price: 0, currentMarketCap: 0 };
        }

        // Buffer Management
        const newHistory = [...stock.history, newPrice].slice(-HISTORY_LENGTH);

        return {
          ...stock,
          price: newPrice,
          currentMarketCap: newPrice * stock.sharesOutstanding,
          metabolicHealth: health,
          history: newHistory
        };
      });

      // Sprouting (Sustainability of the System)
      const activeCount = updated.filter(s => s.status === 'active').length;
      if (activeCount < prevStocks.length * 0.9) {
        const deadIdx = updated.findIndex(s => s.status === 'bankrupt');
        if (deadIdx !== -1) {
          const sKeys = Object.keys(SECTORS);
          const sector = sKeys[Math.floor(Math.random() * sKeys.length)];
          const sub = SECTORS[sector][0];
          const newPrice = 80 + Math.random() * 40;
          updated[deadIdx] = {
            id: `stock-${stockIdCounter.current++}`,
            ticker: `SPRT${stockIdCounter.current % 100}`,
            name: `${sub} Sprout`,
            sector,
            subIndustry: sub,
            price: newPrice,
            sharesOutstanding: (50e9 + Math.random() * 50e9) / newPrice,
            currentMarketCap: 50e9,
            volatility: 0.6,
            valueScore: 0.4,
            metabolicHealth: 1.0,
            history: Array(HISTORY_LENGTH).fill(newPrice),
            status: 'active'
          };
        }
      }
      return updated;
    });
  };

  useEffect(() => {
    simulationRef.current = setInterval(updateSimulation, 500);
    return () => clearInterval(simulationRef.current);
  }, [regime, phase, interestRate, vix]);

  const activeStocks = useMemo(() => stocks.filter(s => s.status === 'active'), [stocks]);
  const marketCapTotal = useMemo(() => activeStocks.reduce((acc, s) => acc + s.currentMarketCap, 0), [activeStocks]);
  const avgHealth = activeStocks.length > 0 ? activeStocks.reduce((acc, s) => acc + s.metabolicHealth, 0) / activeStocks.length : 0;

  return (
    <div className="fixed inset-0 bg-slate-950 text-slate-200 font-sans p-4 flex flex-col gap-4 overflow-hidden">
      {/* --- DASHBOARD HEADER --- */}
      <header className="grid grid-cols-1 md:grid-cols-4 gap-4 h-28 shrink-0">
        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-center relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1">
              <Activity className="w-3 h-3" /> APEX REGIME
            </span>
            <div className={`w-2 h-2 rounded-full ${phase === 'TRADING' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          </div>
          <h2 className={`text-lg font-black italic tracking-tighter truncate ${REGIMES[regime].color}`}>{REGIMES[regime].label}</h2>
          <div className="flex gap-4 mt-1 text-xs font-bold text-slate-300">
            <span>Int. Rate: {interestRate.toFixed(2)}%</span>
            <span className={vix > 35 ? 'text-red-400' : 'text-blue-400'}>VIX: {vix.toFixed(1)}</span>
          </div>
          <div className="absolute bottom-0 left-0 h-1 bg-white/5 w-full">
            <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${(time / (phase === 'TRADING' ? TRADING_WINDOW_SECONDS : CLOSE_WINDOW_SECONDS)) * 100}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-center">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-1">
            <Waves className="w-3 h-3" /> SYSTEM BIOMASS
          </span>
          <h2 className="text-2xl font-black text-white tracking-tighter">{formatCurrency(marketCapTotal)}</h2>
          <div className="w-full h-1 bg-slate-800 rounded-full mt-2 overflow-hidden">
            <div className="h-full bg-emerald-500" style={{ width: `${avgHealth * 100}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl col-span-2 hidden md:flex flex-col">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-1">
             <Wind className="w-3 h-3" /> MYCORRHIZAL LOG
          </span>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1">
            {logs.map(log => (
              <div key={log.id} className="text-[9px] font-bold truncate border-l-2 border-white/10 pl-2 flex justify-between">
                <span className={log.type === 'error' ? 'text-red-500' : log.type === 'success' ? 'text-emerald-500' : 'text-blue-400'}>
                  {log.msg}
                </span>
                <span className="text-slate-600 tabular-nums">{log.time.split(' ')[0]}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* --- DYNAMIC TREEMAP VISUALIZER --- */}
      <main className="flex-1 min-h-0 flex flex-col gap-2">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            <LayoutGrid className="w-4 h-4 text-emerald-500" />
            <h3 className="text-[11px] font-black uppercase text-slate-400 tracking-widest">
              Hierarchical Biomass Heatmap <span className="text-slate-600">(60-Period Return)</span>
            </h3>
          </div>
          <div className="flex items-center gap-4 text-[9px] font-black uppercase tracking-tighter">
            <div className="flex items-center gap-1"><div className="w-2 h-2 bg-emerald-600" /> Metabolic Surge</div>
            <div className="flex items-center gap-1"><div className="w-2 h-2 bg-red-800" /> Trophic Decay</div>
            <div className="flex items-center gap-1 text-slate-500"><BarChart4 className="w-3 h-3" /> Tile Size = Rel. Valuation</div>
          </div>
        </div>
        
        <div className="flex-1 relative">
          <TreemapLayout stocks={activeStocks} />
        </div>
      </main>

      {/* --- SYSTEM FOOTER --- */}
      <footer className="h-10 shrink-0 bg-slate-900/40 border-t border-white/5 flex items-center justify-between px-6">
        <div className="flex gap-8 items-center">
          <div className="flex items-center gap-2">
            <Zap className={`w-3 h-3 ${vix > 40 ? 'text-yellow-400 animate-pulse' : 'text-slate-600'}`} />
            <span className="text-[9px] font-black uppercase text-slate-500">Quorum:</span>
            <span className="text-[10px] font-bold text-slate-300">{vix > 40 ? 'SURVIVAL_MODE' : 'RESOURCE_FORAGING'}</span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-3 h-3 text-slate-600" />
            <span className="text-[9px] font-black uppercase text-slate-500">Sporulation Buffer:</span>
            <span className="text-[10px] font-bold text-slate-300">{(100 - (vix / 80) * 100).toFixed(0)}%</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Maximize2 className="w-3 h-3 text-slate-600" />
          <Clock className="w-3 h-3 text-slate-600" />
          <span className="text-[10px] tabular-nums font-black text-slate-500 uppercase">SYS_TICK: {Math.floor(Date.now() / 1000) % 99999}</span>
        </div>
      </footer>

      {/* --- CRISIS OVERLAY --- */}
      {vix > 50 && (
        <div className="fixed inset-0 pointer-events-none bg-red-600/5 animate-pulse z-50 flex items-center justify-center">
          <div className="bg-red-600 text-white px-12 py-6 rounded-sm font-black text-7xl shadow-2xl uppercase tracking-tighter opacity-80 -rotate-2 border-8 border-white">
             CRASH
          </div>
        </div>
      )}
    </div>
  );
}
