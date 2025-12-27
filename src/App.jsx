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
  GROWTH: {
    label: 'Bull Market',
    color: 'text-green-400',
    rateRange: [0, 1.5],
    vixBase: 15,              // Increased from 12 to keep VIX average ~18
    driftMultiplier: 6.5,     // Target: ~30% annual (bull years)
    healthRegen: 0.0002       // Strong regeneration
  },
  STAGNATION: {
    label: 'Sideways Market',
    color: 'text-yellow-400',
    rateRange: [1.5, 3.5],
    vixBase: 18,              // Reduced from 20
    driftMultiplier: 1.2,     // Target: ~5% annual (normal years)
    healthRegen: 0.00001      // Minimal regeneration
  },
  CONTRACTION: {
    label: 'Correction',
    color: 'text-orange-500',
    rateRange: [3.5, 5.0],
    vixBase: 25,              // Reduced from 28
    driftMultiplier: -1.2,    // Target: ~-5% annual (correction years)
    healthRegen: -0.00005     // Active decay
  },
  CRISIS: {
    label: 'Bear Market',      // Changed from 'Sporulation (Crises)'
    color: 'text-red-500',
    rateRange: [4.0, 5.5],
    vixBase: 35,              // Reduced from 45 (NO SPORULATION TRIGGER)
    driftMultiplier: -5.0,    // Target: ~-20% annual (bear years)
    healthRegen: -0.0002      // Strong decay
  }
};

// Weighted transition probabilities (regimes persist longer for realistic annual variance)
const REGIME_TRANSITIONS = {
  GROWTH: {
    GROWTH: 0.997,       // 99.7% stay (avg 333 ticks before transition)
    STAGNATION: 0.002,
    CONTRACTION: 0.001,
    CRISIS: 0.0          // Can't go directly to CRISIS from GROWTH
  },
  STAGNATION: {
    GROWTH: 0.001,
    STAGNATION: 0.994,   // 99.4% stay
    CONTRACTION: 0.003,
    CRISIS: 0.002
  },
  CONTRACTION: {
    GROWTH: 0.002,
    STAGNATION: 0.002,
    CONTRACTION: 0.993,  // 99.3% stay
    CRISIS: 0.003        // Can escalate to CRISIS
  },
  CRISIS: {
    GROWTH: 0.001,       // Rare recovery
    STAGNATION: 0.003,
    CONTRACTION: 0.001,
    CRISIS: 0.995        // 99.5% stay (bear markets persist!)
  }
};

const HISTORY_LENGTH = 60; // 60-period window for returns
const TRADING_WINDOW_TICKS = 12;  // 6 seconds at 500ms/tick (1 trading day)
const CLOSE_WINDOW_TICKS = 8;     // 4 seconds at 500ms/tick (market closed)

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

const generateSectorTicker = (sector) => {
  const firstLetter = sector.charAt(0).toUpperCase();
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const length = Math.random() > 0.5 ? 3 : 4;
  let ticker = firstLetter;
  for (let i = 1; i < length; i++) {
    ticker += letters[Math.floor(Math.random() * letters.length)];
  }
  return ticker;
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
          ticker: generateSectorTicker(sector),
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
    const isLeftSide = x < 50; // Left half of screen
    const isTopSide = y < 50; // Top half of screen

    // Position modal to avoid cursor and screen edges
    if (isLeftSide && isTopSide) {
      // Top-left quadrant: show modal bottom-right
      return 'left-0 top-full mt-2';
    } else if (!isLeftSide && isTopSide) {
      // Top-right quadrant: show modal bottom-left
      return 'right-0 top-full mt-2';
    } else if (isLeftSide && !isTopSide) {
      // Bottom-left quadrant: show modal top-right
      return 'left-0 bottom-full mb-2';
    } else {
      // Bottom-right quadrant: show modal top-left
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
          {/* Ticker - always visible on non-small tiles */}
          <div className={`font-black text-white leading-none tracking-tight ${
            isMedium ? 'text-[9px]' : isLarge ? 'text-base' : 'text-xs'
          }`}>
            {stock.ticker}
          </div>

          {/* Percentage - visible on medium+ tiles */}
          {!isMedium && (
            <div className={`font-bold leading-none ${
              totalReturn >= 0 ? 'text-white/95' : 'text-white/90'
            } ${isLarge ? 'text-sm' : 'text-[10px]'}`}>
              {totalReturn > 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </div>
          )}

          {/* Company name and cap - only on large tiles */}
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

      {/* Floating hover modal - appears beside the tile, never over cursor */}
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
          {/* Sector label - positioned top-left with better visibility */}
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

// --- Main App ---

export default function App() {
  const [stocks, setStocks] = useState(() => generateInitialStocks());
  const [regime, setRegime] = useState('GROWTH');
  const [interestRate, setInterestRate] = useState(1.25);
  const [vix, setVix] = useState(15.5);
  const [time, setTime] = useState(0);
  const [phase, setPhase] = useState('TRADING');
  const [logs, setLogs] = useState([]);
  const [marketCapHistory, setMarketCapHistory] = useState([]);

  const simulationRef = useRef(null);
  const logIdCounter = useRef(0);
  const stockIdCounter = useRef(5000);

  const addLog = (msg, type = 'info') => {
    const id = `${Date.now()}-${logIdCounter.current++}`;
    setLogs(prev => [{ id, msg, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 5));
  };

  const updateSimulation = () => {
    setTime(prev => {
      const nextTick = prev + 1;
      if (phase === 'TRADING' && nextTick >= TRADING_WINDOW_TICKS) {
        setPhase('CLOSED');
        addLog("Market closing - after-hours trading begins", "warning");
        return 0;
      }
      if (phase === 'CLOSED' && nextTick >= CLOSE_WINDOW_TICKS) {
        setPhase('TRADING');
        // Create gap/disconnect on market open (simulate pre-market movement)
        setStocks(prevStocks => prevStocks.map(stock => {
          if (stock.status === 'bankrupt') return stock;
          const gapDirection = Math.random() > 0.5 ? 1 : -1;
          const gapMagnitude = (Math.random() * 0.015 + 0.005) * gapDirection; // 0.5% to 2%
          const gappedPrice = stock.price * (1 + gapMagnitude);
          return { ...stock, price: Math.max(0.1, gappedPrice) };
        }));
        addLog("Market open - gap from overnight drift", "success");
        return 0;
      }
      return nextTick;
    });

    // Prices drift 24/7 (no longer gated by phase)

    // Macro Updates - Weighted regime transitions for persistence
    setRegime(prev => {
      const transitions = REGIME_TRANSITIONS[prev];
      const rand = Math.random();
      let cumulative = 0;

      for (const [nextRegime, prob] of Object.entries(transitions)) {
        cumulative += prob;
        if (rand < cumulative) {
          if (nextRegime !== prev) {
            addLog(`Regime Shift: ${REGIMES[nextRegime].label}`, "error");
          }
          return nextRegime;
        }
      }
      return prev; // Fallback
    });

    setInterestRate(prev => {
      const target = (REGIMES[regime].rateRange[0] + REGIMES[regime].rateRange[1]) / 2;
      return prev + (target - prev) * 0.05 + (Math.random() - 0.5) * 0.02;
    });

    setVix(prev => {
      const base = REGIMES[regime].vixBase;

      // VIX spike logic: frequent small spikes, rare large spikes
      let spike = 0;
      const rand = Math.random();
      if (rand > 0.998) {
        // 0.2% chance: Rare large spike (+15 to +40) → VIX 30-70 range
        spike = Math.random() * 25 + 15;
      } else if (rand > 0.99) {
        // 1% chance: Common small spike (+5 to +12) → VIX mid-20s
        spike = Math.random() * 7 + 5;
      }

      const decay = (prev - base) * 0.15;
      const noise = (Math.random() - 0.5) * 1.5; // Reduced noise from ±0.5 to ±0.75
      return Math.max(10, prev - decay + spike + noise);
    });

    // Stock & Area Updates
    setStocks(prevStocks => {
      const updated = prevStocks.map(stock => {
        if (stock.status === 'bankrupt') return stock;

        // --- IMPROVED METABOLIC SYSTEM ---

        // 1. Base metabolic cost (doubled for more bankruptcies and IPO activity)
        const baseCost = (interestRate / 5.0) * 0.0008 + (vix / 90.0) * 0.001;

        // 2. Calculate return-based health regeneration
        const recentReturn = stock.history.length >= 5
          ? (stock.price - stock.history[stock.history.length - 5]) / stock.history[stock.history.length - 5]
          : 0;
        const performanceRegen = recentReturn * 0.02; // Profitable stocks regenerate health

        // 3. Regime-based health adjustment
        const regimeRegen = REGIMES[regime].healthRegen || 0;

        // 4. Net health change (can now be positive!)
        const healthChange = -baseCost + performanceRegen + regimeRegen;
        let health = Math.min(1.2, Math.max(0, stock.metabolicHealth + healthChange)); // Cap at 120%

        // --- IMPROVED PRICE DYNAMICS ---

        // 1. Base drift with regime multiplier (calibrated for ~7-10% annual return)
        const regimeMultiplier = REGIMES[regime].driftMultiplier || 1.0;
        const baseDrift = (stock.valueScore * 0.00002) * regimeMultiplier; // Realistic growth bias

        // 2. No crisis shocks - let drift and volatility handle market dynamics
        const shock = 0;

        // 3. Health bonus: healthy companies grow faster
        const healthBonus = (health - 0.5) * 0.001; // Bonus when health > 50%

        // 4. Final drift calculation
        const drift = baseDrift + healthBonus + shock;

        // 5. Volatility (unchanged)
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

      // IPO Mechanism (Replaces bankruptcies with realistic new companies)
      const activeCount = updated.filter(s => s.status === 'active').length;
      if (activeCount < prevStocks.length * 0.9) {
        const deadIdx = updated.findIndex(s => s.status === 'bankrupt');
        if (deadIdx !== -1) {
          const sKeys = Object.keys(SECTORS);
          const sector = sKeys[Math.floor(Math.random() * sKeys.length)];
          const subIndustries = SECTORS[sector];
          const sub = subIndustries[Math.floor(Math.random() * subIndustries.length)];
          const newPrice = 80 + Math.random() * 40;
          updated[deadIdx] = {
            id: `stock-${stockIdCounter.current++}`,
            ticker: generateSectorTicker(sector),
            name: `${sub} ${['Inc', 'Corp', 'Group', 'Holdings'][Math.floor(Math.random() * 4)]}`,
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
          addLog(`IPO: ${updated[deadIdx].ticker} (${sector})`, 'success');
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

  // Track market cap history for period returns
  useEffect(() => {
    setMarketCapHistory(prev => [...prev, marketCapTotal].slice(-366)); // Keep last 366 ticks (need 366 for 365T calc)
  }, [marketCapTotal]);

  // Calculate period returns
  const getPeriodReturn = (periods) => {
    if (marketCapHistory.length < periods + 1) return null;
    const startCap = marketCapHistory[marketCapHistory.length - periods - 1];
    const currentCap = marketCapTotal;
    if (startCap === 0) return null;
    return ((currentCap - startCap) / startCap) * 100;
  };

  const return60 = getPeriodReturn(60);
  const return180 = getPeriodReturn(180);
  const return365 = getPeriodReturn(365);

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
            <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${(time / (phase === 'TRADING' ? TRADING_WINDOW_TICKS : CLOSE_WINDOW_TICKS)) * 100}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl flex flex-col justify-center">
          <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-1 mb-2">
            <Waves className="w-3 h-3" /> SYSTEM BIOMASS
          </span>

          {/* Biomass and Period Returns - Horizontal Layout */}
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-2xl font-black text-white tracking-tighter">{formatCurrency(marketCapTotal)}</h2>

            <div className="flex gap-4">
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">60T</div>
                <div className={`text-xs font-black ${
                  return60 === null ? 'text-slate-600' : return60 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {return60 === null ? '—' : `${return60 > 0 ? '+' : ''}${return60.toFixed(1)}%`}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">180T</div>
                <div className={`text-xs font-black ${
                  return180 === null ? 'text-slate-600' : return180 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {return180 === null ? '—' : `${return180 > 0 ? '+' : ''}${return180.toFixed(1)}%`}
                </div>
              </div>
              <div className="text-center">
                <div className="text-[8px] text-slate-500 font-bold mb-0.5">365T</div>
                <div className={`text-xs font-black ${
                  return365 === null ? 'text-slate-600' : return365 >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {return365 === null ? '—' : `${return365 > 0 ? '+' : ''}${return365.toFixed(1)}%`}
                </div>
              </div>
            </div>
          </div>

          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
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
          <TreemapLayout stocks={activeStocks} phase={phase} />
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
