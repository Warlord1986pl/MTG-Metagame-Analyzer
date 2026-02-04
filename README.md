# MTG Metagame Analyzer

A comprehensive Python tool for analyzing Magic: The Gathering metagame data, generating probability charts, and tracking meta trends over time.

## Features

- **Encounter Probability Analysis**: Calculate the probability of facing specific decks in tournaments
- **Meta Trend Tracking**: Monitor how deck metagame percentages change over weeks
- **Archetype Aggregation**: Group decks by archetype for broader analysis
- **Performance Metrics**: Identify underplayed winners and popular traps
- **Prep Priority Scoring**: Automatically rank decks by preparation importance
- **Interactive Visualizations**: Generate publication-ready charts with matplotlib
- **Historical Data Management**: Track metagame evolution with optional CSV history files

## Quick Start

### Option 1: Google Colab (Recommended for non-technical users)

1. Open [Google Colab](https://colab.research.google.com)
2. Copy the entire content from `src/mtg_analyzer.py`
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
4. **encounter_prob_Deck_W{N}.png** - Bar chart of encounter probabilities
5. **encounter_prob_Archetype_W{N}.png** - Archetype encounter chart
6. **meta_trend_Deck_W{N}_last{X}w.png** - Trend chart (if history available)

All files are packaged in `MTG_Analysis_W{N}.zip`

## Calculations Explained

### Encounter Probability
Uses hypergeometric distribution to calculate the probability of facing a specific deck in a {N}-player tournament:

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
- **Rising** (^): Meta share increased by >0.5%
- **Falling** (v): Meta share decreased by >0.5%
- **Stable** (-): Meta share within ±0.5%

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

## Troubleshooting

**Issue**: "Excel file not found"
- Ensure file is in the correct location
- Check file naming and extension

**Issue**: "Column 'Deck' not found"
- Verify your Excel file has required columns: `Deck`, `Meta`, `Winrate`
- Check column names match exactly (case-sensitive)

**Issue**: Trend chart not generated
- Requires at least 2 weeks of history
- Ensure CSV file has `WeekIndex` column
- Check that deck names match between current and historical data

**Issue**: Empty squares in legend
- Fixed in v1.1+ - update your script
- Deck symbols (□■▪•) are automatically cleaned in display names

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests

## License

MIT License - see [LICENSE](LICENSE) file for details

## Changelog

### Version 1.1
- Fixed legend marker display (empty squares issue)
- Reversed colormap ordering for better visual hierarchy
- Added ASCII trend symbols (^ v -) for better compatibility
- Improved deck name cleaning (removes special symbols)

### Version 1.0
- Initial release
- Core analysis features
- Google Colab integration

## Support

For questions or issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review `examples/` for sample data
3. Open an issue on GitHub

## Author

Created for competitive Magic: The Gathering players and meta analysts.

---

**Last Updated**: February 4, 2026  
**Latest Version**: 1.1
