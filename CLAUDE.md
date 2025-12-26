# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BioMarket CAS (Complex Adaptive System)** - A React-based financial market simulation using biological metaphors to model market dynamics. The application visualizes stocks as a dynamic treemap heatmap with expanding/contracting tiles based on market capitalization, simulating ecosystem-like market behavior.

## Architecture

### Single-File React Application
- **File**: `market_simulation.jsx`
- **Framework**: React with hooks (useState, useEffect, useRef, useMemo)
- **Styling**: Tailwind CSS (via CDN)
- **Icons**: Lucide React

### Core Simulation Engine

The simulation operates on a 500ms tick interval with two distinct phases:
- **TRADING** phase (60 seconds) - Active price updates and market cap changes
- **CLOSED** phase (10 seconds) - Vertical rebalancing period

### Key Systems

1. **Trophic Cascade Macro Engine**
   - 4 market regimes: GROWTH, STAGNATION, CONTRACTION, CRISIS
   - Dynamic interest rates and VIX volatility
   - Regime shifts occur randomly (~0.5% chance per tick)

2. **Stock Metabolism & Lifecycle**
   - Each stock has `metabolicHealth` that decays based on interest rates and VIX
   - Stocks can go **extinct** (bankrupt) when price < $0.5 or health <= 0
   - Dead stocks are replaced by **sprouts** (new stocks) to maintain ecosystem stability
   - Each stock maintains a 60-period price history buffer

3. **Dynamic Market Cap Scaling**
   - Treemap tiles expand/contract based on real-time market cap
   - Market cap = price × shares outstanding
   - Price updates use log-normal distribution with drift and volatility

4. **60-Period Total Return Heatmap**
   - Color intensity based on performance since period start
   - Green gradient (positive returns): `rgb(10, 60+intensity*1.8, 50)`
   - Red gradient (negative returns): `rgb(80+intensity*1.5, 20, 30)`

### Data Structure

**Stock Object**:
```javascript
{
  id, ticker, name, sector, subIndustry,
  price, sharesOutstanding, currentMarketCap,
  volatility, valueScore, metabolicHealth,
  history: [60 prices], // rolling buffer
  status: 'active' | 'bankrupt'
}
```

**Sectors**: 8 sectors (Technology, Healthcare, Energy, Financials, Consumer, Industrials, Communication, Materials), each with 4-5 sub-industries

### Treemap Layout Algorithm

Located in `TreemapLayout` component:
- Recursive binary space partitioning
- Alternates between vertical/horizontal splits
- Weights based on market capitalization
- Two-level hierarchy: sectors → individual stocks

## Development Setup

This is a standalone JSX file meant to be run in a React environment. No package.json or build system is currently configured.

### To Run This Application:

1. **Create an HTML entry point** (`index.html`):
   - Load React, ReactDOM, and Babel from CDN
   - Include Tailwind CSS: `<script src="https://cdn.tailwindcss.com"></script>`
   - Import Lucide React icons
   - Transpile and render `market_simulation.jsx`

2. **OR** convert to a standard React project:
   - Initialize with `npm create vite@latest` (React template)
   - Install dependencies: `react`, `react-dom`, `lucide-react`
   - Configure Tailwind CSS
   - Move code to `App.jsx`

## Key Constants & Configuration

- `HISTORY_LENGTH = 60` - Price history buffer size (affects return calculation)
- `TRADING_WINDOW_SECONDS = 60` - Length of active trading phase
- `CLOSE_WINDOW_SECONDS = 10` - Length of rebalancing phase
- Simulation tick rate: `500ms` (set in `useEffect` interval)

## Important Implementation Notes

### Price Generation
- Initial prices use `logNormalRandom(mean, stdDev)` helper
- Price updates: `newPrice = price * exp(drift + volatility * randomWalk)`
- Drift calculation includes value score, metabolic cost, and crisis shocks

### Performance Considerations
- Treemap recalculates on every stock array change via `useMemo`
- Tile rendering uses CSS transforms (left/top/width/height percentages)
- Transition duration: 700ms for smooth animations

### State Management Pattern
- All state in root `App` component
- Simulation updates via single `updateSimulation()` function
- Logs limited to 5 most recent entries to prevent memory growth

## Styling Conventions

- Uses Tailwind utility classes throughout
- Dark theme: slate-900/slate-950 backgrounds
- Responsive breakpoints: `md:` prefix for desktop-specific styles
- Micro-optimizations: conditional rendering based on tile size (`isSmall`, `isMicro`)
- Drop shadows and borders for visual hierarchy

## Event Log System

The "Mycorrhizal Log" displays 5 recent events:
- **info** (blue): General updates
- **success** (emerald): New cycles
- **warning** (orange): Rebalancing
- **error** (red): Extinctions and regime shifts
