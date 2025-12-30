// Quick Download of All Historical Data

//  Paste this into the Chrome console:

  // Capture analytics from the next WebSocket update
  const downloadHistoricalAnalytics = () => {
    console.log('🔍 Waiting for analytics data from WebSocket...');

    const ws = new WebSocket('ws://localhost:8000/ws/market');

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'update' && message.data?.analytics) {
          const analytics = message.data.analytics;

          console.log('✅ Analytics data captured!');
          console.log(`📊 Completed cycles: ${analytics.summary.total_completed_cycles}`);
          console.log(`📊 Total IPOs: ${analytics.summary.total_ipos}`);
          console.log(`📊 Total Bankruptcies: ${analytics.summary.total_bankruptcies}`);

          // Download as JSON
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
          const filename = `market-analytics-${timestamp}.json`;

          const json = JSON.stringify(analytics, null, 2);
          const blob = new Blob([json], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);

          console.log(`💾 Downloaded ${filename}`);
          console.log(`📦 File contains ${analytics.completed_cycles.length} completed cycles + current partial cycle`);

          // Close the WebSocket
          ws.close();
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      console.log('Make sure backend is running at localhost:8000');
    };

    ws.onopen = () => {
      console.log('🔌 Connected to WebSocket, waiting for data...');
    };
  };

  // Run it
  downloadHistoricalAnalytics();

// This will:
// 1. Connect to the WebSocket
// 2. Wait for the next analytics update (~1 second)
// 3. Automatically download a JSON file with all historical data including:
//   - All completed cycles from overnight
//   - Current partial cycle
//   - Summary statistics