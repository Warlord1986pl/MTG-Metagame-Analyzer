# MTG METAGAME ANALYSIS v1.3 - GOOGLE COLAB
# =====================================
# INSTRUCTIONS:
# 1. Open Google Colab: colab.research.google.com
# 2. Copy this entire file into Colab
# 3. Click "Runtime" → "Run all" (or Ctrl+F9)
# 4. Upload your Excel file when prompted
# 5. Wait for charts and download ZIP results
# =====================================

# Install packages (Colab only)
IN_COLAB = False
try:
    import google.colab  # type: ignore
    IN_COLAB = True
except Exception:
    IN_COLAB = False

if IN_COLAB:
    import subprocess
    import sys as _sys
    subprocess.run([
        _sys.executable, "-m", "pip", "install", "-q", "mplcursors", "openpyxl"
    ], check=False)

# Imports
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import sys
import importlib
import importlib.metadata
import os

REQUIRED_PACKAGES = {
    "mplcursors": "0.5.0",
    "openpyxl": "3.1.5",
    "pandas": "1.3.0",
    "matplotlib": "3.4.0",
    "numpy": "1.21.0",
}

def check_runtime_requirements():
    """Return missing and outdated packages based on REQUIRED_PACKAGES."""
    try:
        from packaging.version import Version
    except Exception:
        Version = None

    missing = []
    outdated = []
    for pkg, min_version in REQUIRED_PACKAGES.items():
        try:
            current = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            missing.append(pkg)
            continue

        if Version is not None and min_version:
            try:
                if Version(current) < Version(min_version):
                    outdated.append((pkg, current, min_version))
            except Exception:
                pass
    return missing, outdated

def offer_install_requirements(missing, outdated):
    """Offer to install missing/outdated requirements. Return True if ready."""
    if not missing and not outdated:
        return True

    print("\n❗ Missing or outdated Python packages detected:")
    if missing:
        print("  Missing:", ", ".join(missing))
    if outdated:
        print("  Outdated:")
        for pkg, current, minimum in outdated:
            print(f"   - {pkg}: {current} (min {minimum})")

    answer = input("Install/upgrade now? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        print("\nPlease install the missing packages and rerun.")
        return False

    import subprocess
    install_args = []
    for pkg in missing:
        min_version = REQUIRED_PACKAGES.get(pkg)
        install_args.append(f"{pkg}>={min_version}" if min_version else pkg)
    for pkg, _, minimum in outdated:
        install_args.append(f"{pkg}>={minimum}")

    if install_args:
        subprocess.run([
            sys.executable, "-m", "pip", "install", *install_args
        ], check=False)

    missing_after, outdated_after = check_runtime_requirements()
    if missing_after or outdated_after:
        print("\n❌ Some requirements are still missing or outdated.")
        return False

    print("\n✅ Requirements are installed.")
    return True

# =====================================
# HELPER FUNCTIONS
def calculate_binomial_records(winrate, rounds):
    """
    Calculate probability of each W-L record over N rounds.
    Uses binomial distribution: P(W wins) = C(N,W) * p^W * (1-p)^(N-W)
    Returns dict: {'5-0': 0.33, '4-1': 0.41, ...}
    """
    from math import comb
    winrate = max(0.0, min(1.0, float(winrate)))
    records = {}
    for wins in range(rounds + 1):
        losses = rounds - wins
        prob = comb(rounds, wins) * (winrate ** wins) * ((1 - winrate) ** losses)
        records[f"{wins}-{losses}"] = prob
    return records

# =====================================

def hypergeometric_probability(N, K, sample_size, threshold=1):
    """Calculate probability of encountering a given deck"""
    from math import comb
    if N <= 0 or sample_size <= 0 or threshold <= 0:
        return 0.0
    sample_size = min(sample_size, N)
    max_successes = min(K, sample_size)
    threshold = min(threshold, max_successes)
    total = comb(N, sample_size)
    if total == 0:
        return 0.0
    prob = 0
    for k in range(threshold, max_successes + 1):
        prob += comb(K, k) * comb(N - K, sample_size - k)
    return prob / total

def prep_priority(quartile):
    """Determine preparation priority level"""
    mapping = {
        'Q4': 'Very High Prep Priority',
        'Q3': 'High Prep Priority',
        'Q2': 'Medium Prep Priority',
        'Q1': 'Low Prep Priority'
    }
    return mapping.get(quartile, 'Low Prep Priority')

def trend_label(current, past_avg, threshold=1.0):
    """Determine deck trend status (Rising/Falling/Stable)"""
    if current - past_avg > threshold:
        return 'Rising Deck'
    elif current - past_avg < -threshold:
        return 'Falling Deck'
    else:
        return 'Stable'

# Color palettes
PERFORMANCE_COLORS = {
    'Underplayed Winner': "#b9f03a",
    'Popular Trap': "#f07431",
    'Neutral': '#000000'
}

PREP_PRIORITY_COLORS = {
    'Very High Prep Priority': 'red',
    'High Prep Priority': 'orange',
    'Medium Prep Priority': 'blue',
    'Low Prep Priority': 'green'
}

TREND_COLORS = {
    'Rising Deck': '#2ecc71',
    'Falling Deck': '#e74c3c',
    'Stable': '#95a5a6'
}

# Trend thresholds (percentage points)
TREND_THRESHOLD_DECK = 0.5
TREND_THRESHOLD_ARCHETYPE = 0.2

def aggregate_by_archetype(df_results):
    """Aggregate deck data by archetype"""
    df = df_results.copy()
    # Handle both NaN and pd.NA for Archetype column
    if 'Archetype' not in df.columns:
        df['Archetype'] = 'Rogue'
    else:
        # Replace both NaN and pd.NA with 'Rogue'
        df['Archetype'] = df['Archetype'].fillna('Rogue').astype(str).replace('<NA>', 'Rogue')
    
    df_arch = (
        df
        .groupby('Archetype', dropna=False)
        .apply(lambda g: pd.Series({
            'Meta': g['Meta'].sum(),
            'Winrate': np.average(g['Winrate'], weights=g['Meta']) if g['Meta'].sum() > 0 else np.nan,
            'My Deck Winrate': (
                np.average(g['My Deck Winrate'].dropna(), weights=g.loc[g['My Deck Winrate'].notna(), 'Meta'])
                if 'My Deck Winrate' in g.columns and g['My Deck Winrate'].notna().any() else pd.NA
            )
        }))
        .reset_index()
    )
    if 'Archetype' not in df_arch.columns:
        df_arch['Archetype'] = df_arch.index.astype(str)
    df_arch['Deck Display Name'] = df_arch['Archetype'].astype(str)
    return df_arch

def calculate_archetype_metrics(df_arch, total_players, sample_size=5):
    """Calculate metrics for archetypes"""
    df = df_arch.copy()
    df['Encounter Copies'] = (total_players * df['Meta'] / 100).round().astype(int)
    # sample_size only affects encounter probability, not meta share or trends
    df['Encounter Probability'] = df.apply(
        lambda r: hypergeometric_probability(total_players, int(r['Encounter Copies']), sample_size, 1), axis=1
    )

    max_meta = df['Meta'].max() if pd.notna(df['Meta'].max()) and df['Meta'].max() > 0 else 1
    min_wr = df['Winrate'].min()
    max_wr = df['Winrate'].max()
    wr_range = (max_wr - min_wr) if pd.notna(max_wr) and pd.notna(min_wr) and (max_wr - min_wr) > 0 else 1

    df['Importance'] = 0.7 * (df['Meta'] / max_meta) + 0.3 * ((df['Winrate'] - min_wr) / wr_range)

    q1, q2, q3 = df['Importance'].quantile([0.25, 0.5, 0.75])

    def quartile_label(val):
        if val <= q1: return 'Q1'
        elif val <= q2: return 'Q2'
        elif val <= q3: return 'Q3'
        return 'Q4'

    df['Quartile'] = df['Importance'].apply(quartile_label)
    df['Prep Priority'] = df['Quartile'].apply(prep_priority)

    meta_med = df['Meta'].median()
    winrate_med = df['Winrate'].median()

    def perf_label(row):
        if row['Meta'] < meta_med and row['Winrate'] > winrate_med:
            return 'Underplayed Winner'
        if row['Meta'] > meta_med and row['Winrate'] < winrate_med:
            return 'Popular Trap'
        return 'Neutral'

    df['Performance Label'] = df.apply(perf_label, axis=1)
    return df

def show_plot_nonblocking():
    """Show plots without blocking script execution outside Colab."""
    if IN_COLAB:
        plt.show()
        return
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()

def create_encounter_probability_chart(df_results, week_num, N_players, chart_type="Deck", min_encounter_threshold=0.05, output_dir=None):
    """Create encounter probability bar chart"""
    plt.figure(figsize=(20, 12))
    # Filter by minimum encounter probability threshold
    df_filtered = df_results[df_results['Encounter Probability'] >= min_encounter_threshold].copy()
    if len(df_filtered) == 0:
        print(f"⚠ No {chart_type.lower()}s with encounter probability >= {min_encounter_threshold:.1%}")
        df_filtered = df_results.copy()
    df_sorted = df_filtered.sort_values('Encounter Probability', ascending=False).reset_index(drop=True)
    num_decks = len(df_sorted)
    cmap = plt.cm.rainbow
    bar_colors = cmap(np.linspace(1, 0, num_decks)) if num_decks > 0 else []
    bars = plt.bar(range(num_decks), df_sorted['Encounter Probability'], color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.5)

    plt.ylabel('Encounter Probability', fontsize=14)
    threshold_text = f' (min. {min_encounter_threshold:.1%})' if min_encounter_threshold > 0 else ''
    plt.title(f'Encounter Probability ({chart_type}){threshold_text} (N={N_players}) - Week {week_num}', fontsize=16, pad=20)
    plt.ylim(0, 1.05)

    for i, (bar, prob, prep, my_wr) in enumerate(zip(bars, df_sorted['Encounter Probability'], df_sorted['Prep Priority'], df_sorted.get('My Winrate', pd.Series([pd.NA]*num_decks)))):
        label = f"{prob:.1%}"
        if not pd.isna(my_wr):
            label += " *"
        color = PREP_PRIORITY_COLORS.get(prep, 'black')
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015, label, ha='center', va='bottom', fontsize=11, color=color)

    rotation_angle = 30 if num_decks < 12 else 45 if num_decks < 20 else 60
    for i, (deck, perf_label) in enumerate(zip(df_sorted['Deck Display Name'], df_sorted['Performance Label'])):
        plt.text(i, -0.03, deck, ha='right', va='top', fontsize=9, rotation=rotation_angle, color=PERFORMANCE_COLORS.get(perf_label, 'black'))

    plt.tick_params(axis='x', which='both', length=0, labelbottom=False)
    plt.gca().spines['bottom'].set_visible(False)

    perf_patches = [
        Patch(facecolor=PERFORMANCE_COLORS['Underplayed Winner'], label='Underplayed Winner'),
        Patch(facecolor=PERFORMANCE_COLORS['Popular Trap'], label='Popular Trap'),
        Patch(facecolor=PERFORMANCE_COLORS['Neutral'], label='Neutral')
    ]
    prep_patches = [
        Patch(facecolor='red', label='Very High'),
        Patch(facecolor='orange', label='High'),
        Patch(facecolor='blue', label='Medium'),
        Patch(facecolor='green', label='Low')
    ]

    leg1 = plt.legend(handles=prep_patches, title="Prep Priority", loc='upper right', bbox_to_anchor=(0.98, 0.98), fontsize=10)
    leg2 = plt.legend(handles=perf_patches, title="Performance Colors", loc='upper right', bbox_to_anchor=(0.98, 0.78), fontsize=10)
    plt.gca().add_artist(leg1)

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.45, right=0.85)
    out_dir = output_dir or "."
    out_png = os.path.join(out_dir, f'encounter_prob_{chart_type}_W{week_num}.png')
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    show_plot_nonblocking()

    my_wr_count = df_sorted.get('My Winrate', pd.Series()).notna().sum()
    if my_wr_count > 0:
        print(f"ℹ {my_wr_count} decks use My Winrate (marked with *)")
    return out_png

def calculate_deck_trend_status(df_history, deck_name, weeks_back=4, chart_type="Deck"):
    """Calculate deck/archetype trend status"""
    # Filter by deck name with correct Level type
    if 'Level' in df_history.columns:
        if chart_type == "Archetype":
            mask = (df_history['Deck'] == deck_name) & (df_history['Level'] == 'Archetype')
        else:
            mask = (df_history['Deck'] == deck_name) & ((df_history['Level'] == 'Deck') | (df_history['Level'].isna()))
        deck_history = df_history[mask].sort_values('WeekIndex')
    else:
        deck_history = df_history[df_history['Deck'] == deck_name].sort_values('WeekIndex')
    
    if len(deck_history) < 2:
        return 'Stable', TREND_COLORS['Stable']
    
    recent = deck_history.tail(weeks_back)
    
    if len(recent) < 2:
        return 'Stable', TREND_COLORS['Stable']
    
    weeks = recent['WeekIndex'].values
    meta_values = recent['Meta'].values
    trend_change = meta_values[-1] - meta_values[0]
    threshold = TREND_THRESHOLD_ARCHETYPE if chart_type == "Archetype" else TREND_THRESHOLD_DECK
    
    if trend_change > threshold:
        return 'Rising', TREND_COLORS['Rising Deck']
    elif trend_change < -threshold:
        return 'Falling', TREND_COLORS['Falling Deck']
    else:
        return 'Stable', TREND_COLORS['Stable']

def create_trend_chart(df_history, df_results, weeks_back, week_num, chart_type="Deck", output_dir=None):
    """Create trend chart - FIXED (clean legend, reversed colors)"""
    if len(df_history) == 0:
        print("ℹ No history data available for trend chart")
        return None
    
    # For Archetype chart, try 'Archetype' column first, then 'Deck'
    key_column = None
    display_column = None
    
    if chart_type == "Archetype":
        if 'Archetype' in df_results.columns:
            key_column = 'Archetype'
            display_column = 'Archetype'
        elif 'Deck' in df_results.columns:
            key_column = 'Deck'
            display_column = 'Deck'
    else:
        if 'Deck' in df_results.columns:
            key_column = 'Deck'
            display_column = 'Deck Display Name' if 'Deck Display Name' in df_results.columns else 'Deck'
    
    if key_column is None or key_column not in df_results.columns:
        print(f"ℹ Required column not found for {chart_type} chart")
        return None
    
    selected_decks = df_results.nlargest(10, 'Meta')[key_column].tolist()
    
    # Build display names dictionary
    if display_column in df_results.columns and key_column != display_column:
        # Different columns: map key_column to display_column
        deck_display_names = df_results.nlargest(10, 'Meta').set_index(key_column)[display_column].to_dict()
    else:
        # Same column or display_column doesn't exist: use key_column values as-is
        deck_display_names = {d: str(d) for d in selected_decks}
    
    if not selected_decks:
        print("ℹ No decks available for trend chart")
        return None
    
    # Filter history by the correct Level type first
    if chart_type == "Archetype":
        # For archetypes, explicitly filter by Level == 'Archetype'
        if 'Level' not in df_history.columns:
            print("ℹ Archetype trend chart requires history with 'Level' column")
            return None
        df_level_filtered = df_history[df_history['Level'] == 'Archetype'].copy()
    else:
        # For decks, include rows where Level == 'Deck' OR Level is missing/NaN (backward compatibility)
        if 'Level' in df_history.columns:
            mask_deck = (df_history['Level'] == 'Deck') | (df_history['Level'].isna())
            df_level_filtered = df_history[mask_deck].copy()
        else:
            # No Level column at all - assume all are decks
            df_level_filtered = df_history.copy()
    
    # Get week range BEFORE filtering by selected decks
    if 'WeekIndex' not in df_level_filtered.columns or len(df_level_filtered) == 0:
        print(f"ℹ No history data available for {chart_type} trend chart")
        return None
    
    max_week = df_level_filtered['WeekIndex'].max()
    min_week = max(1, max_week - weeks_back + 1)
    df_week_filtered = df_level_filtered[(df_level_filtered['WeekIndex'] >= min_week) & (df_level_filtered['WeekIndex'] <= max_week)].copy()
    
    # NOW select top 10 decks from the current week (for legend/display)
    # But include ALL their historical data from the week range
    df_trend = df_week_filtered[df_week_filtered['Deck'].isin(selected_decks)].copy()
    
    if len(df_trend) == 0:
        print(f"ℹ No trend data for last {weeks_back} weeks")
        return None
    
    plt.figure(figsize=(18, 11))
    
    cmap = plt.cm.rainbow
    num_decks = len(selected_decks)
    # Reversed color mapping
    deck_colors = {deck: cmap(1 - i / max(1, num_decks - 1)) for i, deck in enumerate(selected_decks)}
    
    legend_elements = []
    
    for deck in selected_decks:
        deck_data = df_trend[df_trend['Deck'] == deck].sort_values('WeekIndex')
        if len(deck_data) > 0:
            trend_status, _ = calculate_deck_trend_status(df_history, deck, weeks_back, chart_type=chart_type)
            trend_symbol = '^' if trend_status == 'Rising' else 'v' if trend_status == 'Falling' else '-'
            # Use cleaned name without symbols
            display_name = deck_display_names.get(deck, deck)
            label = f"{display_name} {trend_symbol}"
            
            plt.plot(deck_data['WeekIndex'], deck_data['Meta'], 
                    marker='o', linewidth=2.5, markersize=8, 
                    color=deck_colors[deck])
            
            # Legend with matching markers
            legend_elements.append(
                Line2D([0], [0], color=deck_colors[deck], linewidth=2.5, 
                       marker='o', markersize=6, label=label)
            )
    
    ax = plt.gca()
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.xlabel('Week', fontsize=12)
    plt.ylabel('Meta %', fontsize=12)
    plt.title(f'Meta Trend ({chart_type}) - Last {weeks_back} weeks', fontsize=14, pad=20)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    plt.legend(handles=legend_elements, title="Decks (Trend Status)", 
               loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9, 
               framealpha=0.95, title_fontsize=10)
    
    trend_box_text = "^ Rising  |  - Stable  |  v Falling"
    plt.text(0.5, -0.08, trend_box_text, transform=plt.gca().transAxes, 
             ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12, right=0.82)
    
    out_dir = output_dir or "."
    out_png = os.path.join(out_dir, f'meta_trend_{chart_type}_W{week_num}_last{weeks_back}w.png')
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    show_plot_nonblocking()
    
    print(f"✅ Trend chart saved: {out_png}")
    return out_png

def analyze_metagame(filename_excel, history_csv=None, total_encounter_players=1000, sample_size=5):
    """Main metagame analysis function"""
    try:
        df_new = pd.read_excel(filename_excel)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise

    # Clean deck names immediately to remove tabs and whitespace
    if 'Deck' in df_new.columns:
        df_new['Deck'] = df_new['Deck'].astype(str).str.strip()

    # Normalize numeric inputs (handles commas and percent strings)
    if 'Meta' in df_new.columns:
        meta_raw = df_new['Meta'].astype(str)
        meta_clean = meta_raw.str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        df_new['Meta'] = pd.to_numeric(meta_clean, errors='coerce')
        meta_invalid = df_new['Meta'].isna().sum()
        if meta_invalid > 0:
            print(f"⚠ Meta conversion: {meta_invalid} rows became NaN (check input format)")
    if 'Winrate' in df_new.columns:
        winrate_raw = df_new['Winrate'].astype(str)
        winrate_has_pct = winrate_raw.str.contains('%', regex=False)
        winrate_clean = winrate_raw.str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        winrate_num = pd.to_numeric(winrate_clean, errors='coerce')
        if winrate_has_pct.any() or (pd.notna(winrate_num).any() and winrate_num.max() > 1):
            winrate_num = winrate_num / 100
        df_new['Winrate'] = winrate_num
        winrate_invalid = df_new['Winrate'].isna().sum()
        if winrate_invalid > 0:
            print(f"⚠ Winrate conversion: {winrate_invalid} rows became NaN (check input format)")

    # Normalize My Deck Winrate (v1.4: renamed from My Winrate)
    if 'My Deck Winrate' in df_new.columns:
        my_wr_raw = df_new['My Deck Winrate'].astype(str)
        has_pct_my = my_wr_raw.str.contains('%', regex=False)
        my_wr_clean = my_wr_raw.str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        my_wr_num = pd.to_numeric(my_wr_clean, errors='coerce')
        if has_pct_my.any() or (pd.notna(my_wr_num).any() and my_wr_num.max() > 1):
            my_wr_num = my_wr_num / 100
        df_new['My Deck Winrate'] = my_wr_num
    elif 'My Winrate' in df_new.columns:
        # Backward compatibility: accept old column name, rename it
        print("Info: 'My Winrate' column found - renamed to 'My Deck Winrate' (update your template)")
        my_wr_raw = df_new['My Winrate'].astype(str)
        has_pct_my = my_wr_raw.str.contains('%', regex=False)
        my_wr_clean = my_wr_raw.str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
        my_wr_num = pd.to_numeric(my_wr_clean, errors='coerce')
        if has_pct_my.any() or (pd.notna(my_wr_num).any() and my_wr_num.max() > 1):
            my_wr_num = my_wr_num / 100
        df_new['My Deck Winrate'] = my_wr_num
        df_new = df_new.drop(columns=['My Winrate'])
    else:
        df_new['My Deck Winrate'] = pd.NA
    if 'Archetype' not in df_new.columns:
        df_new['Archetype'] = pd.NA

    df_history = pd.DataFrame()
    if history_csv:
        try:
            df_history = pd.read_csv(history_csv)
            print(f"✓ History loaded: {len(df_history)} rows")
        except FileNotFoundError:
            print("ℹ History file not found — continuing without history")
            df_history = pd.DataFrame()
        except Exception as e:
            print(f"ℹ Error loading history: {e} — continuing without history")
            df_history = pd.DataFrame()

    if 'WeekIndex' in df_history.columns:
        df_history['WeekIndex'] = pd.to_numeric(df_history['WeekIndex'], errors='coerce')

    if len(df_history) > 0 and 'WeekIndex' in df_history.columns:
        max_week = df_history['WeekIndex'].max()
        this_week_idx = int(max_week) + 1 if pd.notna(max_week) else 1
    else:
        this_week_idx = 1
    print(f"✓ Week: {this_week_idx}")

    df_new['WeekIndex'] = this_week_idx
    df_new['Deck Display Name'] = df_new['Deck'].astype(str).str.replace(r'[\[\]□■▪•]', '', regex=True).str.strip()

    total_players = total_encounter_players
    # sample_size influences encounter odds only; meta share and trends use Meta column
    sample_size = max(1, min(int(sample_size), total_players))
    df_new['Encounter Copies'] = (total_players * df_new['Meta'] / 100).round().astype(int)
    df_new['Encounter Probability'] = df_new.apply(
        lambda r: hypergeometric_probability(total_players, int(r['Encounter Copies']), sample_size, 1), axis=1
    )

    max_meta = df_new['Meta'].max() if pd.notna(df_new['Meta'].max()) and df_new['Meta'].max() > 0 else 1
    min_wr = df_new['Winrate'].min()
    max_wr = df_new['Winrate'].max()
    wr_range = (max_wr - min_wr) if pd.notna(max_wr) and pd.notna(min_wr) and (max_wr - min_wr) > 0 else 1

    df_new['Importance'] = 0.7 * (df_new['Meta'] / max_meta) + 0.3 * ((df_new['Winrate'] - min_wr) / wr_range)

    q1, q2, q3 = df_new['Importance'].quantile([0.25, 0.5, 0.75])
    def quartile_label(val):
        if val <= q1: return 'Q1'
        elif val <= q2: return 'Q2'
        elif val <= q3: return 'Q3'
        return 'Q4'
    df_new['Quartile'] = df_new['Importance'].apply(quartile_label)
    df_new['Prep Priority'] = df_new['Quartile'].apply(prep_priority)

    meta_med, winrate_med = df_new['Meta'].median(), df_new['Winrate'].median()
    def perf_label(row):
        if row['Meta'] < meta_med and row['Winrate'] > winrate_med:
            return 'Underplayed Winner'
        if row['Meta'] > meta_med and row['Winrate'] < winrate_med:
            return 'Popular Trap'
        return 'Neutral'
    df_new['Performance Label'] = df_new.apply(perf_label, axis=1)

    if len(df_history) > 0 and 'Deck' in df_history.columns:
        df_tmp = df_history.sort_values('WeekIndex').groupby('Deck').tail(4)
        trend_meta = df_tmp.groupby('Deck')['Meta'].mean().to_dict()
        df_new['Trend Label'] = df_new.apply(
            lambda r: trend_label(r['Meta'], trend_meta.get(r['Deck'], r['Meta']), threshold=TREND_THRESHOLD_DECK),
            axis=1
        )
    else:
        df_new['Trend Label'] = 'Stable'

    def pillar_flag(deck):
        if len(df_history) == 0 or 'Deck' not in df_history.columns:
            return False
        if 'Prep Priority' not in df_history.columns:
            return False
        recent = df_history[df_history['Deck'] == deck].sort_values('WeekIndex').tail(3)
        return len(recent) >= 3 and all(recent['Prep Priority'] == 'Very High Prep Priority')

    df_new['Pillar'] = df_new['Deck'].apply(pillar_flag)
    df_new['Emerging Threat'] = False
    df_new['Declining Threat'] = False
    df_new['Level'] = 'Deck'

    if len(df_history) > 0 and 'Deck' in df_history.columns:
        mask_dup = (df_history['WeekIndex'] == this_week_idx) & df_history['Deck'].isin(df_new['Deck'])
        df_history = df_history[~mask_dup]
    df_history = pd.concat([df_history, df_new], ignore_index=True)

    # Add archetypes to history
    df_arch_for_history = aggregate_by_archetype(df_new)
    df_arch_for_history = calculate_archetype_metrics(df_arch_for_history, total_players, sample_size=sample_size)
    df_arch_for_history['Level'] = 'Archetype'
    df_arch_for_history['Deck'] = df_arch_for_history['Archetype']
    df_arch_for_history['WeekIndex'] = this_week_idx
    df_arch_for_history['Trend Label'] = 'Stable'
    df_arch_for_history['Pillar'] = False
    df_arch_for_history['Emerging Threat'] = False
    df_arch_for_history['Declining Threat'] = False
    
    # Remove old archetype entries for this week if they exist
    if len(df_history) > 0 and 'Level' in df_history.columns:
        mask_arch_dup = (df_history['WeekIndex'] == this_week_idx) & (df_history['Level'] == 'Archetype')
        df_history = df_history[~mask_arch_dup]
    
    df_history = pd.concat([df_history, df_arch_for_history], ignore_index=True)

    print("✅ Analysis complete!")
    return df_new, df_history, this_week_idx, total_players, sample_size

# =====================================
# PROGRAM EXECUTION
# =====================================

import zipfile
import os

def try_pick_file_dialog(title, filetypes):
    """Try to open a file picker; return empty string on cancel or failure."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        return path or ""
    except Exception:
        return ""

def try_pick_directory_dialog(title):
    """Try to open a folder picker; return empty string on cancel or failure."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title=title)
        root.destroy()
        return path or ""
    except Exception:
        return ""


# ===================== v1.4 PROMPTS AND NEW FEATURES =====================
print("\n" + "="*80)
print("MTG METAGAME ANALYSIS v1.4 - START")
print("="*80 + "\n")

missing_pkgs, outdated_pkgs = check_runtime_requirements()
if not offer_install_requirements(missing_pkgs, outdated_pkgs):
    sys.exit(1)

if IN_COLAB:
    print("Colab upload/download not supported in this version. Please provide file paths manually.")
    sys.exit(1)
    output_dir = os.getcwd()
else:
    excel_file = try_pick_file_dialog(
        "Select Excel file (Deck, Meta, Winrate)",
        [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
    )
    if not excel_file:
        excel_file = input("Path to Excel file (columns: Deck, Meta, Winrate): ").strip()
    if not excel_file:
        print("❌ No file path provided. Exiting.")
        sys.exit(1)

    history_csv = try_pick_file_dialog(
        "Select history CSV (optional)",
        [("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not history_csv:
        history_csv = input("Optional path to history CSV (press Enter to skip): ").strip() or None

    output_dir = try_pick_directory_dialog("Select output folder")
    if not output_dir:
        output_dir = input("Output folder (press Enter for current): ").strip() or os.getcwd()
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

print(f"✓ Output folder: {output_dir}")

# Player count
try:
    N_players = int(input("Player count for calculations (default 1000): ").strip() or 1000)
except Exception:
    N_players = 1000

# Number of rounds/opponents
try:
    rounds = int(input("How many rounds/opponents? (default 5): ").strip() or 5)
    rounds = max(1, rounds)
except Exception:
    rounds = 5

# Encounter probability threshold
min_encounter_pct = 5.0
try:
    min_encounter_pct = float(input("Minimum encounter probability to display (default 5%): ").strip() or 5)
except Exception:
    min_encounter_pct = 5.0
min_encounter_threshold = min_encounter_pct / 100

# NEW in v1.4: Deck name for chart titles
print("\n--- Your Deck Settings (NEW in v1.4) ---")
try:
    deck_name_input = input("Your deck name (press Enter for default 'My Deck'): ").strip()
    player_deck_name = deck_name_input if deck_name_input else "My Deck"
except Exception:
    player_deck_name = "My Deck"
print(f"Deck name set to: {player_deck_name}")

# NEW in v1.4: Player overall winrate for record probability chart
print("\n--- Record Probability Settings (NEW in v1.4) ---")
print("Your overall winrate is used to calculate your expected record distribution.")
print("If you don't know it, press Enter to use 50% (neutral assumption).")
try:
    player_wr_input = input("Your overall winrate (e.g. 0.55 or 55%, default 50%): ").strip()
    if not player_wr_input:
        player_overall_winrate = 0.50
    else:
        player_overall_winrate = float(player_wr_input.replace('%', '').replace(',', '.'))
        if player_overall_winrate > 1:
            player_overall_winrate /= 100
        player_overall_winrate = max(0.01, min(0.99, player_overall_winrate))
except Exception:
    player_overall_winrate = 0.50
    print("Could not parse winrate - using 50%")
print(f"Player winrate set to: {player_overall_winrate:.1%}")

print(f"\nStarting analysis (N={N_players}, rounds={rounds}, min encounter: {min_encounter_pct:g}%, player WR: {player_overall_winrate:.1%})...\n")
print("Note: rounds/opponents affect encounter probability only; meta share and trends use the Meta column.")

# Run main analysis
df_results, df_history, week_num, N_players, rounds = analyze_metagame(
    excel_file, history_csv, N_players, sample_size=rounds
)

print(f"\nHistory: {df_history.shape[0]} rows, {df_history['WeekIndex'].nunique()} weeks")

# Generate archetype charts
print("\nGenerating archetype encounter chart...")
df_arch = aggregate_by_archetype(df_results)
df_arch = calculate_archetype_metrics(df_arch, N_players, sample_size=rounds)
arch_chart = create_encounter_probability_chart(
    df_arch, week_num, N_players, chart_type="Archetype",
    min_encounter_threshold=min_encounter_threshold, output_dir=output_dir
)

# Generate deck encounter chart
print("\nGenerating deck encounter chart...")
deck_chart = create_encounter_probability_chart(
    df_results, week_num, N_players, chart_type="Deck",
    min_encounter_threshold=min_encounter_threshold, output_dir=output_dir
)

# NEW in v1.4: My Deck Performance chart
def create_my_deck_performance_chart(df_results, week_num, N_players, min_encounter_threshold=0.05, player_deck_name="My Deck"):
    my_wr_col = 'My Deck Winrate'
    df_my = df_results[df_results[my_wr_col].notna()].copy()
    if len(df_my) == 0:
        print("Info: No 'My Deck Winrate' data in input - skipping my deck performance chart.")
        print("      Fill in 'My Deck Winrate' column in your Excel template to enable this chart.")
        return None
    df_show = df_my[df_my['Encounter Probability'] >= min_encounter_threshold].copy()
    if len(df_show) == 0:
        print("Info: No decks with My Deck Winrate above encounter threshold - using all.")
        df_show = df_my.copy()
    df_show['Problem Score'] = df_show['Encounter Probability'] * (1 - df_show[my_wr_col])
    df_show = df_show.sort_values('Problem Score', ascending=False).reset_index(drop=True)
    num_decks = len(df_show)
    fig_width = max(14, num_decks * 1.3)
    fig, ax = plt.subplots(figsize=(fig_width, 10))
    norm = plt.Normalize(vmin=0, vmax=1)
    cmap = plt.cm.RdYlGn
    bar_colors = [cmap(norm(float(wr))) for wr in df_show[my_wr_col]]
    bars = ax.bar(range(num_decks), df_show['Encounter Probability'],
                  color=bar_colors, edgecolor='black', linewidth=0.6, alpha=0.92)
    for i, (bar, enc_prob, my_wr, prob_score) in enumerate(zip(
        bars, df_show['Encounter Probability'], df_show[my_wr_col], df_show['Problem Score']
    )):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.018,
               f'{enc_prob:.1%}',
               ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')
        bar_h = bar.get_height()
        if bar_h > 0.07:
            text_y = bar_h / 2
            text_color = 'white' if (float(my_wr) < 0.3 or float(my_wr) > 0.72) else 'black'
            ax.text(bar.get_x() + bar.get_width() / 2, text_y,
                   f'WR: {float(my_wr):.0%}',
                   ha='center', va='center', fontsize=9, fontweight='bold', color=text_color)
    rotation_angle = 30 if num_decks < 12 else 45 if num_decks < 20 else 60
    for i, (deck, perf) in enumerate(zip(df_show['Deck Display Name'], df_show['Performance Label'])):
        ax.text(i, -0.03, deck, ha='right', va='top', fontsize=9, rotation=rotation_angle,
               color=PERFORMANCE_COLORS.get(perf, 'black'))
    ax.tick_params(axis='x', which='both', length=0, labelbottom=False)
    ax.spines['bottom'].set_visible(False)
    ax.set_ylabel('Encounter Probability', fontsize=13)
    ax.set_ylim(0, 1.15)
    title = (
        f'{player_deck_name} Performance vs Metagame - Week {week_num}\n'
        f'Sorted by Problem Score (Encounter Prob x Loss Rate) | N={N_players}'
    )
    ax.set_title(title, fontsize=14, pad=20)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', fraction=0.025, pad=0.02)
    cbar.set_label('My Winrate Against This Deck', fontsize=11)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_ticklabels(['0% (0-X)', '25%', '50%', '75%', '100% (X-0)'])
    perf_patches = [
        Patch(facecolor=PERFORMANCE_COLORS['Underplayed Winner'], label='Underplayed Winner'),
        Patch(facecolor=PERFORMANCE_COLORS['Popular Trap'], label='Popular Trap'),
        Patch(facecolor=PERFORMANCE_COLORS['Neutral'], label='Neutral')
    ]
    ax.legend(handles=perf_patches, title="Deck Performance (meta)", loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.38, right=0.88)
    out_png = os.path.join(output_dir, f'my_deck_performance_W{week_num}.png')
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()
    print(f"Saved: {out_png}  ({len(df_show)} decks with My Deck Winrate data)")
    return out_png

print("\nGenerating My Deck Performance chart (v1.4)...")
my_deck_chart = create_my_deck_performance_chart(
    df_results, week_num, N_players, min_encounter_threshold=min_encounter_threshold,
    player_deck_name=player_deck_name
)

# NEW in v1.4: Record Probability chart
def create_record_probability_chart(player_winrate, df_results, rounds, week_num, player_deck_name="My Deck"):
    player_records = calculate_binomial_records(player_winrate, rounds)
    records_list = list(player_records.keys())
    probs_list = list(player_records.values())
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))
    fig.suptitle(f'Record Probability Analysis - Week {week_num} ({rounds}-round event)', fontsize=15, y=1.01)
    ax1 = axes[0]
    bar_colors_left = plt.cm.RdYlGn(np.linspace(0, 1, len(records_list)))
    bars1 = ax1.bar(records_list, probs_list, color=bar_colors_left, edgecolor='black', linewidth=0.6, alpha=0.9)
    for bar, prob in zip(bars1, probs_list):
        ax1.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f'{prob:.1%}', ha='center', va='bottom', fontsize=11, fontweight='bold'
        )
    ax1.set_xlabel('Record (W-L)', fontsize=12)
    ax1.set_ylabel('Probability', fontsize=12)
    ax1.set_title(
        f'{player_deck_name} Record Distribution\nOverall Winrate: {player_winrate:.1%} | Expected: {player_winrate * rounds:.1f}-{(1 - player_winrate) * rounds:.1f}',
        fontsize=13
    )
    ax1.set_ylim(0, max(probs_list) * 1.25)
    ax1.tick_params(axis='x', labelsize=10)
    best_idx = int(np.argmax(probs_list))
    bars1[best_idx].set_edgecolor('gold')
    bars1[best_idx].set_linewidth(3)
    ax1.text(
        bars1[best_idx].get_x() + bars1[best_idx].get_width() / 2,
        max(probs_list) * 1.15,
        'Most likely', ha='center', fontsize=9, color='goldenrod', fontweight='bold'
    )
    ax2 = axes[1]
    df_sorted = df_results.sort_values('Winrate', ascending=False).head(20).reset_index(drop=True)
    deck_names = df_sorted['Deck Display Name'].tolist()
    deck_winrates = df_sorted['Winrate'].tolist()
    expected_wins = [wr * rounds for wr in deck_winrates]
    norm2 = plt.Normalize(vmin=0, vmax=1)
    bar_colors_right = [plt.cm.RdYlGn(norm2(wr)) for wr in deck_winrates]
    bars2 = ax2.barh(range(len(deck_names)), expected_wins,
                     color=bar_colors_right, edgecolor='black', linewidth=0.5, alpha=0.9)
    ax2.set_yticks(range(len(deck_names)))
    ax2.set_yticklabels(deck_names, fontsize=8)
    ax2.set_xlabel('Expected Wins', fontsize=12)
    ax2.set_title(
        f'Expected Wins per Deck\nBased on deck winrate | {rounds} rounds',
        fontsize=13
    )
    ax2.set_xlim(0, rounds + 0.5)
    ax2.axvline(x=rounds / 2, color='gray', linestyle='--', alpha=0.6, linewidth=1.5, label='50% line')
    ax2.legend(fontsize=9)
    for bar, wr, ew in zip(bars2, deck_winrates, expected_wins):
        ax2.text(
            bar.get_width() + 0.07, bar.get_y() + bar.get_height() / 2,
            f'{wr:.1%}  ({ew:.1f}W)', va='center', fontsize=8
        )
    sm2 = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn, norm=norm2)
    sm2.set_array([])
    cbar2 = plt.colorbar(sm2, ax=ax2, orientation='vertical', fraction=0.025, pad=0.02)
    cbar2.set_label('Deck Winrate', fontsize=10)
    cbar2.set_ticks([0, 0.5, 1.0])
    cbar2.set_ticklabels(['0%', '50%', '100%'])
    plt.tight_layout()
    out_png = os.path.join(output_dir, f'record_probability_W{week_num}.png')
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()
    print(f"Saved: {out_png}")
    return out_png

print("\nGenerating Record Probability chart (v1.4)...")
record_chart = create_record_probability_chart(
    player_overall_winrate, df_results, rounds, week_num, player_deck_name=player_deck_name
)

# NEW in v1.4: Record Probability Excel table
def build_record_probability_excel(df_results, player_winrate, rounds, week_num):
    record_labels = [f"{w}-{rounds-w}" for w in range(rounds, -1, -1)]
    rows = []
    player_row = {'Deck': 'YOU (overall winrate)', 'Meta': '', 'Deck Winrate': f'{player_winrate:.1%}'}
    player_probs = calculate_binomial_records(player_winrate, rounds)
    for label in record_labels:
        player_row[label] = f"{player_probs.get(label, 0):.1%}"
    rows.append(player_row)
    for _, r in df_results.sort_values('Meta', ascending=False).iterrows():
        wr = r.get('Winrate', 0.5)
        if pd.isna(wr):
            wr = 0.5
        deck_probs = calculate_binomial_records(wr, rounds)
        row = {
            'Deck': r.get('Deck Display Name', r.get('Deck', '')),
            'Meta': f"{r['Meta']:.1f}%",
            'Deck Winrate': f'{wr:.1%}'
        }
        for label in record_labels:
            row[label] = f"{deck_probs.get(label, 0):.1%}"
        rows.append(row)
    df_out = pd.DataFrame(rows)
    excel_path = os.path.join(output_dir, f'record_probabilities_W{week_num}.xlsx')
    df_out.to_excel(excel_path, index=False)
    print(f"Saved: {excel_path}")
    return excel_path

print("\nBuilding Record Probability Excel table (v1.4)...")
record_excel = build_record_probability_excel(df_results, player_overall_winrate, rounds, week_num)

# Save standard files
excel_out = os.path.join(output_dir, f'deck_analysis_W{week_num}.xlsx')
csv_out = os.path.join(output_dir, f'Metagame_History_W{week_num}.csv')
arch_excel_out = os.path.join(output_dir, f'deck_analysis_ARCHETYPE_W{week_num}.xlsx')

df_results.to_excel(excel_out, index=False)
df_arch.to_excel(arch_excel_out, index=False)
df_history.to_csv(csv_out, index=False)
print(f"\nSaved: {excel_out}, {arch_excel_out}, {csv_out}")

# Trend charts (if history available)
trend_chart = None
arch_trend_chart = None
unique_weeks = df_history['WeekIndex'].nunique() if len(df_history) > 0 else 0

if unique_weeks > 1:
    try:
        weeks_back = int(input("\nHow many weeks back for trend chart? (default 4): ").strip() or 4)
        weeks_back = max(2, min(weeks_back, int(df_history['WeekIndex'].max())))
    except Exception:
        weeks_back = 4
    print(f"\nGenerating trend chart (last {weeks_back} weeks)...")
    trend_chart = create_trend_chart(df_history, df_results, weeks_back, week_num, chart_type="Deck", output_dir=output_dir)
    print(f"Generating archetype trend chart (last {weeks_back} weeks)...")
    df_arch_for_trends = df_history[df_history['Level'] == 'Archetype'].copy() if 'Level' in df_history.columns else pd.DataFrame()
    if len(df_arch_for_trends) > 0:
        arch_trend_chart = create_trend_chart(df_history, df_arch, weeks_back, week_num, chart_type="Archetype", output_dir=output_dir)
    else:
        print("Info: No archetype history available for trend chart")
    df_results['Trend Status'] = df_results['Deck'].apply(
        lambda d: calculate_deck_trend_status(df_history, d, weeks_back)[0]
    )
    excel_out_trend = os.path.join(output_dir, f'deck_analysis_WITH_TRENDS_W{week_num}.xlsx')
    df_results.to_excel(excel_out_trend, index=False)
    print(f"Saved: {excel_out_trend}")
else:
    print("\nInfo: Trend chart requires at least 2 weeks of history")
    excel_out_trend = None

# Summary
print("\nTop Very High Prep Priority Decks:")
top_df = df_results[df_results['Prep Priority'] == 'Very High Prep Priority'][
    ['Deck Display Name', 'Meta', 'Winrate', 'Encounter Probability', 'Prep Priority']
].head(10)
print(top_df.to_string(index=False))

my_deck_rows = df_results['My Deck Winrate'].notna().sum()
if my_deck_rows > 0:
    print(f"\nMy Deck Winrate: {my_deck_rows} decks with data")
    problem = df_results[df_results['My Deck Winrate'].notna()].copy()
    problem['Problem Score'] = problem['Encounter Probability'] * (1 - problem['My Deck Winrate'])
    problem = problem.sort_values('Problem Score', ascending=False).head(5)
    print("Top 5 matchups to fix (highest Problem Score):")
    for _, row in problem.iterrows():
        print(f"  {row['Deck Display Name']}: encounter {row['Encounter Probability']:.1%}, your WR {row['My Deck Winrate']:.1%}, problem score {row['Problem Score']:.3f}")

print(f"\nRecord probability for {player_overall_winrate:.1%} winrate over {rounds} rounds:")
player_recs = calculate_binomial_records(player_overall_winrate, rounds)
for rec, prob in player_recs.items():
    print(f"  {rec}: {prob:.1%}")

# Package into ZIP
print("\nPreparing ZIP download...")
outputs = [excel_out, csv_out, arch_excel_out, arch_chart, deck_chart, record_excel]
if my_deck_chart:
    outputs.append(my_deck_chart)
if record_chart:
    outputs.append(record_chart)
if trend_chart:
    outputs.append(trend_chart)
if arch_trend_chart:
    outputs.append(arch_trend_chart)
if excel_out_trend:
    outputs.append(excel_out_trend)

existing = [p for p in outputs if p and os.path.exists(p)]

if len(existing) > 1:
    zip_name = f'MTG_Analysis_W{week_num}.zip'
    zip_path = os.path.join(output_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for f in existing:
            zf.write(f)
    print(f"Created: {zip_path}")
else:
    for f in existing:
        print(f"Created: {f}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETED - v1.4")
print("New outputs: my_deck_performance, record_probability chart + Excel")
print("=" * 80)
