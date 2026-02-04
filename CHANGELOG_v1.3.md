# MTG Metagame Analyzer v1.3 - Release Notes

**Release Date:** February 4, 2026

## 🎉 Summary

Version 1.3 fixes critical bugs in the deck trend chart functionality and improves data handling for Excel files with formatting issues. All trend visualizations now work correctly, showing complete multi-week trend lines instead of single-point data.

---

## 🐛 Critical Bug Fixes

### 1. **Deck Trend Chart Fixed** ✅
**Problem:** Deck trend chart displayed only single vertical column of points at the current week, instead of showing multi-week trend lines like the archetype chart did.

**Root Cause:** Filter order in `create_trend_chart()` was:
1. Filter by Level (Deck vs Archetype)
2. Filter by selected decks (top 10 from current week) ← **PROBLEM**
3. Filter by week range (e.g., weeks 8-11)

This excluded historical data for decks that weren't in the top 10 during older weeks, even though they're top 10 now.

**Solution:** Reversed filter order to:
1. Filter by Level
2. Filter by week range **FIRST**
3. **THEN** filter by selected decks

**Impact:** Deck trend charts now show complete 4-week (or custom) trend lines for all top 10 decks.

**Example:** Boros Energy at 18.5% Meta in Week 11 might have been 14.5% in Week 8. Old logic excluded Week 8 data; new logic preserves it.

---

### 2. **Tab Character Handling in Excel Files** ✅
**Problem:** Excel files with tab characters (`\t`) in deck names caused name mismatches between current week data and historical CSV, resulting in missing trend data.

**Example:** 
- Excel file: `"	Boros Energy"` (with leading tab)
- History CSV: `"Boros Energy"` (clean)
- Result: No match found → only current week shown in trend

**Solution:** Added automatic deck name cleaning immediately after loading Excel:
```python
# Clean deck names immediately to remove tabs and whitespace
if 'Deck' in df_new.columns:
    df_new['Deck'] = df_new['Deck'].astype(str).str.strip()
```

**Impact:** All leading/trailing whitespace (including tabs) automatically removed from deck names.

---

### 3. **Archetype Data Contamination in Deck Trends** ✅
**Problem:** `calculate_deck_trend_status()` was using archetype-level records when calculating deck trends, because archetypes are stored with `Deck` column = archetype name.

**Solution:** Added Level filtering to exclude archetype records:
```python
if 'Level' in df_history.columns:
    mask = (df_history['Deck'] == deck_name) & 
           ((df_history['Level'] == 'Deck') | (df_history['Level'].isna()))
    deck_history = df_history[mask].sort_values('WeekIndex')
```

**Impact:** Trend calculations now use only deck-level data, not archetype aggregations.

---

### 4. **Archetype Column Stability** ✅
**Problem:** pandas `groupby().apply().reset_index()` operations didn't guarantee that the grouping column (`'Archetype'`) would exist after reset.

**Solution:** Added explicit column existence checks and fallbacks in `aggregate_by_archetype()`:
```python
if 'Archetype' not in df_arch.columns:
    df_arch['Archetype'] = df_arch.index.astype(str)
```

**Impact:** Archetype aggregation now works reliably even with edge-case data.

---

### 5. **Display Name Mapping Error** ✅
**Problem:** When `key_column == display_column` (both `'Archetype'`), calling `.set_index(key_column)[display_column]` failed because the column became the index.

**Solution:** Added conditional check:
```python
if display_column in df_results.columns and key_column != display_column:
    deck_display_names = df_results.nlargest(10, 'Meta').set_index(key_column)[display_column].to_dict()
else:
    deck_display_names = {d: str(d) for d in selected_decks}
```

**Impact:** Archetype trend charts work correctly without KeyError crashes.

---

## 🚀 Improvements

### Backward Compatibility
- Supports historical CSV files without `Level` column (treats all rows as decks)
- Handles missing `Archetype` column gracefully (assigns "Rogue")
- Maintains compatibility with v1.2 and earlier data files

### Enhanced Filtering Logic
- Week range filtering now happens **before** deck selection
- Preserves complete historical data for decks with changing rankings
- More robust handling of NaN and pd.NA values

### Code Quality
- Removed all DEBUG logging statements from production code
- Updated version numbers to 1.3 across all files
- Improved code comments explaining filter order rationale

---

## 📁 Files Changed

### Core Code Files
- **`src/mtg_analyzer.py`** - Production Python script (v1.3)
- **`docs/SCRIPT_FULL.txt`** - Google Colab version (v1.3)

### Documentation Files
- **`README.md`** - Updated version history and troubleshooting
- **`docs/DESCRIPTION.txt`** - Updated version number
- **`examples/README.md`** - New v1.3 section with detailed examples

### Example Files (NEW)
- **`examples/Example_Metagame_History_W1-W10.csv`** - 10-week realistic meta evolution
- **`examples/encounter_prob_Deck_W11.png`** - Fixed deck encounter chart
- **`examples/encounter_prob_Archetype_W11.png`** - Archetype encounter chart
- **`examples/meta_trend_Deck_W11_last4w.png`** - **Fixed deck trend chart** (now shows multi-week lines!)
- **`examples/meta_trend_Archetype_W11_last4w.png`** - Archetype trend chart

---

## 🧪 Testing & Validation

### Test Case: 10-Week Example Data
Created realistic test data spanning 10 weeks demonstrating:
- **Boros Energy**: Rising pillar (12.5% W1 → 18.5% W10)
- **Murktide Tempo**: Emerging threat (0% W1 → 12.8% W10)
- **Affinity**: Declining (11.2% W1 → 2.8% W10)
- **Aggro archetype**: Dominant (30.5% W1 → 39.8% W10)

### Verified Outputs
✅ Deck trend chart shows 4 complete trend lines (weeks 8-11)  
✅ Archetype trend chart shows 6 complete trend lines (weeks 8-11)  
✅ All encounter probability charts render correctly  
✅ History CSV contains both deck-level and archetype-level records (178 rows total)  
✅ Trend symbols display correctly in legends (^ Rising, - Stable, v Falling)  

---

## 📊 Example: Before vs After

### BEFORE v1.3 (Broken)
```
DEBUG: 10 rows after Level filter, 1 unique weeks
DEBUG: Week range: 11-11
DEBUG: Unique decks: 10
DEBUG: Weeks covered: [11]
```
**Result:** Single vertical column of points at Week 11

### AFTER v1.3 (Fixed)
```
✓ History: 178 rows, 11 weeks
📊 Generating trend chart (last 4 weeks)...
✅ Trend chart saved: meta_trend_Deck_W11_last4w.png
```
**Result:** Complete trend lines across weeks 8-11 for all 10 decks

---

## 🔄 Migration Guide

### For Users Upgrading from v1.2 or Earlier

1. **Update your script files:**
   - Replace `src/mtg_analyzer.py` or `docs/SCRIPT_FULL.txt` with v1.3 versions

2. **Fix Excel file formatting (if needed):**
   - v1.3 auto-cleans tab characters, but for best results:
   - Open Excel file → Select Deck column → Find & Replace tabs with nothing
   - Or just let v1.3 auto-clean (recommended)

3. **Optional: Regenerate history CSV:**
   - If you have old history with tab characters in deck names
   - Re-run analysis with all your Excel files to create clean history
   - This ensures 100% name matching for trends

4. **No data loss:**
   - All existing CSV history files work with v1.3
   - Backward compatible with files lacking `Level` column

---

## 🎯 Known Limitations

- Trend charts require at least 2 weeks of history data
- Maximum trend period is limited by available historical weeks
- Deck names must match exactly between Excel and CSV (case-sensitive, but whitespace auto-cleaned)

---

## 📝 Technical Details

### Filter Order Change (Key Fix)

**Old Logic (BROKEN):**
```python
# 1. Filter by Level
df_filtered = df_history[mask_level]
# 2. Filter by selected decks (top 10 from Week 11)
df_filtered = df_filtered[df_filtered['Deck'].isin(selected_decks)]
# 3. Filter by week range (8-11)
df_trend = df_filtered[(WeekIndex >= 8) & (WeekIndex <= 11)]
```

**New Logic (FIXED):**
```python
# 1. Filter by Level
df_level_filtered = df_history[mask_level]
# 2. Filter by week range FIRST (8-11)
df_week_filtered = df_level_filtered[(WeekIndex >= 8) & (WeekIndex <= 11)]
# 3. THEN filter by selected decks (top 10)
df_trend = df_week_filtered[df_week_filtered['Deck'].isin(selected_decks)]
```

**Why This Matters:**
- Old: Excluded weeks where current top-10 decks had lower rankings
- New: Preserves all historical data for currently-top-10 decks

---

## 🙏 Acknowledgments

Thanks to the community for reporting the deck trend chart issue and providing detailed reproduction steps with screenshots. Your feedback made this fix possible!

---

## 📮 Support

- **Issues:** Report bugs via GitHub Issues
- **Questions:** Check README.md and docs/DESCRIPTION.txt
- **Examples:** See `examples/` folder for working test data

---

**Full Changelog:** [View all changes](https://github.com/yourusername/MTG-Metagame-Analyzer/compare/v1.2...v1.3)
