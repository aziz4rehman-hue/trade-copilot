import unittest

from tradecopilot.cli import main
from tradecopilot.engine import parse_request, run_backtest


class CopilotTests(unittest.TestCase):
    def test_parse_swaps_fast_and_slow(self):
        spec = parse_request("sma crossover fast 30 slow 10")
        self.assertEqual(spec.name, "sma")
        self.assertEqual((spec.fast, spec.slow), (10, 30))

    def test_parse_rsi_and_buyhold(self):
        rsi = parse_request("rsi 14 buy below 30 sell above 70")
        self.assertEqual((rsi.period, rsi.low, rsi.high), (14, 30, 70))
        self.assertEqual(parse_request("buy and hold").name, "buyhold")
        with self.assertRaises(ValueError):
            parse_request("threshold something else")

    def test_buyhold_fills_next_close(self):
        result = run_backtest([100, 100, 110], parse_request("buyhold"), cash=1000)
        self.assertAlmostEqual(result.end, 1100)
        self.assertEqual(result.metrics()["trades"], 0)
        self.assertAlmostEqual(result.metrics()["total_return"], 0.10)

    def test_sma_run_is_finite(self):
        result = run_backtest(
            [100 + i * 0.4 for i in range(40)] + [116 - i * 0.5 for i in range(40)],
            parse_request("moving average 5 and 15"),
            cash=10_000,
        )
        stats = result.metrics()
        self.assertGreaterEqual(stats["trades"], 1)
        self.assertLessEqual(stats["max_drawdown"], 0)
        self.assertEqual(stats["total_return"], stats["total_return"])

    def test_cli_rejects_noise(self):
        self.assertEqual(main(["please", "make", "money"]), 2)


if __name__ == "__main__":
    unittest.main()
