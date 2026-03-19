# Changelog for MTG Metagame Analyzer v1.5

## [v1.5] - 2026-03-19

This release introduces a production-ready metagame input generator pipeline with robust name normalization, configurable Rogue bucketing, historical snapshot generation, and a dedicated Colab workflow for non-technical users.

## Highlights

- New standalone input-generation tool: `src/metagame_input_generator.py`
- New Colab notebook for data generation: `docs/COLAB_INPUT_GENERATOR.ipynb`
- Configurable metagame cutoff for Rogue bucketing via `--rogue-threshold`
- Automatic weekly and history snapshot folder structure by date range
- Improved matchup reliability with 90d -> 180d -> 50% fallback strategy

## Added

- New script: `src/metagame_input_generator.py`
- New Colab notebook: `docs/COLAB_INPUT_GENERATOR.ipynb`
- New CLI option: `--rogue-threshold` (default `0.5`)
- New CLI options for history generation:
  - `--history-points`
  - `--metagame-window-days`
  - `--anchor-sunday`
  - `--history-output-dir`
- Additional output columns:
  - `Winrate Game Count`
  - `My Deck Winrate Game Count`

## Changed

- Metagame input generation now supports two output variants by default:
  - standard
  - Rogue-grouped
- Data outputs are now organized into date-range directories:
  - standard run: `outputs/YYYY-MM-DD_to_YYYY-MM-DD/`
  - history run: `outputs/history/YYYY-MM-DD_to_YYYY-MM-DD/`
- `Reanimator` archetype label is normalized to `Graveyard`
- `Sultai Midrange` is normalized to `Midrange`
- All decks with `Meta < rogue-threshold` are merged into `Deck=Rogue` and aggregated with weighted metrics

## Improved

- Better handling of noisy/fragmented crowd-sourced deck names
- Better consistency of `My Deck Winrate` when multiple aliases map to one canonical deck family
- Better explainability through sample-size columns for winrate values
- Better non-technical onboarding with dedicated Colab path

## Fallback and Reliability Logic

`My Deck Winrate` is now sourced in this order:

1. Primary window (`--my-window-days`, default 90)
2. Fallback window (`--my-fallback-window-days`, default 180)
3. Neutral fallback (`0.50`) when no API matchup exists

Excel visualization:

- Green cell: value sourced from fallback 180-day window
- Yellow cell: neutral `0.50` imputation

## Upgrade Instructions

1. Pull latest changes:

```sh
git pull origin main
```

2. Install dependencies:

```sh
pip install -r requirements.txt
```

3. Generate weekly input set:

```sh
python src/metagame_input_generator.py \
  --format Modern \
  --history-points 1 \
  --metagame-window-days 14 \
  --my-deck "Domain Zoo" \
  --my-window-days 90 \
  --my-fallback-window-days 180 \
  --rogue-threshold 0.5
```

4. For historical rebuilds, increase `--history-points` and optionally set `--anchor-sunday`.

## Notes for Existing Users

- v1.5 does not remove `src/mtg_analyzer.py`.
- The new generator is a separate data-prep tool.
- Recommended workflow:
  1. Generate inputs with `metagame_input_generator.py` (local or Colab)
  2. Analyze generated XLSX/CSV with `mtg_analyzer.py`

## Files Updated in v1.5

- `src/metagame_input_generator.py`
- `docs/COLAB_INPUT_GENERATOR.ipynb`
- `README.md`
- `CHANGELOG_v1.5.md` (this file)

