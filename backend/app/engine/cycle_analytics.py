"""
Cycle analytics tracker for market simulation.

Tracks market behavior over full cycles (7,300 ticks = 365 periods = ~60 minutes).
Provides cumulative statistics for both completed cycles and current partial cycle.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import deque
import statistics

from ..models.regime import Regime


TICKS_PER_CYCLE = 7300  # 365 periods × 20 ticks/period


@dataclass
class CycleStats:
    """Statistics for one complete (or partial) cycle"""
    cycle_number: int
    start_tick: int
    end_tick: int
    is_complete: bool

    # Company statistics
    min_companies: int
    max_companies: int
    avg_companies: float

    # Event counts
    ipo_count: int
    bankruptcy_count: int

    # Regime statistics (in periods, not ticks)
    regime_periods: Dict[str, int]  # e.g., {'GROWTH': 120, 'STAGNATION': 180, ...}
    regime_transitions: int

    # Market volatility statistics
    min_vix: float
    median_vix: float
    max_vix: float

    # Interest rate statistics
    min_interest_rate: float
    median_interest_rate: float
    max_interest_rate: float

    # Period returns (if available)
    return_60t: Optional[float] = None
    return_180t: Optional[float] = None
    return_365t: Optional[float] = None


class CycleAnalytics:
    """
    Tracks market behavior over multiple cycles.

    Always exposes current partial cycle data for immediate feedback,
    plus all completed cycles for historical analysis.
    """

    def __init__(self):
        # Completed cycles
        self.completed_cycles: List[CycleStats] = []

        # Current cycle tracking
        self.current_cycle_start_tick = 0
        self.current_cycle_number = 0

        # Accumulators for current cycle
        self.company_counts: List[int] = []
        self.vix_values: List[float] = []
        self.interest_rate_values: List[float] = []
        self.regime_ticks: Dict[Regime, int] = {regime: 0 for regime in Regime}
        self.last_regime: Optional[Regime] = None
        self.regime_transition_count = 0
        self.ipo_count = 0
        self.bankruptcy_count = 0

        # Market cap history for return calculations (track last 366 values)
        self.market_cap_history: deque = deque(maxlen=366)

    def tick_update(
        self,
        tick: int,
        active_company_count: int,
        regime: Regime,
        vix: float,
        interest_rate: float,
        total_market_cap: float
    ):
        """
        Called every tick to accumulate cycle statistics.

        Args:
            tick: Current tick number (global)
            active_company_count: Number of active companies
            regime: Current market regime
            vix: Current VIX value
            interest_rate: Current interest rate
            total_market_cap: Total market capitalization
        """
        # Accumulate data for current cycle
        self.company_counts.append(active_company_count)
        self.vix_values.append(vix)
        self.interest_rate_values.append(interest_rate)
        self.market_cap_history.append(total_market_cap)

        # Track regime time
        self.regime_ticks[regime] += 1

        # Detect regime transitions
        if self.last_regime is not None and self.last_regime != regime:
            self.regime_transition_count += 1
        self.last_regime = regime

        # Check if cycle is complete
        ticks_in_current_cycle = tick - self.current_cycle_start_tick
        if ticks_in_current_cycle >= TICKS_PER_CYCLE and ticks_in_current_cycle % TICKS_PER_CYCLE == 0:
            self._complete_cycle(tick)

    def record_ipo(self):
        """Record an IPO event in the current cycle"""
        self.ipo_count += 1

    def record_bankruptcy(self):
        """Record a bankruptcy event in the current cycle"""
        self.bankruptcy_count += 1

    def _complete_cycle(self, tick: int):
        """
        Complete the current cycle and start a new one.

        Args:
            tick: Current tick number (should be at cycle boundary)
        """
        cycle_stats = self._calculate_cycle_stats(
            cycle_number=self.current_cycle_number,
            start_tick=self.current_cycle_start_tick,
            end_tick=tick,
            is_complete=True
        )

        self.completed_cycles.append(cycle_stats)

        # Reset for next cycle
        self.current_cycle_number += 1
        self.current_cycle_start_tick = tick
        self.company_counts = []
        self.vix_values = []
        self.interest_rate_values = []
        self.regime_ticks = {regime: 0 for regime in Regime}
        self.regime_transition_count = 0
        self.ipo_count = 0
        self.bankruptcy_count = 0
        # Note: market_cap_history persists across cycles for return calculations

    def _calculate_cycle_stats(
        self,
        cycle_number: int,
        start_tick: int,
        end_tick: int,
        is_complete: bool
    ) -> CycleStats:
        """
        Calculate statistics for a cycle (complete or partial).

        Args:
            cycle_number: Cycle number (0-indexed)
            start_tick: Starting tick of cycle
            end_tick: Ending tick of cycle
            is_complete: Whether this is a complete cycle or partial

        Returns:
            CycleStats object with all statistics
        """
        # Company statistics
        min_companies = min(self.company_counts) if self.company_counts else 0
        max_companies = max(self.company_counts) if self.company_counts else 0
        avg_companies = statistics.mean(self.company_counts) if self.company_counts else 0

        # Convert regime ticks to periods (20 ticks = 1 period)
        regime_periods = {
            regime.value: ticks // 20
            for regime, ticks in self.regime_ticks.items()
        }

        # VIX statistics
        min_vix = min(self.vix_values) if self.vix_values else 0
        max_vix = max(self.vix_values) if self.vix_values else 0
        median_vix = statistics.median(self.vix_values) if self.vix_values else 0

        # Interest rate statistics
        min_ir = min(self.interest_rate_values) if self.interest_rate_values else 0
        max_ir = max(self.interest_rate_values) if self.interest_rate_values else 0
        median_ir = statistics.median(self.interest_rate_values) if self.interest_rate_values else 0

        # Calculate period returns if enough data
        return_60t = self._calculate_return(60)
        return_180t = self._calculate_return(180)
        return_365t = self._calculate_return(365)

        return CycleStats(
            cycle_number=cycle_number,
            start_tick=start_tick,
            end_tick=end_tick,
            is_complete=is_complete,
            min_companies=min_companies,
            max_companies=max_companies,
            avg_companies=round(avg_companies, 2),
            ipo_count=self.ipo_count,
            bankruptcy_count=self.bankruptcy_count,
            regime_periods=regime_periods,
            regime_transitions=self.regime_transition_count,
            min_vix=round(min_vix, 2),
            median_vix=round(median_vix, 2),
            max_vix=round(max_vix, 2),
            min_interest_rate=round(min_ir, 4),
            median_interest_rate=round(median_ir, 4),
            max_interest_rate=round(max_ir, 4),
            return_60t=return_60t,
            return_180t=return_180t,
            return_365t=return_365t
        )

    def _calculate_return(self, periods: int) -> Optional[float]:
        """
        Calculate return over specified number of periods.

        Args:
            periods: Number of periods to look back

        Returns:
            Percentage return, or None if insufficient data
        """
        if len(self.market_cap_history) <= periods:
            return None

        current_cap = self.market_cap_history[-1]
        past_cap = self.market_cap_history[-(periods + 1)]

        if past_cap == 0:
            return None

        return round(((current_cap - past_cap) / past_cap) * 100, 2)

    def get_analytics_snapshot(self, current_tick: int) -> dict:
        """
        Get complete analytics data for frontend.

        Returns both completed cycles and current partial cycle data.
        Frontend always sees immediate feedback, even from tick 0.

        Args:
            current_tick: Current global tick number

        Returns:
            dict with 'completed_cycles', 'current_cycle', and 'summary' fields
        """
        # Get current partial cycle stats
        current_partial = None
        if self.company_counts:  # Only include if we have data
            current_partial = self._calculate_cycle_stats(
                cycle_number=self.current_cycle_number,
                start_tick=self.current_cycle_start_tick,
                end_tick=current_tick,
                is_complete=False
            )

        # Calculate summary statistics (across all cycles + current)
        all_cycles = self.completed_cycles + ([current_partial] if current_partial else [])

        total_ipos = sum(c.ipo_count for c in all_cycles)
        total_bankruptcies = sum(c.bankruptcy_count for c in all_cycles)
        avg_companies = (
            statistics.mean([c.avg_companies for c in all_cycles])
            if all_cycles else 0
        )

        # Current cycle progress
        ticks_in_current_cycle = current_tick - self.current_cycle_start_tick
        cycle_progress_pct = round((ticks_in_current_cycle / TICKS_PER_CYCLE) * 100, 1)

        return {
            'completed_cycles': [self._cycle_stats_to_dict(c) for c in self.completed_cycles],
            'current_cycle': self._cycle_stats_to_dict(current_partial) if current_partial else None,
            'summary': {
                'total_completed_cycles': len(self.completed_cycles),
                'total_ipos': total_ipos,
                'total_bankruptcies': total_bankruptcies,
                'avg_companies': round(avg_companies, 2),
                'current_cycle_ticks': ticks_in_current_cycle,
                'current_cycle_progress_pct': cycle_progress_pct
            }
        }

    def _cycle_stats_to_dict(self, stats: CycleStats) -> dict:
        """Convert CycleStats to JSON-serializable dict"""
        return {
            'cycle_number': stats.cycle_number,
            'start_tick': stats.start_tick,
            'end_tick': stats.end_tick,
            'is_complete': stats.is_complete,
            'min_companies': stats.min_companies,
            'max_companies': stats.max_companies,
            'avg_companies': stats.avg_companies,
            'ipo_count': stats.ipo_count,
            'bankruptcy_count': stats.bankruptcy_count,
            'regime_periods': stats.regime_periods,
            'regime_transitions': stats.regime_transitions,
            'min_vix': stats.min_vix,
            'median_vix': stats.median_vix,
            'max_vix': stats.max_vix,
            'min_interest_rate': stats.min_interest_rate,
            'median_interest_rate': stats.median_interest_rate,
            'max_interest_rate': stats.max_interest_rate,
            'return_60t': stats.return_60t,
            'return_180t': stats.return_180t,
            'return_365t': stats.return_365t
        }
