// Alternative: Export to CSV for Analysis
// If you want CSV format for easier analysis in Excel/Python:

const downloadAnalyticsCSV = () => {
    const ws = new WebSocket('ws://localhost:8000/ws/market');

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'update' && message.data?.analytics) {
          const analytics = message.data.analytics;
          const cycles = [...analytics.completed_cycles];
          if (analytics.current_cycle) cycles.push(analytics.current_cycle);

          // CSV Headers
          const headers = [
            'cycle_number', 'is_complete', 'start_tick', 'end_tick',
            'ipo_count', 'bankruptcy_count', 'regime_transitions',
            'min_companies', 'max_companies', 'avg_companies',
            'min_vix', 'median_vix', 'max_vix',
            'min_interest_rate', 'median_interest_rate', 'max_interest_rate',
            'return_60t', 'return_180t', 'return_365t',
            'regime_growth_periods', 'regime_stagnation_periods',
            'regime_contraction_periods', 'regime_crisis_periods'
          ];

          // CSV Rows
          const rows = cycles.map(c => [
            c.cycle_number,
            c.is_complete,
            c.start_tick,
            c.end_tick,
            c.ipo_count,
            c.bankruptcy_count,
            c.regime_transitions,
            c.min_companies,
            c.max_companies,
            c.avg_companies,
            c.min_vix,
            c.median_vix,
            c.max_vix,
            c.min_interest_rate,
            c.median_interest_rate,
            c.max_interest_rate,
            c.return_60t || '',
            c.return_180t || '',
            c.return_365t || '',
            c.regime_periods.GROWTH || 0,
            c.regime_periods.STAGNATION || 0,
            c.regime_periods.CONTRACTION || 0,
            c.regime_periods.CRISIS || 0
          ]);

          const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const blob = new Blob([csv], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `market-analytics-${timestamp}.csv`;
          a.click();
          URL.revokeObjectURL(url);

          console.log(`💾 Downloaded CSV with ${cycles.length} cycles`);
          ws.close();
        }
      } catch (e) {
        console.error('Error:', e);
      }
    };

    ws.onopen = () => console.log('🔌 Connected, waiting for data...');
    ws.onerror = (e) => console.error('❌ WebSocket error:', e);
  };

  downloadAnalyticsCSV();