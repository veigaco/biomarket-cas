import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { TrendingUp, Users, Building2, AlertTriangle } from 'lucide-react';
import { useMarketStore } from '../store/marketStore';

export default function AnalyticsView() {
  const { analytics } = useMarketStore();

  if (!analytics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading analytics data...</div>
      </div>
    );
  }

  const { completed_cycles, current_cycle, summary } = analytics;
  const allCycles = [...completed_cycles, current_cycle].filter(Boolean);

  // Progress indicator
  const progressPercent = summary.current_cycle_progress_pct || 0;
  const cycleLabel = current_cycle && !current_cycle.is_complete
    ? `Cycle ${current_cycle.cycle_number} (partial)`
    : 'No active cycle';

  return (
    <div className="flex flex-col gap-4 h-full overflow-y-auto p-4">
      {/* Progress Indicator */}
      <div className="bg-slate-900 border border-white/5 p-4 rounded-xl">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-bold text-slate-300">
            {cycleLabel} - {summary.current_cycle_ticks}/7,300 ticks
          </span>
          <span className="text-sm font-bold text-green-400">
            {progressPercent.toFixed(1)}%
          </span>
        </div>
        <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-600 to-green-400 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <span className="text-xs text-slate-500 font-bold uppercase">Completed Cycles</span>
          </div>
          <div className="text-3xl font-black text-white">
            {summary.total_completed_cycles}
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="w-5 h-5 text-blue-400" />
            <span className="text-xs text-slate-500 font-bold uppercase">Total IPOs</span>
          </div>
          <div className="text-3xl font-black text-white">
            {summary.total_ipos}
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-xs text-slate-500 font-bold uppercase">Total Bankruptcies</span>
          </div>
          <div className="text-3xl font-black text-white">
            {summary.total_bankruptcies}
          </div>
        </div>

        <div className="bg-slate-900 border border-white/5 p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-yellow-400" />
            <span className="text-xs text-slate-500 font-bold uppercase">Avg Companies</span>
          </div>
          <div className="text-3xl font-black text-white">
            {summary.avg_companies.toFixed(0)}
          </div>
        </div>
      </div>

      {/* Charts */}
      {allCycles.length > 0 && (
        <>
          {/* Returns Chart */}
          <div className="bg-slate-900 border border-white/5 p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-4">Period Returns by Cycle</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={allCycles.map(c => ({
                name: c.is_complete ? `Cycle ${c.cycle_number}` : `Cycle ${c.cycle_number} (partial)`,
                '60T': c.return_60t,
                '180T': c.return_180t,
                '365T': c.return_365t
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                <Line type="monotone" dataKey="60T" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="180T" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="365T" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Company Count Chart */}
          <div className="bg-slate-900 border border-white/5 p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-4">Company Count by Cycle</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={allCycles.map(c => ({
                name: c.is_complete ? `Cycle ${c.cycle_number}` : `C${c.cycle_number}*`,
                Min: c.min_companies,
                Avg: c.avg_companies,
                Max: c.max_companies
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} label={{ value: 'Companies', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                <Bar dataKey="Min" fill="#ef4444" />
                <Bar dataKey="Avg" fill="#3b82f6" />
                <Bar dataKey="Max" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Events Chart */}
          <div className="bg-slate-900 border border-white/5 p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-4">Market Events by Cycle</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={allCycles.map(c => ({
                name: c.is_complete ? `Cycle ${c.cycle_number}` : `C${c.cycle_number}*`,
                IPOs: c.ipo_count,
                Bankruptcies: c.bankruptcy_count
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" style={{ fontSize: '12px' }} />
                <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} label={{ value: 'Count', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
                <Bar dataKey="IPOs" fill="#10b981" />
                <Bar dataKey="Bankruptcies" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed Table */}
          <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Detailed Cycle Statistics</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-300 uppercase">Cycle</th>
                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-300 uppercase">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">IPOs</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">Bankruptcies</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">Avg Companies</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">Transitions</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">VIX Min/Med/Max</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">IR Min/Med/Max</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-slate-300 uppercase">60T / 180T / 365T</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {allCycles.map((cycle) => (
                    <tr key={`${cycle.cycle_number}-${cycle.is_complete}`} className="hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-white font-mono">
                        {cycle.cycle_number}
                      </td>
                      <td className="px-4 py-3">
                        {cycle.is_complete ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-green-900/30 text-green-400 border border-green-500/30">
                            Complete
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-yellow-900/30 text-yellow-400 border border-yellow-500/30">
                            Partial
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-green-400 font-bold">{cycle.ipo_count}</td>
                      <td className="px-4 py-3 text-right text-red-400 font-bold">{cycle.bankruptcy_count}</td>
                      <td className="px-4 py-3 text-right text-white font-mono">{cycle.avg_companies}</td>
                      <td className="px-4 py-3 text-right text-slate-300 font-mono">{cycle.regime_transitions}</td>
                      <td className="px-4 py-3 text-right text-slate-300 font-mono text-xs">
                        {cycle.min_vix} / {cycle.median_vix} / {cycle.max_vix}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-300 font-mono text-xs">
                        {cycle.min_interest_rate} / {cycle.median_interest_rate} / {cycle.max_interest_rate}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-xs">
                        <span className={cycle.return_60t !== null ? (cycle.return_60t >= 0 ? 'text-green-400' : 'text-red-400') : 'text-slate-600'}>
                          {cycle.return_60t !== null ? `${cycle.return_60t > 0 ? '+' : ''}${cycle.return_60t}%` : '—'}
                        </span>
                        {' / '}
                        <span className={cycle.return_180t !== null ? (cycle.return_180t >= 0 ? 'text-green-400' : 'text-red-400') : 'text-slate-600'}>
                          {cycle.return_180t !== null ? `${cycle.return_180t > 0 ? '+' : ''}${cycle.return_180t}%` : '—'}
                        </span>
                        {' / '}
                        <span className={cycle.return_365t !== null ? (cycle.return_365t >= 0 ? 'text-green-400' : 'text-red-400') : 'text-slate-600'}>
                          {cycle.return_365t !== null ? `${cycle.return_365t > 0 ? '+' : ''}${cycle.return_365t}%` : '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Regime Breakdown (Optional - shows regime periods for each cycle) */}
          <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <h3 className="text-lg font-bold text-white">Regime Distribution by Cycle</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-bold text-slate-300 uppercase">Cycle</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-green-300 uppercase">Growth</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-yellow-300 uppercase">Stagnation</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-orange-300 uppercase">Contraction</th>
                    <th className="px-4 py-3 text-right text-xs font-bold text-red-300 uppercase">Crisis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {allCycles.map((cycle) => (
                    <tr key={`${cycle.cycle_number}-regime`} className="hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-white font-mono">
                        Cycle {cycle.cycle_number} {!cycle.is_complete && '(partial)'}
                      </td>
                      <td className="px-4 py-3 text-right text-green-400 font-bold">
                        {cycle.regime_periods.GROWTH || 0}
                      </td>
                      <td className="px-4 py-3 text-right text-yellow-400 font-bold">
                        {cycle.regime_periods.STAGNATION || 0}
                      </td>
                      <td className="px-4 py-3 text-right text-orange-400 font-bold">
                        {cycle.regime_periods.CONTRACTION || 0}
                      </td>
                      <td className="px-4 py-3 text-right text-red-400 font-bold">
                        {cycle.regime_periods.CRISIS || 0}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
