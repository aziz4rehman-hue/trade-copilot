"""Close-only paper engine. Signal uses history so far. Fill is the next close."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field


@dataclass
class Spec:
    name: str
    fast: int = 10
    slow: int = 30
    period: int = 14
    low: float = 30
    high: float = 70


@dataclass
class Result:
    equity: list[float]
    closed: list[float] = field(default_factory=list)
    start: float = 0.0

    @property
    def end(self) -> float:
        return self.equity[-1]

    def metrics(self) -> dict:
        total_return = (self.end / self.start - 1) if self.start else 0.0
        wins = [pnl for pnl in self.closed if pnl > 0]
        losses = [pnl for pnl in self.closed if pnl < 0]
        win_rate = (len(wins) / len(self.closed)) if self.closed else None
        gross_loss = -sum(losses)
        profit_factor = None if not self.closed else (float("inf") if gross_loss == 0 else sum(wins) / gross_loss)
        return {
            "total_return": total_return,
            "max_drawdown": _max_drawdown(self.equity),
            "trades": len(self.closed),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
        }


def parse_request(text: str) -> Spec:
    raw = " ".join(text.strip().split())
    low = raw.lower()
    if not raw:
        raise ValueError("say what to test, for example: sma crossover fast 10 slow 30")
    if re.search(r"\bbuy[- ]and[- ]hold\b", low) or re.search(r"\bbuyhold\b", low):
        return Spec("buyhold")
    if re.search(r"\brsi\b", low):
        nums = [float(item) for item in re.findall(r"\d+(?:\.\d+)?", low)]
        period = int(nums[0]) if nums else 14
        buy = nums[1] if len(nums) > 1 else 30
        sell = nums[2] if len(nums) > 2 else 70
        if period < 2:
            raise ValueError("rsi period must be at least 2")
        if not 0 <= buy < sell <= 100:
            raise ValueError("rsi levels must satisfy 0 <= buy < sell <= 100")
        return Spec("rsi", period=period, low=buy, high=sell)
    if re.search(r"\bsma\b", low) or "crossover" in low or "moving average" in low:
        nums = [int(item) for item in re.findall(r"\d+", low)]
        fast = nums[0] if len(nums) > 0 else 10
        slow = nums[1] if len(nums) > 1 else 30
        if fast > slow:
            fast, slow = slow, fast
        fast = max(2, fast)
        slow = max(fast + 1, slow)
        return Spec("sma", fast=fast, slow=slow)
    raise ValueError("could not read that. Try buy and hold, sma crossover fast 10 slow 30, or rsi 14 30 70")


def synthetic_closes(n: int = 120, seed: int = 3, start: float = 100.0) -> list[float]:
    if n < 3:
        raise ValueError("need at least 3 closes")
    rng = random.Random(seed)
    price = start
    closes = []
    for i in range(n):
        drift = 0.003 if (i // 30) % 2 == 0 else -0.003
        price = max(1.0, price * (1 + drift + rng.gauss(0, 0.005)))
        closes.append(round(price, 4))
    return closes


def desired_long(spec: Spec, history: list[float], in_position: bool) -> bool:
    if spec.name == "buyhold":
        return True
    if spec.name == "sma":
        if len(history) < spec.slow:
            return False
        fast = sum(history[-spec.fast :]) / spec.fast
        slow = sum(history[-spec.slow :]) / spec.slow
        return fast > slow
    if spec.name == "rsi":
        value = _rsi(history, spec.period)
        if value is None:
            return in_position
        if not in_position and value < spec.low:
            return True
        if in_position and value > spec.high:
            return False
        return in_position
    raise ValueError(f"unknown strategy {spec.name}")


def run_backtest(closes: list[float], spec: Spec, cash: float = 10_000.0) -> Result:
    if len(closes) < 2:
        raise ValueError("need at least 2 closes")
    if cash <= 0:
        raise ValueError("cash must be positive")
    cash_left = float(cash)
    qty = 0.0
    avg = 0.0
    pending: bool | None = None
    equity: list[float] = []
    closed: list[float] = []
    for i, price in enumerate(closes):
        if pending is not None:
            in_position = qty > 0
            if pending and not in_position:
                qty = cash_left / price
                avg = price
                cash_left = 0.0
            elif not pending and in_position:
                pnl = (price - avg) * qty
                cash_left += qty * price
                closed.append(pnl)
                qty = 0.0
                avg = 0.0
            pending = None
        equity.append(cash_left + qty * price)
        if i < len(closes) - 1:
            want = desired_long(spec, closes[: i + 1], qty > 0)
            if want != (qty > 0):
                pending = want
    return Result(equity=equity, closed=closed, start=cash)


def narrate(spec: Spec, result: Result) -> str:
    stats = result.metrics()
    if spec.name == "sma":
        label = f"sma crossover {spec.fast}/{spec.slow}"
    elif spec.name == "rsi":
        label = f"rsi {spec.period} buy below {spec.low:g} sell above {spec.high:g}"
    else:
        label = "buy and hold"
    win = "n/a" if stats["win_rate"] is None else f"{stats['win_rate'] * 100:.1f}%"
    factor = stats["profit_factor"]
    if factor is None:
        factor_text = "n/a"
    elif factor == float("inf"):
        factor_text = "inf"
    else:
        factor_text = f"{factor:.2f}"
    return "\n".join(
        [
            f"strategy    {label}",
            f"bars        {len(result.equity)} synthetic closes",
            f"equity      {result.start:.2f} -> {result.end:.2f}",
            f"return      {stats['total_return'] * 100:+.2f}%",
            f"max DD      {stats['max_drawdown'] * 100:+.2f}%",
            f"trades      {stats['trades']}",
            f"win rate    {win}",
            f"profit fac  {factor_text}",
            "fill rule   signal on this close, fill on the next close",
            "not financial advice · paper research only · no live order",
        ]
    )


def _rsi(closes: list[float], period: int) -> float | None:
    if len(closes) < period + 1:
        return None
    window = closes[-(period + 1) :]
    gains = 0.0
    losses = 0.0
    for prev, cur in zip(window, window[1:]):
        diff = cur - prev
        if diff >= 0:
            gains += diff
        else:
            losses -= diff
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = (gains / period) / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, (value - peak) / peak)
    return worst
