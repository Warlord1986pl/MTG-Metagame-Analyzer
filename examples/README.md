# Examples - MTG Metagame Analyzer v1.3

This folder contains example input data and sample output files to help you understand the tool's functionality.

## Files

### Input Data

- **`Example_Metagame_Data.xlsx.xlsx`** - Example input file with MTG deck metagame data for Week 11
  - Required columns: `Deck`, `Meta`, `Winrate`
  - Optional columns: `Archetype`, `My Winrate`
  - Format: Each row represents one deck/strategy in the current metagame

- **`Example_Metagame_History_W1-W10.csv`** - Historical metagame data from weeks 1-10
  - Used to calculate trends and identify rising/falling strategies
  - Demonstrates realistic meta evolution over 10 weeks
  - Includes both deck-level AND archetype-level records (`Level` column)

### Output Visualizations (PNG)

#### Week 11 Charts (Generated from Example Data)
- **`encounter_prob_Deck_W11.png`** - Bar chart showing encounter probability for individual decks
- **`encounter_prob_Archetype_W11.png`** - Bar chart for archetypes (aggregated data)
- **`meta_trend_Deck_W11_last4w.png`** - Line chart showing deck metagame trends over weeks 8-11
- **`meta_trend_Archetype_W11_last4w.png`** - Line chart showing archetype trends over weeks 8-11

### Output Files (in `outputs/` folder)

#### Data Files (Excel)
- **`deck_analysis_W11.xlsx`** - Detailed analysis per deck including:
  - Meta percentage
  - Win rate
  - Encounter probability
  - Importance score
  - Prep priority level
  - Performance classification

- **`deck_analysis_ARCHETYPE_W11.xlsx`** - Same metrics aggregated by archetype

- **`deck_analysis_WITH_TRENDS_W11.xlsx`** - Deck analysis with trend status column

#### History (CSV)
- **`Metagame_History_W11.csv`** - Combined history including all 11 weeks
  - Contains both deck-level (`Level='Deck'`) and archetype-level (`Level='Archetype'`) records
  - Used as input for next week's trend analysis
  - Demonstrates complete data structure with 178 rows (11 weeks × ~16 rows/week)

## What's New in v1.3

### Fixed Issues
- **Deck trend chart now works correctly** - Shows multi-week trend lines instead of single points
- **Tab character handling** - Excel deck names with leading tabs are automatically cleaned
- **Filter order bug** - Historical data for decks with changing rankings is now preserved

### Key Features Demonstrated
- Complete 10-week meta evolution example (Boros Energy rising, Affinity declining, Murktide emerging)
- Dual-level tracking (decks AND archetypes in same history file)
- Trend symbols in legend (^ Rising, - Stable, v Falling)
- All 4 chart types working correctly

## How to Use These Examples

1. **Test the tool** - Upload `Example_Metagame_Data.xlsx.xlsx` to Google Colab
2. **Add history** - Upload `Example_Metagame_History_W1-W10.csv` when prompted
3. **Compare outputs** - Your results should match the charts and files in this folder
4. **Understand trends** - See how Boros Energy's rise from 12.5% (W1) to 14.8% (W11) appears in charts

## Data Format

### Sample Input (Excel) - Week 11

| Deck | Meta | Winrate | Archetype | My Winrate |
|------|------|---------|-----------|-----------|
| Boros Energy | 14.80 | 54 | Aggro | 55 |
| Affinity | 9.71 | 53 | Aggro | 52 |
| Jeskai Blink | 7.35 | 50 | Midrange | 55 |

### Sample History (CSV) - Week 1

| Deck | Meta | Winrate | Archetype | Level | WeekIndex |
|------|------|---------|-----------|-------|-----------|
| Boros Energy | 12.5 | 52 | Aggro | Deck | 1 |
| Aggro | 30.5 | 51.95 | Aggro | Archetype | 1 |

## Interpretation of Output

**Encounter Probability**: Likelihood of facing this deck in a tournament
- Calculated using hypergeometric distribution
- Based on meta percentage and sample size (default: 5-round tournament)
- Encounter charts use a minimum probability filter (default 5%) for readability

**Importance Score**: Combined metric (70% meta + 30% win rate)
- Used to determine prep priority quartile (Q1-Q4)
- Q4 = Very High Priority

**Performance Label**:
- **Underplayed Winner**: Low meta% but high win rate → Good target
- **Popular Trap**: High meta% but low win rate → Avoid playing
- **Neutral**: Average performance

**Trend Status** (v1.3):
- **Rising**: Meta% increased >0.5% (decks) or >0.2% (archetypes) over trend period
- **Falling**: Meta% decreased >0.5% (decks) or >0.2% (archetypes) over trend period
- **Stable**: Change within the thresholds above

## Contact & Feedback

Have questions about the examples? Check the main README.md or docs/DESCRIPTION.txt for more details.
