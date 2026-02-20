# Changelog for MTG Metagame Analyzer v1.4

## [v1.4] - 2026-02-20

### Added
- New chart: **My Deck Performance** (encounter probability colored by your winrate against each deck)
- New chart: **Record Probability Distribution** (binomial model for 5-0, 4-1, etc.)
- New Excel output: **Record probabilities per deck**

### Changed
- Renamed input column "My Winrate" to **"My Deck Winrate"** (backward compatible: old column auto-renamed)
- Improved input normalization: accepts both decimal and percent formats for winrates and meta
- Enhanced error handling and user prompts

### Fixed
- All known bugs from v1.3, including column normalization and KeyError issues
- Improved compatibility with various Excel input formats

### Notes
- All documentation and input templates updated for v1.4
- See README.md for full usage instructions and feature list# MTG Metagame Analyzer v1.4 - Release Notes

**Release Date:** 2026-02-20

## 🎉 Highlights

- New input column: `My Deck Winrate` (your personal winrate against each deck)
- New chart: My Deck Performance (problem score, colored by your winrate)
- New chart: Record Probability (binomial distribution for your record and all decks)
- New Excel output: Record Probability Table (record probabilities for each deck)
- Full backward compatibility with the old `My Winrate` column (auto-migrated)
- Improved summaries and reporting
- Bugfixes and better input handling

## 🛠️ How to Update

1. Pull the latest repository changes (`git pull`).
2. Make sure you have all required packages (`pip install -r requirements.txt`).
3. Run `src/mtg_analyzer.py` or use the Colab version from `docs/SCRIPT_FULL.txt`.
4. See the updated README.md for details.

## 📝 Technical Changes

- All new features and charts in `src/mtg_analyzer.py`
- Updated input and output file formats
- Improved history and archetype aggregation
# MTG Metagame Analyzer v1.4 - Release Notes

**Release Date:** 2026-02-20

## 🎉 Highlights

- New input column: `My Deck Winrate` (your personal winrate against each deck)
- New chart: My Deck Performance (problem score, colored by your winrate)
- New chart: Record Probability (binomial distribution for your record and all decks)
- New Excel output: Record Probability Table (record probabilities for each deck)
- Full backward compatibility with the old `My Winrate` column (auto-migrated)
- Improved summaries and reporting
- Bugfixes and better input handling

## 🛠️ Upgrade Instructions

1. Pull the latest repository changes (`git pull`).
2. Ensure all dependencies are installed (`pip install -r requirements.txt`).
3. Run `src/mtg_analyzer.py` or use the Colab version from `docs/SCRIPT_FULL.txt`.
4. Review the updated README.md for new features and input format.

## 📝 Technical Changes

- New features and charts in `src/mtg_analyzer.py`
- Updated input and output file formats
- Improved history and archetype aggregation handling
