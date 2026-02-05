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
2. Copy the entire content from `docs/SCRIPT_FULL.txt` (or `src/mtg_analyzer.py`)
3. Paste it into a new Colab notebook
4. Click **Runtime** → **Run all** (or press Ctrl+F9)
5. Upload your Excel file when prompted
6. Download results as ZIP

### Option 2: Local Installation

**Requirements:**
- Python 3.8+
- See `requirements.txt` for dependencies

**Installation:**
```bash
git clone https://github.com/yourusername/MTG-Metagame-Analyzer.git
cd MTG-Metagame-Analyzer
pip install -r requirements.txt
```

**Running the script:**
```bash
python src/mtg_analyzer.py
```

## Input Data Format

### Excel File (Required)
Your Excel file must contain these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `Deck` | Deck name (can include symbols □■▪•) | "Boros Energy □" |
| `Meta` | Metagame percentage | 5.2 |
| `Winrate` | Win rate as decimal | 0.52 |
| `Archetype` | (Optional) Deck archetype | "Aggro" |
| `My Winrate` | (Optional) Your personal win rate | 0.58 |

### CSV History File (Optional)
For trend analysis, provide a CSV with historical data. Same columns as above plus:
- `WeekIndex`: Week number (auto-calculated if not provided)

## Output Files

The script generates:

1. **deck_analysis_W{N}.xlsx** - Detailed deck metrics for week N
2. **deck_analysis_ARCHETYPE_W{N}.xlsx** - Archetype-level aggregation
3. **Metagame_History_W{N}.csv** - Updated history file (use as input next week)
4. **encounter_prob_Deck_W{N}.png** - Bar chart of encounter probabilities (by deck)
5. **encounter_prob_Archetype_W{N}.png** - Bar chart of encounter probabilities (by archetype)
6. **meta_trend_Deck_W{N}_last{X}w.png** - Trend line chart for top 10 decks (if history available)
7. **meta_trend_Archetype_W{N}_last{X}w.png** - Trend line chart for archetypes (if history available)

All files are packaged in `MTG_Analysis_W{N}.zip`

## Calculations Explained

### Encounter Probability
Uses hypergeometric distribution to calculate the probability of facing a specific deck in an N-player tournament:

- **N**: Total estimated tournament players
- **K**: Number of players piloting the deck
- **Sample**: Your 5 opponents
- Formula: P(encounter ≥ 1 out of 5 opponents)

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

**Issue**: Trend charts not generated or show only single points
- Requires at least 2 weeks of history
- Ensure CSV file has `WeekIndex` column
- Check that deck names match between current and historical data
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
