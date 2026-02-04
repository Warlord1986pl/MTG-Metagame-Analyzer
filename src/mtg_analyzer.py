# MTG METAGAME ANALYSIS - GOOGLE COLAB
# =====================================
# INSTRUCTIONS:
# 1. Open Google Colab: colab.research.google.com
# 2. Copy this entire file into Colab
# 3. Click "Runtime" → "Run all" (or Ctrl+F9)
# 4. Upload your Excel file when prompted
# 5. Wait for charts and download ZIP results
# =====================================

# Install packages
!pip install mplcursors openpyxl -q

# Imports
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import sys

# =====================================
# HELPER FUNCTIONS
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

def aggregate_by_archetype(df_results):
    """Aggregate deck data by archetype"""
    df = df_results.copy()
    df['Archetype'] = df.get('Archetype', pd.Series()).fillna('Rogue')
    df_arch = (
        df
        .groupby('Archetype', dropna=False)
        .apply(lambda g: pd.Series({
            'Meta': g['Meta'].sum(),
            'Winrate': np.average(g['Winrate'], weights=g['Meta']) if g['Meta'].sum() > 0 else np.nan,
            'My Winrate': (np.average(g['My Winrate'].dropna(), weights=g.loc[g['My Winrate'].notna(), 'Meta'])
                           if g['My Winrate'].notna().any() else pd.NA)
        }))
        .reset_index()
    )
    df_arch['Deck Display Name'] = df_arch['Archetype']
    return df_arch

def calculate_archetype_metrics(df_arch, total_players, sample_size=5):
    """Calculate metrics for archetypes"""
    df = df_arch.copy()
    df['Encounter Copies'] = (total_players * df['Meta'] / 100).round().astype(int)
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

def create_encounter_probability_chart(df_results, week_num, N_players, chart_type="Deck"):
    """Create encounter probability bar chart"""
    plt.figure(figsize=(20, 12))
    df_sorted = df_results.sort_values('Encounter Probability', ascending=False).reset_index(drop=True)
    num_decks = len(df_sorted)
    cmap = plt.cm.rainbow
    bar_colors = cmap(np.linspace(1, 0, num_decks)) if num_decks > 0 else []
    bars = plt.bar(range(num_decks), df_sorted['Encounter Probability'], color=bar_colors, alpha=0.8, edgecolor='black', linewidth=0.5)

    plt.ylabel('Encounter Probability', fontsize=14)
    plt.title(f'Encounter Probability ({chart_type}) (N={N_players}) - Week {week_num}', fontsize=16, pad=20)
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
    out_png = f'encounter_prob_{chart_type}_W{week_num}.png'
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()

    my_wr_count = df_sorted.get('My Winrate', pd.Series()).notna().sum()
    if my_wr_count > 0:
        print(f"ℹ {my_wr_count} decks use My Winrate (marked with *)")
    return out_png

def calculate_deck_trend_status(df_history, deck_name, weeks_back=4):
    """Calculate deck trend status"""
    deck_history = df_history[df_history['Deck'] == deck_name].sort_values('WeekIndex')
    
    if len(deck_history) < 2:
        return 'Stable', TREND_COLORS['Stable']
    
    recent = deck_history.tail(weeks_back)
    
    if len(recent) < 2:
        return 'Stable', TREND_COLORS['Stable']
    
    weeks = recent['WeekIndex'].values
    meta_values = recent['Meta'].values
    trend_change = meta_values[-1] - meta_values[0]
    threshold = 0.5
    
    if trend_change > threshold:
        return 'Rising', TREND_COLORS['Rising Deck']
    elif trend_change < -threshold:
        return 'Falling', TREND_COLORS['Falling Deck']
    else:
        return 'Stable', TREND_COLORS['Stable']

def create_trend_chart(df_history, df_results, weeks_back, week_num, chart_type="Deck"):
    """Create trend chart - FIXED (clean legend, reversed colors)"""
    if len(df_history) == 0:
        print("ℹ No history data available for trend chart")
        return None
    
    selected_decks = df_results.nlargest(10, 'Meta')['Deck'].tolist()
    deck_display_names = df_results.nlargest(10, 'Meta').set_index('Deck')['Deck Display Name'].to_dict()
    
    if not selected_decks:
        print("ℹ No decks available for trend chart")
        return None
    
    df_trend = df_history[df_history['Deck'].isin(selected_decks)].copy()
    max_week = df_trend['WeekIndex'].max()
    min_week = max(1, max_week - weeks_back + 1)
    df_trend = df_trend[(df_trend['WeekIndex'] >= min_week) & (df_trend['WeekIndex'] <= max_week)]
    
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
            trend_status, _ = calculate_deck_trend_status(df_history, deck, weeks_back)
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
    
    out_png = f'meta_trend_{chart_type}_W{week_num}_last{weeks_back}w.png'
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"✅ Trend chart saved: {out_png}")
    return out_png

def analyze_metagame(filename_excel, history_csv=None, total_encounter_players=1000):
    """Main metagame analysis function"""
    try:
        df_new = pd.read_excel(filename_excel)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise

    if 'My Winrate' not in df_new.columns:
        df_new['My Winrate'] = pd.NA
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

    this_week_idx = int(df_history['WeekIndex'].max()) + 1 if (len(df_history) > 0 and 'WeekIndex' in df_history.columns) else 1
    print(f"✓ Week: {this_week_idx}")

    df_new['WeekIndex'] = this_week_idx
    df_new['Deck Display Name'] = df_new['Deck'].astype(str).str.replace(r'[\[\]□■▪•]', '', regex=True).str.strip()

    total_players = total_encounter_players
    df_new['Encounter Copies'] = (total_players * df_new['Meta'] / 100).round().astype(int)
    df_new['Encounter Probability'] = df_new.apply(
        lambda r: hypergeometric_probability(total_players, int(r['Encounter Copies']), 5, 1), axis=1
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
        df_new['Trend Label'] = df_new.apply(lambda r: trend_label(r['Meta'], trend_meta.get(r['Deck'], r['Meta'])), axis=1)
    else:
        df_new['Trend Label'] = 'Stable'

    def pillar_flag(deck):
        if len(df_history) == 0 or 'Deck' not in df_history.columns:
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

    print("✅ Analysis complete!")
    return df_new, df_history, this_week_idx, total_players

# =====================================
# PROGRAM EXECUTION
# =====================================

from google.colab import files
import zipfile
import os

print("\n" + "="*80)
print("MTG METAGAME ANALYSIS - START")
print("="*80 + "\n")

# Upload Excel file
print("📁 Upload Excel file (columns: Deck, Meta, Winrate):")
uploaded = files.upload()

if not uploaded:
    print("❌ No file uploaded. Exiting.")
    sys.exit(1)

excel_file = list(uploaded.keys())[0]
print(f"✓ Loaded: {excel_file}\n")

# Upload history file (optional)
print("📁 (OPTIONAL) Upload CSV history file:")
print("   If you don't have history, just click 'Cancel' below.\n")
try:
    uploaded_hist = files.upload()
    history_csv = list(uploaded_hist.keys())[0] if uploaded_hist else None
    if history_csv:
        print(f"✓ History loaded: {history_csv}\n")
except Exception:
    uploaded_hist = {}
    history_csv = None
    print("ℹ Continuing without history\n")

# Player count
try:
    N_players = int(input("Player count for calculations (default 1000): ").strip() or 1000)
except Exception:
    N_players = 1000

print(f"\n🔄 Starting analysis (N={N_players} players)...\n")

# Run analysis
df_results, df_history, week_num, N_players = analyze_metagame(excel_file, history_csv, N_players)

print(f"\n✓ History: {df_history.shape[0]} rows, {df_history['WeekIndex'].nunique()} weeks")

# Generate archetype charts
print("\n📊 Generating archetype charts...")
df_arch = aggregate_by_archetype(df_results)
df_arch = calculate_archetype_metrics(df_arch, N_players)
arch_chart = create_encounter_probability_chart(df_arch, week_num, N_players, chart_type="Archetype")

# Generate deck charts
print("\n📊 Generating deck charts...")
deck_chart = create_encounter_probability_chart(df_results, week_num, N_players, chart_type="Deck")

# Prepare data for export
df_arch['Level'] = 'Archetype'
df_arch['Deck'] = df_arch['Archetype']

arch_cols_to_keep = ['Archetype', 'Meta', 'Winrate', 'My Winrate', 'WeekIndex', 'Importance', 
                     'Quartile', 'Prep Priority', 'Performance Label', 'Level', 'Deck']
df_arch_for_history = df_arch[[col for col in arch_cols_to_keep if col in df_arch.columns]].copy()

df_history_combined = pd.concat([df_history, df_arch_for_history], ignore_index=True)

# Save files
excel_out = f'deck_analysis_W{week_num}.xlsx'
csv_out = f'Metagame_History_W{week_num}.csv'
arch_excel_out = f'deck_analysis_ARCHETYPE_W{week_num}.xlsx'

df_results.to_excel(excel_out, index=False)
df_arch.to_excel(arch_excel_out, index=False)
df_history_combined.to_csv(csv_out, index=False)

print(f"\n💾 Saved: {excel_out}, {arch_excel_out}, {csv_out}")

# Trend chart (if history available)
trend_chart = None
unique_weeks = df_history['WeekIndex'].nunique() if len(df_history) > 0 else 0

if unique_weeks > 1:
    try:
        weeks_back = int(input("\n📈 How many weeks back for trend chart? (default 4): ").strip() or 4)
        weeks_back = max(2, min(weeks_back, int(df_history['WeekIndex'].max())))
    except Exception:
        weeks_back = 4
    
    print(f"\n📊 Generating trend chart (last {weeks_back} weeks)...")
    trend_chart = create_trend_chart(df_history, df_results, weeks_back, week_num, chart_type="Deck")
    
    df_results['Trend Status'] = df_results['Deck'].apply(
        lambda d: calculate_deck_trend_status(df_history, d, weeks_back)[0]
    )
    
    excel_out_trend = f'deck_analysis_WITH_TRENDS_W{week_num}.xlsx'
    df_results.to_excel(excel_out_trend, index=False)
    print(f"💾 Saved: {excel_out_trend}")
else:
    print("\nℹ Trend chart requires at least 2 weeks of history")

# Show top decks
print("\n📊 TOP Very High Prep Priority Decks:")
top_df = df_results[df_results['Prep Priority'] == 'Very High Prep Priority'][
    ['Deck Display Name', 'Meta', 'Winrate', 'Encounter Probability', 'Prep Priority']
].head(10)
display(top_df)

print(f"\n📈 Encounter probability range (N={N_players}): {df_results['Encounter Probability'].min():.1%} - {df_results['Encounter Probability'].max():.1%}")

# Download all files as ZIP
print("\n📦 Preparing files for download...")
outputs = [excel_out, csv_out, arch_excel_out, arch_chart, deck_chart]
if trend_chart:
    outputs.append(trend_chart)
    outputs.append(excel_out_trend)

existing = [p for p in outputs if os.path.exists(p)]

if len(existing) > 1:
    zip_name = f'MTG_Analysis_W{week_num}.zip'
    with zipfile.ZipFile(zip_name, 'w') as zf:
        for file in existing:
            zf.write(file)
    print(f"✅ Downloading: {zip_name}")
    files.download(zip_name)
else:
    for file in existing:
        print(f"✅ Downloading: {file}")
        files.download(file)

print("\n" + "="*80)
print("✅ ANALYSIS COMPLETED SUCCESSFULLY!")
print("="*80)
