# trade-copilot

Type a strategy in a sentence. Get a paper backtest back.

It understands three requests: buy and hold, an SMA crossover, and RSI. The series is synthetic. A losing result is a valid result. On the demo tape, the SMA crossover loses money.

**[See the live demo](https://aziz4rehman-hue.github.io/trade-copilot/)**

**Not financial advice. This does not place an order.**

```bash
git clone https://github.com/aziz4rehman-hue/trade-copilot.git
cd trade-copilot
python -m tradecopilot --demo
```

```
strategy    sma crossover 10/30
bars        120 synthetic closes
equity      10000.00 -> 9400.25
return      -6.00%
max DD      -6.00%
trades      2
win rate    0.0%
profit fac  0.00
fill rule   signal on this close, fill on the next close
not financial advice · paper research only · no live order
```

## Ask for something else

```bash
python -m tradecopilot buy and hold
python -m tradecopilot sma crossover fast 30 slow 10
python -m tradecopilot "rsi 14 buy below 30 sell above 70"
```

`fast 30 slow 10` is swapped so the fast window is the shorter one. If the sentence is not one of those three strategies, the command exits with an error instead of guessing.

The fill rule is the whole point: the signal can only see closes up to now, and the trade happens on the **next** close.

From Python:

```python
from tradecopilot.engine import parse_request, run_backtest, synthetic_closes, narrate

spec = parse_request("sma crossover fast 10 slow 30")
print(narrate(spec, run_backtest(synthetic_closes(), spec)))
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Python 3.10+. No third-party packages.

## License

MIT. Built by [Aziz Rehman](https://github.com/aziz4rehman-hue).
