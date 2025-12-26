# BioMarket CAS - Market Simulation Engine

A React-based financial market simulation using biological metaphors to model ecosystem-like market dynamics.

## Quick Start

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

Then open the URL shown in your terminal (usually http://localhost:5173)

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## What You'll See

- **Dynamic Treemap**: Tiles expand/contract based on market capitalization
- **Color Heatmap**: Green = positive returns, Red = negative returns (60-period)
- **Live Simulation**: Updates every 500ms
- **Market Regimes**: Watch as the economy shifts between GROWTH, STAGNATION, CONTRACTION, and CRISIS
- **Extinctions & Sprouts**: Companies die and new ones are born
- **CRASH Overlay**: Appears when VIX > 50

## How It Works

See `engine_explainer.md` for an intuitive breakdown of the market engine mechanics.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

## Project Structure

```
mkteng/
├── src/
│   ├── App.jsx           # Main application component
│   ├── main.jsx          # React entry point
│   └── index.css         # Tailwind imports
├── index.html            # HTML entry point
├── market_simulation.jsx # Original standalone version
├── CLAUDE.md            # Technical documentation
└── engine_explainer.md   # Intuitive engine explanation
```

## Development

The simulation runs on a 500ms tick interval. Key parameters can be adjusted in `src/App.jsx`:

- `HISTORY_LENGTH` - Price history buffer (default: 60)
- `TRADING_WINDOW_SECONDS` - Active trading duration (default: 60)
- `CLOSE_WINDOW_SECONDS` - Rebalancing duration (default: 10)
