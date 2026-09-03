# NSE Breakout & Volume Surge Telegram Bot

Scans (almost) every NSE-listed equity (~2000+ stocks) every 30 minutes
during market hours and pings a Telegram chat when it sees:

- 📊 **Volume surge** — current 15-min bar volume vs. the average for that
  same time-of-day slot over recent sessions (default: 12x)
- 🚀 **Breakout** — price closes above its N-day high (default 20 days)
- ⚡ **Sharp move** — a single 15-min bar moves more than a threshold % (default 3%)
- 📐 **Ascending triangle breakout** — flat resistance + rising support, then a close above resistance
- 〰️ **Double bottom breakout** — two similar swing lows with a bounce between them, then a close above the "neckline"
- 📦 **Range breakout** — a tight consolidation range, then a close above it

> **Chart patterns are algorithmic approximations, not true pattern
> recognition.** They use simple, rule-based swing-point detection and will
> have false positives/negatives that a human chartist wouldn't make. Treat
> pattern-breakout alerts as "worth a look," not confirmed setups.

Each run only sends the strongest `TOP_N_PER_RUN` alerts (ranked by volume
multiple / % above breakout / % move) and skips stocks below `MIN_STOCK_PRICE`
or `MIN_AVG_DAILY_VOLUME`, to keep the list manageable and cut out illiquid noise.

Runs for free on GitHub Actions — no server needed.

## ⚠️ Read this first

- **Data source is free/unofficial (yfinance).** It is not real-time-guaranteed,
  can lag, and occasionally rate-limits or blocks bulk requests. This is not
  a substitute for a broker's market-data feed if you're trading on it.
- **Scanning the full NSE universe (~2000+ symbols) every 30 minutes is a
  lot of requests**, and is the most likely reason for slow runs or
  cancellations (see the troubleshooting section below). Fixes, roughly in
  order of effort:
  1. Lower `CHUNK_SIZE` (fewer tickers per call, more calls — gentler bursts)
  2. Increase `COOLDOWN_MINUTES`
  3. Set `UNIVERSE=total_market` (~750) or `UNIVERSE=nifty500` (~500) if you
     want a faster/lighter run instead of the full universe
- **GitHub Actions cron is "best effort."** During busy periods, scheduled
  runs can be delayed by several minutes — don't rely on this for
  time-critical trading decisions.
- This is a signal/alert tool, not investment advice. Verify anything before acting on it.

## Setup

### 1. Create your Telegram bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts.
2. Copy the **bot token** it gives you.
3. Send any message to your new bot (so it can message you back).
4. Get your **chat ID**: message [@userinfobot](https://t.me/userinfobot) and it'll reply with your numeric ID.
   (For a group chat, add the bot to the group and use the group's chat ID instead.)

### 2. Push this project to a GitHub repo
```bash
cd nse-breakout-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 3. Add secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 4. Enable Actions
Go to the **Actions** tab and enable workflows if prompted. The scan runs
automatically every 30 min on weekdays during market hours. You can also
trigger a run manually from the Actions tab (`Run workflow`) to test it.

## Tuning

Everything's tunable via environment variables in `.github/workflows/scan.yml`
(add them under `env:` in the "Run scanner" step) or by editing
`scanner/config.py` directly:

| Variable | Default | Meaning |
|---|---|---|
| `UNIVERSE` | all | `"all"` (every NSE equity, ~2000+), `"total_market"` (~750), or `"nifty500"` (~500) |
| `VOLUME_SURGE_MULTIPLIER` | 12.0 | Alert when volume ≥ this × the same-time average |
| `BREAKOUT_LOOKBACK_DAYS` | 20 | Days used for the high breakout check |
| `PRICE_MOVE_THRESHOLD_PCT` | 3.0 | % move in one 15-min bar to trigger an alert |
| `MIN_STOCK_PRICE` | 20 | Skip stocks priced below this (cuts penny-stock noise) |
| `MIN_AVG_DAILY_VOLUME` | 2500 | Skip stocks whose average daily volume is below this (cuts illiquid stocks) |
| `TOP_N_PER_RUN` | 15 | Max alerts sent per run, keeping the strongest ones |
| `PATTERN_LOOKBACK_BARS` | 120 | Bars scanned back for triangle/double-bottom patterns |
| `PATTERN_PIVOT_WINDOW` | 3 | Bars either side used to confirm a swing high/low |
| `TRIANGLE_RESISTANCE_TOLERANCE_PCT` | 1.0 | How flat the resistance touches must be (%) to count as a triangle |
| `DOUBLE_BOTTOM_TOLERANCE_PCT` | 2.0 | How close the two lows must be (%) to count as a double bottom |
| `RANGE_BREAKOUT_LOOKBACK_BARS` | 40 | Bars used to measure the consolidation range |
| `RANGE_BREAKOUT_MAX_RANGE_PCT` | 6.0 | Max width (%) of that range to still call it "tight" |
| `COOLDOWN_MINUTES` | 60 | Don't re-alert the same stock+signal within this window |
| `CHUNK_SIZE` | 150 | Tickers per yfinance batch request |
| `YF_PERIOD` | 25d | How much history to pull per run (must stay ≥ your longest lookback below) |

## Local testing

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=xxx
export TELEGRAM_CHAT_ID=xxx
python main.py
```

## Troubleshooting: "Canceling since a higher priority waiting request exists"

This means a run took longer than 30 minutes, so the next scheduled trigger
canceled it before it could send anything. If this happens repeatedly, **no
alerts are being sent at all** — it's worth fixing right away, not just a
cosmetic warning. Ways to speed things up, roughly in order of effort:

1. Lower `YF_PERIOD` further (e.g. `"15d"`) if 25 days is still too slow —
   just keep it above `BREAKOUT_LOOKBACK_DAYS`.
2. Lower `CHUNK_SIZE` for gentler, possibly faster batches.
3. Set `UNIVERSE=total_market` (~750) or `UNIVERSE=nifty500` (~500) as a
   faster middle ground if the full universe consistently won't fit.
4. As a last resort, widen the cron schedule further (e.g. every 60 min).

Check the Actions log's "Run scanner" step timing to see how close you are
to the 20-minute job timeout before and after any change.

## Troubleshooting: scheduled runs missing entirely (works fine on manual "Run workflow")

This is a known GitHub Actions limitation, not a bug in this project.
GitHub's own docs state that scheduled ("cron") triggers are **best
effort**: they can be delayed during high load, and if load is high
enough, **queued runs can be dropped entirely** — with no error anywhere,
since nothing ran at all. The start of every hour and half-hour is
specifically called out as peak load, which is exactly when a `0,30`
cron competes with the largest number of other repos' scheduled jobs.
This cron is set to `7,37` instead for that reason.

If missed runs are still frequent enough to matter, the only fully
reliable fix (per GitHub's own community threads) is to stop relying on
GitHub's schedule queue at all: use a free external scheduler (e.g.
cron-job.org, a cloud scheduler, or your own machine's cron) to call the
[`workflow_dispatch` REST API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)
at the exact time you want — `workflow_dispatch` is dispatched near-instantly
and doesn't sit in the same delay-prone queue as `schedule`. This needs a
GitHub Personal Access Token with `actions: write` permission. Happy to
help set this up if the offset-cron fix above isn't enough on its own.

## Project structure

```
main.py                  # entry point, market-hours check, orchestration
scanner/
  config.py               # thresholds & settings
  symbols.py              # fetches full NSE symbol list
  data.py                 # batched yfinance downloads
  signals.py              # breakout/volume/move detection logic
  patterns.py             # chart pattern detection (triangle, double bottom, range)
  state.py                # cooldown/dedup persisted to state.json
  notifier.py             # Telegram sending
.github/workflows/scan.yml # the cron schedule
state.json                # committed automatically to remember past alerts
```
