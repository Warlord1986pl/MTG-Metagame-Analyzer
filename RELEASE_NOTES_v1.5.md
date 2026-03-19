# MTG Metagame Analyzer v1.5 - Release Notes

**Release Date:** 2026-03-19

## Summary

Version 1.5 adds a complete data-generation pipeline for metagame analysis inputs.

This release separates data preparation from analysis so users can:

1. fetch data consistently from the same source,
2. normalize and aggregate it with reproducible rules,
3. export ready-to-analyze files for local scripts and Colab workflows.

## Major Additions

- New generator script: `src/build_metagame_input.py`
- New Colab notebook for data generation: `docs/COLAB_INPUT_GENERATOR.ipynb`
- New configurable Rogue cutoff parameter: `--rogue-threshold`
- New date-range folder organization for weekly and historical runs
- New game-sample columns:
  - `Winrate Game Count`
  - `My Deck Winrate Game Count`

## Why This Matters

v1.5 reduces manual data work and makes weekly updates predictable.

- Better consistency: same normalization logic every run
- Better transparency: game-count columns show sample sizes
- Better realism: low-meta tail can be merged into Rogue using configurable threshold
- Better reliability: matchup fallback strategy avoids empty critical fields

## New Data Generation Behavior

### 1) Configurable Rogue Threshold

Use:

```sh
--rogue-threshold 0.5
```

All decks with `Meta < rogue-threshold` are merged into `Deck=Rogue` and aggregated with weighted metrics.

### 2) Matchup Reliability Cascade

`My Deck Winrate` is sourced in this order:

1. primary window (`--my-window-days`, default 90)
2. fallback window (`--my-fallback-window-days`, default 180)
3. neutral `0.50` fallback if data is still missing

### 3) Date-Range Output Layout

- Weekly run:
  - `outputs/YYYY-MM-DD_to_YYYY-MM-DD/`
- History run:
  - `outputs/history/YYYY-MM-DD_to_YYYY-MM-DD/`

This makes archiving and week-to-week comparisons easier.

## New/Updated Documentation

- `CHANGELOG_v1.5.md`
- `docs/DATA_GENERATOR_GUIDE.md`
- `docs/COLAB_INPUT_GENERATOR.ipynb`
- `README.md` (v1.5 links and workflow clarifications)

## Upgrade Instructions

1. Pull latest changes:

```sh
git pull origin main
```

2. Install dependencies:

```sh
pip install -r requirements.txt
```

3. Run weekly generation:

```sh
python src/build_metagame_input.py \
  --format Modern \
  --history-points 1 \
  --metagame-window-days 14 \
  --my-deck "Domain Zoo" \
  --my-window-days 90 \
  --my-fallback-window-days 180 \
  --rogue-threshold 0.5
```

4. Run analysis using generated XLSX/CSV in your existing analyzer workflow.

## Backward Compatibility

- Existing analysis script `src/mtg_analyzer.py` remains available.
- v1.5 adds data-prep capabilities; it does not remove previous analysis features.

## Recommended v1.5 Workflow

1. Generate inputs with `build_metagame_input.py` (local or Colab).
2. Validate XLSX output quickly (including color-coded fallback indicators).
3. Run full metagame analysis with `mtg_analyzer.py`.
4. Archive weekly date-range folder into your long-term history.
