# MTG Metagame Analyzer

A comprehensive Python tool for analyzing Magic: The Gathering metagame data, generating probability charts, and tracking meta trends over time.

## Features

- **Encounter Probability Analysis**: Calculate the probability of facing specific decks in tournaments
- **Encounter Threshold Filter**: Hide low-probability decks for cleaner encounter charts
- **Meta Trend Tracking**: Monitor how deck and archetype metagame percentages change over weeks
- **Archetype Aggregation**: Group decks by archetype for broader analysis
- **Performance Metrics**: Identify underplayed winners and popular traps
- **Prep Priority Scoring**: Automatically rank decks by preparation importance
- **Interactive Visualizations**: Generate publication-ready charts with matplotlib
- **Historical Data Management**: Track metagame evolution with optional CSV history files
- **Dual-Level Analysis**: Separate trend tracking for both decks AND archetypes

## Quick Start

### Option 1: Google Colab (Recommended for non-technical users)

1. Open [Google Colab](https://colab.research.google.com)
2. Upload and run [docs/COLAB_INPUT_GENERATOR.ipynb](docs/COLAB_INPUT_GENERATOR.ipynb)
3. Set parameters in the notebook (format, history points, windows, deck)
4. Run all cells to generate ready input files in `outputs/`
5. Download generated ZIP from Colab

This notebook is focused on data generation (metagame input + history files).
For full chart/report analysis, use `src/mtg_analyzer.py` with the generated XLSX.

### Option 2: Local Installation


# MTG Metagame Analyzer v1.4

Analyze Magic: The Gathering (MTG) metagame data to understand trends, deck performance, matchup probabilities, and more. This tool generates insightful charts and Excel outputs from your metagame data, supporting both competitive players and deckbuilders.

---

## What's New in v1.4

- **Renamed Input Column:** "My Winrate" → **"My Deck Winrate"**
- **New Chart:** My Deck Performance (encounter probability colored by your winrate)
- **New Chart:** Record Probability Distribution (binomial model for 5-0, 4-1, etc.)
- **New Excel Output:** Record probabilities per deck
- **Improved Input Normalization:** Accepts both decimal and percent formats for winrates and meta
- **Backward Compatibility:** Accepts old "My Winrate" column (auto-renamed)

---

## Input File Format

Provide an Excel file (.xlsx) with the following columns:

| Column             | Required | Description                                                      |
|--------------------|----------|------------------------------------------------------------------|
| Deck               | Yes      | Name of the deck                                                 |
| Meta               | Yes      | Meta share (%) (can be decimal or percent, e.g. 12.5 or 12.5%)   |
| Winrate            | Yes      | Deck winrate (decimal or %, e.g. 0.58 or 58%)                    |
| Archetype          | No       | Archetype name (optional)                                        |
| My Deck Winrate    | No       | Your winrate vs this deck (decimal or %, e.g. 0.62 or 62%)       |

**Note:** "My Deck Winrate" is your personal winrate against each deck. If not provided, related charts are skipped.

---

## Usage

1. Run the script:

   ```sh
   python src/mtg_analyzer.py
   ```

2. Enter the path to your Excel file when prompted.
3. (Optional) Enter a CSV history file for trend analysis.
4. Follow prompts for player count, rounds, and other settings.
5. Review generated charts and Excel outputs in the working directory.

### Weekly auto-import + Domain Zoo `My Deck Winrate`

Jeśli chcesz mieć szybkie, powtarzalne źródło danych bez ręcznego przepisywania:

```sh
python src/build_metagame_input.py \
  --format Modern \
  --week-start 2026-03-09 \
  --week-end 2026-03-15 \
  --my-deck "Domain Zoo" \
  --my-window-days 90 \
  --rogue-threshold 0.5
```

Skrypt:

- pobiera tygodniowy metagame (`Deck`, `Meta`, `Winrate`),
- pobiera matchupy dla Twojego decku (domyślnie `Domain Zoo`) z okna 30/90 dni,
- wpisuje je jako `My Deck Winrate`,
- mapuje `Archetype` automatycznie (reguły + heurystyka),
- wrzuca decki z `Meta < rogue-threshold` do wspólnego koszyka `Rogue`,
- eksportuje gotowe pliki:
  - `outputs/metagame_input.xlsx`
  - `outputs/metagame_input.csv`
  - `outputs/unknown_archetypes.csv`

Reguły mapowania archetypów są w `docs/archetype_rules.csv`.
Uzupełniaj tylko rekordy z `outputs/unknown_archetypes.csv`, a z czasem ręczna praca spadnie praktycznie do zera.

Nazwy decków normalizujesz osobno w `docs/deck_aliases.csv` (np. `Sultai Midrange` -> `Sultai Ritual`).
Aliasowanie dzieje się przed przypisaniem archetypu i przed mapowaniem `My Deck Winrate`, więc statystyki będą spójne między tygodniami.

Najprostszy workflow: edytuj tylko `docs/user_deck_mapping.csv`.
To jest Twój plik nadpisujący, gdzie możesz ręcznie ustawić:
- `raw_name` (nazwa z API),
- `canonical_name` (jak ma się nazywać u Ciebie),
- `archetype` (np. Blink, Eldrazi, Combo).

Jeśli wpis istnieje w `docs/user_deck_mapping.csv`, ma priorytet nad aliasami i auto-regułami.

---

## Outputs

- **Encounter Probability Charts:** For decks and archetypes
- **My Deck Performance Chart:** Shows your toughest matchups (NEW in v1.4)
- **Record Probability Chart:** Binomial model for your and all decks' records (NEW in v1.4)
- **Record Probability Excel:** Table of record probabilities for all decks (NEW in v1.4)
- **Excel Summary Tables:** Deck and archetype analysis
- **Metagame History CSV:** Tracks meta and trends over time
- **ZIP Archive:** All outputs packaged for easy sharing

---

## Requirements

- Python 3.8+
- pandas
- matplotlib
- numpy
- openpyxl
- mplcursors

Install dependencies:

```sh
pip install -r requirements.txt
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

This project is licensed under the MIT License.
- **Sample**: Number of rounds/opponents you expect to face (default 5)
- Formula: $P(\text{encounter} \ge 1 \text{ out of sample})$

### Importance Score
Weighted metric combining metagame and performance:
- **70%** metagame share (prevalence)
- **30%** win rate range (performance)

### Prep Priority Quartiles
- **Q4 (Very High)**: Top 25% importance - must prepare
- **Q3 (High)**: Next 25% - strongly recommended
- **Q2 (Medium)**: Middle 50% - optional prep
- **Q1 (Low)**: Bottom 25% - minimal focus

### Performance Labels
- **Underplayed Winner**: Low meta % + High win rate = You should play this!
- **Popular Trap**: High meta % + Low win rate = Avoid overplaying this
- **Neutral**: All other combinations

### Trend Status
Calculated over last N weeks:
- **Rising** (^): Meta share increased by >0.5% (decks) or >0.2% (archetypes)
- **Falling** (v): Meta share decreased by >0.5% (decks) or >0.2% (archetypes)
- **Stable** (-): Change within the thresholds above

## Examples

See the `examples/` folder for:
- Sample Excel input files
- Expected output formats
- Week-by-week comparison data

## Configuration

### Player Count
Default: 1,000 players (typical large tournament). Adjust based on your specific format:
- **SCG 10k events**: 10,000+ players
- **Regional PTQs**: 100-500 players
- **Local events**: 20-100 players

Lower counts = higher encounter probabilities

### Rounds/Opponents
Default: 5 (typical MTGO league). Change this to match your event length.
Only affects encounter probability calculations; meta share and trends always use `Meta`.

### Minimum Encounter Probability
Default: 5% (filters encounter probability charts for readability)
- Enter a lower value (e.g., 2) to show more decks
- Enter a higher value (e.g., 8) to focus on the most likely matchups

## History Management

**First run (no history):**
1. Upload only Excel file
2. Script outputs `Metagame_History_W1.csv`
3. Charts generated: 2 encounter probability charts only

**Subsequent runs (with history):**
1. Upload current Excel file
2. Upload previous `Metagame_History_W{N}.csv`
3. Script will prompt: "How many weeks back for trend chart? (default 4)"
4. Outputs: 4 charts (2 encounter probability + 2 trend charts for decks & archetypes)

## Troubleshooting

**Issue**: "Excel file not found"
- Ensure file is in the correct location
- Check file naming and extension

**Issue**: "Column 'Deck' not found"
- Verify your Excel file has required columns: `Deck`, `Meta`, `Winrate`
- Check column names match exactly (case-sensitive)

**Issue**: "Meta/Winrate conversion: X rows became NaN"
- Some values in `Meta` or `Winrate` are not recognized as numbers
- Use supported formats (see Input Data Format) and avoid extra text

**Issue**: Trend charts not generated or show only single points
- Requires at least 2 weeks of history
- Ensure CSV file has `WeekIndex` column
- Check that deck names match between current and historical data
- Rounds/opponents only affect encounter probability, not trend/meta calculations
- **v1.3 FIX**: Tab characters in Excel deck names now auto-cleaned
- If upgrading from pre-v1.3, re-generate history CSV to clean old deck names

**Issue**: Empty squares in legend
- Fixed in v1.1+ - update your script
- Deck symbols (□■▪•) are automatically cleaned in display names

**Issue**: Archetype trend chart missing
- Ensure Excel file includes `Archetype` column
- If no `Archetype` column, all decks assigned to "Rogue"
- Chart still generates but with single "Rogue" archetype

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests

## Version History

### v1.3 (Current - February 2026)
- **FIXED**: Deck trend chart now displays multi-week trend lines correctly
- **FIXED**: Filter order bug that excluded historical data for decks with changing rankings
- **FIXED**: Tab character handling in Excel deck names (auto-cleanup with `.str.strip()`)
- **IMPROVED**: Week range filtering now happens BEFORE deck selection filtering
- **IMPROVED**: Archetype-level records properly excluded from deck trend calculations
- **NEW**: Minimum encounter probability filter (default 5%) for cleaner charts
- **IMPROVED**: Separate trend thresholds (decks: 0.5%, archetypes: 0.2%)
- Trend charts now show complete 4-week history for all top 10 decks
- Enhanced backward compatibility for data without `Level` column

#### Patch Updates (February 5, 2026)
- Added a minimum encounter probability filter (default 5%) for encounter charts
- Separated trend thresholds for decks (0.5%) vs archetypes (0.2%)
- Archetype trend status now strictly uses archetype-level history rows

### v1.2
- **NEW**: Archetype trend chart (4th visualization)
- **NEW**: Archetype history tracking in CSV
- **IMPROVED**: Better separation of deck vs archetype analysis
- Added `Level` column to history CSV to distinguish deck/archetype entries

### v1.1
- Fixed legend marker inconsistencies (empty squares)
- Fixed colormap reversal in trend charts
- Improved chart layout and legend positioning

### v1.0
- Initial release
- Encounter probability analysis
- Deck trend tracking
- Basic archetype aggregation

## License

MIT License - see LICENSE file for details

---

**For detailed technical documentation**, see [DESCRIPTION.txt](docs/DESCRIPTION.txt)
