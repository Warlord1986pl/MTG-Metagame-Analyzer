# MTG Data Generator Guide (Python + Colab)

This guide explains the new v1.5 data-generation workflow in plain language.

The goal is simple:

1. Collect metagame data from API
2. Normalize deck names/archetypes
3. Generate clean input files for analysis

This tool does not replace `src/mtg_analyzer.py`. It prepares better input for it.

## What This Tool Does

Script: `src/metagame_input_generator.py`

It creates files with:

- `Deck`
- `Meta`
- `Winrate`
- `Archetype`
- `My Deck Winrate`
- sample-size columns for both winrates

It also:

- groups very low-meta decks into `Rogue`
- applies name and archetype normalization rules
- creates standard and Rogue-grouped output variants
- creates clean date-range folders for every run

## Recommended Workflow

1. Run generator (local or Colab)
2. Review XLSX output (colors + sanity check)
3. Run your analysis script (`src/mtg_analyzer.py`)

## Option A: Local Python (Step by Step)

### 1. Open terminal in repository root

```sh
cd MTG-Metagame-Analyzer
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Run a standard weekly snapshot

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

### 4. Check outputs

Files are created in:

- `outputs/YYYY-MM-DD_to_YYYY-MM-DD/`

Main files:

- `metagame_input.xlsx`
- `metagame_input.csv`
- `metagame_input_rogue_grouped.xlsx`
- `metagame_input_rogue_grouped.csv`
- `unknown_archetypes.csv`
- `alias_suggestions.csv`

## Option B: Google Colab (Step by Step)

### 1. Open Colab

- https://colab.research.google.com

### 2. Upload and run notebook

- `docs/COLAB_INPUT_GENERATOR.ipynb`

### 3. Set parameters in the notebook

You can configure:

- format
- history points
- metagame window
- my deck
- 90d and 180d matchup windows
- Rogue threshold

### 4. Run all cells

The notebook will:

- clone repository
- install requirements
- run generator
- package outputs into ZIP
- download ZIP to your computer

## Key Parameters Explained

- `--format`: game format, e.g. `Modern`
- `--history-points`: number of weekly snapshots to generate
- `--metagame-window-days`: size of metagame window, usually `14`
- `--anchor-sunday`: optional fixed reference Sunday (`YYYY-MM-DD`)
- `--my-deck`: your deck name for matchup extraction
- `--my-window-days`: primary matchup window (default `90`)
- `--my-fallback-window-days`: fallback matchup window (default `180`)
- `--rogue-threshold`: decks with `Meta < threshold` are merged into `Rogue`

## How Winrates Are Computed

### Deck Winrate (`Winrate`)

- sourced from metagame endpoint
- aggregated using weighted averages by `Meta`

### My Deck Winrate (`My Deck Winrate`)

- sourced from matchups of your selected deck
- if missing in primary window, tries fallback window
- if still missing, uses neutral `0.50`

Excel colors:

- Green: fallback (180-day) value
- Yellow: neutral `0.50` value

## Name and Archetype Rules

The tool applies normalization and mapping from:

- `docs/deck_aliases.csv`
- `docs/user_deck_mapping.csv`
- `docs/archetype_rules.csv`

Special defaults in v1.5:

- `Reanimator` -> `Graveyard`
- `Sultai Midrange` -> `Midrange`
- low-meta decks (`Meta < rogue-threshold`) -> `Rogue`

## Typical Scenarios

### Weekly routine

Use:

- `--history-points 1`
- `--metagame-window-days 14`

### Backfill 4 historical points

Use:

- `--history-points 4`
- optional `--anchor-sunday YYYY-MM-DD`

Outputs go to:

- `outputs/history/YYYY-MM-DD_to_YYYY-MM-DD/`

## Troubleshooting

### I see many Unknown archetypes

- review `unknown_archetypes.csv`
- add mappings to `docs/user_deck_mapping.csv`
- rerun generator

### My deck matchup is empty for some decks

- this can mean no API samples
- script will use 180d fallback, then 0.50 if still missing

### I want fewer decks merged into Rogue

- lower `--rogue-threshold`, e.g. `0.3`

### I want more decks merged into Rogue

- raise `--rogue-threshold`, e.g. `0.7`

## Best Practices

1. Keep `user_deck_mapping.csv` maintained weekly
2. Use the same weekday anchor for historical consistency
3. Keep both outputs:
   - standard
   - Rogue-grouped
4. Always inspect sample-size columns before strategic conclusions

