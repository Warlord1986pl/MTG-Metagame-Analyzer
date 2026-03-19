import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd
from openpyxl.styles import PatternFill


API_BASE = "https://api.videreproject.com"


@dataclass
class ArchetypeRule:
    pattern: str
    archetype: str
    match_type: str = "contains"
    priority: int = 100


@dataclass
class DeckAliasRule:
    pattern: str
    canonical_name: str
    match_type: str = "contains"
    priority: int = 100


@dataclass
class UserDeckMapping:
    raw_name: str
    canonical_name: str
    archetype: str


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def latest_sunday(reference: date) -> date:
    days_since_sunday = (reference.weekday() + 1) % 7
    return reference - timedelta(days=days_since_sunday)


def parse_percent(value, decimal: bool) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        number = float(value)
    else:
        text = str(value).strip().replace("%", "").replace(",", ".")
        if text == "":
            return None
        try:
            number = float(text)
        except ValueError:
            return None

    if decimal:
        if number > 1:
            return number / 100.0
        return number
    return number


def parse_count(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return max(0, int(value))

    text = str(value).strip().replace(",", "")
    if text == "":
        return 0
    try:
        return max(0, int(float(text)))
    except ValueError:
        return 0


def api_get(endpoint: str, params: Dict[str, object]) -> Dict[str, object]:
    qs = urlencode(params)
    url = f"{API_BASE}/{endpoint}?{qs}"
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "MTG-Metagame-Analyzer/1.0 (+https://github.com)",
        },
    )
    with urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip()).lower()


def load_rules(path: Path) -> List[ArchetypeRule]:
    if not path.exists():
        return []

    rules: List[ArchetypeRule] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pattern = (row.get("pattern") or "").strip()
            archetype = (row.get("archetype") or "").strip()
            if not pattern or not archetype:
                continue
            rules.append(
                ArchetypeRule(
                    pattern=pattern,
                    archetype=archetype,
                    match_type=(row.get("match_type") or "contains").strip().lower(),
                    priority=int((row.get("priority") or "100").strip()),
                )
            )
    return sorted(rules, key=lambda rule: rule.priority)


def load_aliases(path: Path) -> List[DeckAliasRule]:
    if not path.exists():
        return []

    aliases: List[DeckAliasRule] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pattern = (row.get("pattern") or "").strip()
            canonical_name = (row.get("canonical_name") or "").strip()
            if not pattern or not canonical_name:
                continue
            aliases.append(
                DeckAliasRule(
                    pattern=pattern,
                    canonical_name=canonical_name,
                    match_type=(row.get("match_type") or "contains").strip().lower(),
                    priority=int((row.get("priority") or "100").strip()),
                )
            )
    return sorted(aliases, key=lambda alias: alias.priority)


def load_user_deck_mappings(path: Path) -> List[UserDeckMapping]:
    if not path.exists():
        return []

    mappings: List[UserDeckMapping] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_name = (row.get("raw_name") or "").strip()
            canonical_name = (row.get("canonical_name") or "").strip()
            archetype = (row.get("archetype") or "").strip()
            if not raw_name or not canonical_name:
                continue
            mappings.append(
                UserDeckMapping(
                    raw_name=raw_name,
                    canonical_name=canonical_name,
                    archetype=archetype,
                )
            )
    return mappings


def mapping_lookup(mappings: List[UserDeckMapping]) -> Dict[str, UserDeckMapping]:
    return {normalize_name(m.raw_name): m for m in mappings}


def canonicalize_deck_name(deck_name: str, aliases: Iterable[DeckAliasRule]) -> str:
    base_name = re.sub(r"\s+", " ", str(deck_name).strip())
    base_name = re.sub(r"(?i)generic", " ", base_name)
    base_name = re.sub(r"\s+", " ", base_name).strip()
    deck_norm = normalize_name(base_name)

    for alias in aliases:
        pattern = alias.pattern
        mtype = alias.match_type

        if mtype == "exact" and deck_norm == normalize_name(pattern):
            return alias.canonical_name
        if mtype == "contains" and normalize_name(pattern) in deck_norm:
            return alias.canonical_name
        if mtype == "regex" and re.search(pattern, base_name, flags=re.IGNORECASE):
            return alias.canonical_name

    if "prowess" in deck_norm:
        return "Prowess"

    return base_name


def heuristic_archetype(deck_name: str) -> str:
    normalized = normalize_name(deck_name)
    patterns = [
        (r"\b(burn|zoo|prowess|aggro|humans|goblins|elves|merfolk|infect|affinity|hammer)\b", "Aggro"),
        (r"\b(midrange|rock|jund|abzan|grixis midrange|golgari)\b", "Midrange"),
        (r"\b(control|azorius|jeskai control|dimir control|uw control|esper control)\b", "Control"),
        (r"\b(combo|storm|belcher|twin|neoform|oops|creativity|ad nauseam|yawgmoth|amulet)\b", "Combo"),
        (r"\b(ramp|tron|titan|eldrazi ramp|scapeshift)\b", "Ramp"),
        (r"\b(tempo|delver|murktide)\b", "Tempo"),
        (r"\b(prison|lantern|lock)\b", "Prison"),
        (r"\b(reanimator|goryo|living end|dredge)\b", "Graveyard"),
    ]
    for pattern, archetype in patterns:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return archetype
    return "Unknown"


def classify_archetype(deck_name: str, rules: Iterable[ArchetypeRule]) -> str:
    deck_norm = normalize_name(deck_name)
    for rule in rules:
        pattern = rule.pattern
        mtype = rule.match_type

        if mtype == "exact" and deck_norm == normalize_name(pattern):
            return rule.archetype
        if mtype == "contains" and normalize_name(pattern) in deck_norm:
            return rule.archetype
        if mtype == "regex" and re.search(pattern, deck_name, flags=re.IGNORECASE):
            return rule.archetype

    return heuristic_archetype(deck_name)


def normalize_archetype_label(archetype: str) -> str:
    text = str(archetype or "").strip()
    if normalize_name(text) == "reanimator":
        return "Graveyard"
    return text if text else "Unknown"


def is_code_like_deck_name(deck_name: str) -> bool:
    text = str(deck_name or "").strip()
    if text == "":
        return False
    if re.fullmatch(r"[A-Z]{1,5}", text):
        return True
    norm = normalize_name(text)
    if re.fullmatch(r"[wubrg]{1,5}", norm):
        return True
    return False


def apply_archetype_overrides(raw_deck_name: str, deck_name: str, meta_share: Optional[float], archetype: str) -> str:
    raw_norm = normalize_name(raw_deck_name)
    deck_norm = normalize_name(deck_name)

    if raw_norm == "sultai midrange" or deck_norm == "sultai midrange":
        return "Midrange"

    return archetype


def extract_my_deck_matchups(
    format_name: str,
    my_deck: str,
    start_date: date,
    end_date: date,
    limit: int,
    aliases: List[DeckAliasRule],
) -> Dict[str, tuple[float, int]]:
    payload = api_get(
        "matchups",
        {
            "format": format_name,
            "min_date": start_date.isoformat(),
            "max_date": end_date.isoformat(),
            "limit": limit,
        },
    )

    data = payload.get("data") or []
    if not isinstance(data, list):
        return {}

    my_canonical = canonicalize_deck_name(my_deck, aliases)
    my_norm = normalize_name(my_canonical)
    exact = None
    contains = None

    for row in data:
        archetype = row.get("archetype")
        if not archetype:
            continue
        row_canonical = canonicalize_deck_name(str(archetype), aliases)
        row_norm = normalize_name(row_canonical)
        if row_norm == my_norm:
            exact = row
            break
        if my_norm in row_norm or row_norm in my_norm:
            contains = row

    selected = exact or contains
    if not selected:
        return {}

    grouped_wr: Dict[str, List[tuple[float, int]]] = defaultdict(list)
    for matchup in selected.get("matchups", []):
        opponent = matchup.get("archetype")
        if not opponent:
            continue
        opponent_canonical = canonicalize_deck_name(str(opponent), aliases)
        wr = parse_percent(matchup.get("game_winrate"), decimal=True)
        if wr is None:
            continue
        games = parse_count(matchup.get("game_count"))
        grouped_wr[normalize_name(opponent_canonical)].append((wr, games))

    # If multiple source matchups collapse into one canonical deck family
    # (e.g. Izzet Prowess + Izzet Steel-Cutter -> Prowess), use their mean.
    out: Dict[str, tuple[float, int]] = {}
    for opponent_norm, wr_values in grouped_wr.items():
        total_games = sum(g for _, g in wr_values)
        if total_games > 0:
            weighted_wr = sum(wr * g for wr, g in wr_values) / total_games
            out[opponent_norm] = (float(weighted_wr), int(total_games))
        else:
            out[opponent_norm] = (float(sum(wr for wr, _ in wr_values) / len(wr_values)), 0)
    return out


def build_dataset(
    format_name: str,
    week_start: date,
    week_end: date,
    my_deck: str,
    my_window_days: int,
    my_fallback_window_days: int,
    rogue_threshold: float,
    rules: List[ArchetypeRule],
    aliases: List[DeckAliasRule],
    user_mapping: Dict[str, UserDeckMapping],
    metagame_limit: int,
    matchup_limit: int,
) -> tuple[pd.DataFrame, int, Dict[str, int]]:
    metagame_payload = api_get(
        "metagame",
        {
            "format": format_name,
            "min_date": week_start.isoformat(),
            "max_date": week_end.isoformat(),
            "limit": metagame_limit,
        },
    )
    metagame_data = metagame_payload.get("data") or []
    if not isinstance(metagame_data, list) or not metagame_data:
        raise RuntimeError("Brak danych metagame dla zadanego tygodnia.")

    my_start = week_end - timedelta(days=max(1, my_window_days))
    my_wr_primary = extract_my_deck_matchups(
        format_name=format_name,
        my_deck=my_deck,
        start_date=my_start,
        end_date=week_end,
        limit=matchup_limit,
        aliases=aliases,
    )

    my_wr_fallback: Dict[str, tuple[float, int]] = {}
    if my_fallback_window_days > my_window_days:
        fallback_start = week_end - timedelta(days=max(1, my_fallback_window_days))
        my_wr_fallback = extract_my_deck_matchups(
            format_name=format_name,
            my_deck=my_deck,
            start_date=fallback_start,
            end_date=week_end,
            limit=matchup_limit,
            aliases=aliases,
        )

    rows = []
    mapped_from_user = 0
    for entry in metagame_data:
        raw_deck_name = str(entry.get("archetype") or "").strip()
        user_map = user_mapping.get(normalize_name(raw_deck_name))
        if user_map:
            mapped_from_user += 1

        canonical_source = user_map.canonical_name if user_map else raw_deck_name
        deck_name = canonicalize_deck_name(canonical_source, aliases)
        if not deck_name:
            continue

        meta_share = parse_percent(entry.get("percentage"), decimal=False)
        winrate = parse_percent(entry.get("game_winrate"), decimal=True)
        archetype_raw = user_map.archetype if (user_map and user_map.archetype) else classify_archetype(deck_name, rules)
        archetype = normalize_archetype_label(archetype_raw)
        archetype = apply_archetype_overrides(raw_deck_name, deck_name, meta_share, archetype)

        deck_lookup_name = deck_name
        if meta_share is not None and meta_share < rogue_threshold:
            deck_name = "Rogue"
            archetype = "Rogue"

        deck_norm = normalize_name(deck_lookup_name)
        if deck_norm in my_wr_primary:
            my_wr, my_wr_games = my_wr_primary[deck_norm]
            my_wr_source = "primary"
        elif deck_norm in my_wr_fallback:
            my_wr, my_wr_games = my_wr_fallback[deck_norm]
            my_wr_source = "fallback"
        else:
            my_wr = pd.NA
            my_wr_games = 0
            my_wr_source = "none"

        rows.append(
            {
                "Raw Deck": raw_deck_name,
                "Deck": deck_name,
                "Meta": meta_share,
                "Winrate": winrate,
                "Winrate Game Count": parse_count(entry.get("game_count")),
                "Archetype": archetype,
                "My Deck Winrate": my_wr,
                "My Deck Winrate Game Count": my_wr_games,
                "My Deck Winrate Source": my_wr_source,
            }
        )

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["Deck", "Meta", "Winrate"]).copy()

    def merge_archetype(series: pd.Series) -> str:
        known = [
            normalize_archetype_label(s)
            for s in series.astype(str).tolist()
            if s and normalize_archetype_label(s) != "Unknown"
        ]
        return known[0] if known else "Unknown"

    def merge_my_wr(series: pd.Series, meta_series: pd.Series):
        mask = pd.Series(series).notna()
        if not mask.any():
            return pd.NA
        wr_valid = pd.Series(series)[mask].astype(float)
        meta_valid = pd.Series(meta_series)[mask].astype(float)
        total_meta = meta_valid.sum()
        if total_meta > 0:
            return (wr_valid * meta_valid).sum() / total_meta
        return wr_valid.mean()

    def merge_my_wr_source(series: pd.Series) -> str:
        values = [str(v) for v in series.astype(str).tolist() if v]
        if any(v == "primary" for v in values):
            return "primary"
        if any(v == "fallback" for v in values):
            return "fallback"
        return "none"

    def merge_count(series: pd.Series) -> int:
        return int(pd.to_numeric(series, errors="coerce").fillna(0).sum())

    aggregated = (
        df.groupby("Deck", as_index=False)
        .apply(
            lambda g: pd.Series(
                {
                    "Source Deck Names": " | ".join(sorted(set(g["Raw Deck"].astype(str).tolist()))),
                    "Meta": g["Meta"].sum(),
                    "Winrate": (g["Winrate"] * g["Meta"]).sum() / g["Meta"].sum() if g["Meta"].sum() > 0 else g["Winrate"].mean(),
                    "Winrate Game Count": merge_count(g["Winrate Game Count"]),
                    "Archetype": merge_archetype(g["Archetype"]),
                    "My Deck Winrate": merge_my_wr(g["My Deck Winrate"], g["Meta"]),
                    "My Deck Winrate Game Count": merge_count(g["My Deck Winrate Game Count"]),
                    "My Deck Winrate Source": merge_my_wr_source(g["My Deck Winrate Source"]),
                }
            )
        )
        .reset_index(drop=True)
    )

    df = aggregated[
        [
            "Deck",
            "Source Deck Names",
            "Meta",
            "Winrate",
            "Winrate Game Count",
            "Archetype",
            "My Deck Winrate",
            "My Deck Winrate Game Count",
        ]
    ].copy()
    df["Archetype"] = df["Archetype"].apply(normalize_archetype_label)
    source = aggregated["My Deck Winrate Source"].copy()
    df["My Deck Winrate Fallback180"] = source.eq("fallback")
    df["My Deck Winrate Imputed"] = source.eq("none")
    df.loc[df["My Deck Winrate Imputed"], "My Deck Winrate"] = 0.5
    df = df.sort_values("Meta", ascending=False).reset_index(drop=True)
    source = source.loc[df.index]
    stats = {
        "primary": int(source.eq("primary").sum()),
        "fallback": int(source.eq("fallback").sum()),
        "imputed": int(source.eq("none").sum()),
    }
    return df, mapped_from_user, stats


def _fallback_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def _safe_to_csv(df: pd.DataFrame, path: Path) -> Path:
    final_path = path
    try:
        df.to_csv(final_path, index=False, encoding="utf-8")
    except PermissionError:
        final_path = _fallback_path(path)
        df.to_csv(final_path, index=False, encoding="utf-8")
    return final_path


def export_outputs(df: pd.DataFrame, output_csv: Path, output_xlsx: Path) -> tuple[Path, Path]:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    export_df = df.drop(columns=["My Deck Winrate Imputed", "My Deck Winrate Fallback180"], errors="ignore")
    imputed_flags = df.get("My Deck Winrate Imputed", pd.Series([False] * len(df))).astype(bool).tolist()
    fallback180_flags = df.get("My Deck Winrate Fallback180", pd.Series([False] * len(df))).astype(bool).tolist()

    final_csv = output_csv
    final_xlsx = output_xlsx

    try:
        final_csv = _safe_to_csv(export_df, final_csv)
    except Exception:
        raise

    yellow_fill = PatternFill(fill_type="solid", start_color="FFF59D", end_color="FFF59D")
    green_fill = PatternFill(fill_type="solid", start_color="C8E6C9", end_color="C8E6C9")
    wr_col_idx = export_df.columns.get_loc("My Deck Winrate") + 1

    try:
        with pd.ExcelWriter(final_xlsx, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False)
            ws = writer.sheets["Sheet1"]
            for row_idx, is_imputed in enumerate(imputed_flags, start=2):
                if is_imputed:
                    ws.cell(row=row_idx, column=wr_col_idx).fill = yellow_fill
            for row_idx, is_fallback in enumerate(fallback180_flags, start=2):
                if is_fallback:
                    ws.cell(row=row_idx, column=wr_col_idx).fill = green_fill
    except PermissionError:
        final_xlsx = _fallback_path(output_xlsx)
        with pd.ExcelWriter(final_xlsx, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False)
            ws = writer.sheets["Sheet1"]
            for row_idx, is_imputed in enumerate(imputed_flags, start=2):
                if is_imputed:
                    ws.cell(row=row_idx, column=wr_col_idx).fill = yellow_fill
            for row_idx, is_fallback in enumerate(fallback180_flags, start=2):
                if is_fallback:
                    ws.cell(row=row_idx, column=wr_col_idx).fill = green_fill

    return final_csv, final_xlsx


def aggregate_rogue_bucket(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "Archetype" not in out.columns:
        return out

    archetype_series = out["Archetype"].fillna("").astype(str).str.strip().str.lower()
    rogue_mask = archetype_series.isin({"rogue", "other"})
    if not rogue_mask.any():
        return out

    rogue_rows = out.loc[rogue_mask].copy()
    keep_rows = out.loc[~rogue_mask].copy()

    meta_sum = float(pd.to_numeric(rogue_rows["Meta"], errors="coerce").fillna(0).sum())
    winrate_vals = pd.to_numeric(rogue_rows["Winrate"], errors="coerce")
    meta_vals = pd.to_numeric(rogue_rows["Meta"], errors="coerce").fillna(0)
    if meta_sum > 0:
        winrate_agg = float((winrate_vals.fillna(0) * meta_vals).sum() / meta_sum)
    else:
        winrate_agg = float(winrate_vals.dropna().mean()) if winrate_vals.notna().any() else 0.5

    my_wr_vals = pd.to_numeric(rogue_rows["My Deck Winrate"], errors="coerce")
    my_wr_mask = my_wr_vals.notna()
    if my_wr_mask.any():
        my_meta = meta_vals[my_wr_mask]
        if my_meta.sum() > 0:
            my_wr_agg = float((my_wr_vals[my_wr_mask] * my_meta).sum() / my_meta.sum())
        else:
            my_wr_agg = float(my_wr_vals[my_wr_mask].mean())
    else:
        my_wr_agg = 0.5

    source_names = sorted(
        set(rogue_rows["Source Deck Names"].dropna().astype(str).tolist())
        | set(rogue_rows["Deck"].dropna().astype(str).tolist())
    )

    rogue_row = {
        "Deck": "Rogue",
        "Source Deck Names": " | ".join(source_names),
        "Meta": meta_sum,
        "Winrate": winrate_agg,
        "Winrate Game Count": int(pd.to_numeric(rogue_rows["Winrate Game Count"], errors="coerce").fillna(0).sum()),
        "Archetype": "Rogue",
        "My Deck Winrate": my_wr_agg,
        "My Deck Winrate Game Count": int(pd.to_numeric(rogue_rows["My Deck Winrate Game Count"], errors="coerce").fillna(0).sum()),
        "My Deck Winrate Fallback180": bool(rogue_rows.get("My Deck Winrate Fallback180", pd.Series(dtype=bool)).fillna(False).any()),
        "My Deck Winrate Imputed": bool(rogue_rows.get("My Deck Winrate Imputed", pd.Series(dtype=bool)).fillna(False).any()),
    }

    combined = pd.concat([keep_rows, pd.DataFrame([rogue_row])], ignore_index=True)
    combined = combined.sort_values("Meta", ascending=False).reset_index(drop=True)
    return combined


def export_unknown_archetypes(df: pd.DataFrame, path: Path) -> Path:
    unknown = df[df["Archetype"] == "Unknown"][["Deck", "Source Deck Names"]].drop_duplicates().sort_values("Deck")
    path.parent.mkdir(parents=True, exist_ok=True)
    if len(unknown) == 0:
        return _safe_to_csv(pd.DataFrame(columns=["Deck", "Source Deck Names", "Suggested Archetype"]), path)
    unknown = unknown.assign(**{"Suggested Archetype": ""})
    return _safe_to_csv(unknown, path)


def export_alias_suggestions(df: pd.DataFrame, aliases: List[DeckAliasRule], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    unknown = df[df["Archetype"] == "Unknown"].copy()
    if len(unknown) == 0:
        return _safe_to_csv(
            pd.DataFrame(columns=["Deck", "Suggested Canonical Name", "Confidence", "Reason"]),
            path,
        )

    canonical_pool = sorted(set([a.canonical_name for a in aliases] + df[df["Archetype"] != "Unknown"]["Deck"].astype(str).tolist()))
    results = []

    for deck in unknown["Deck"].astype(str).tolist():
        norm = normalize_name(deck)
        if re.fullmatch(r"[wubrg]{1,5}", norm):
            results.append(
                {
                    "Deck": deck,
                    "Suggested Canonical Name": "",
                    "Confidence": 0.0,
                    "Reason": "Color code placeholder (manual decision)",
                }
            )
            continue

        match = difflib.get_close_matches(deck, canonical_pool, n=1, cutoff=0.74)
        if not match:
            results.append(
                {
                    "Deck": deck,
                    "Suggested Canonical Name": "",
                    "Confidence": 0.0,
                    "Reason": "No close canonical match",
                }
            )
            continue

        candidate = match[0]
        confidence = difflib.SequenceMatcher(a=normalize_name(deck), b=normalize_name(candidate)).ratio()
        results.append(
            {
                "Deck": deck,
                "Suggested Canonical Name": candidate,
                "Confidence": round(confidence, 3),
                "Reason": "Name similarity",
            }
        )

    result_df = pd.DataFrame(results).sort_values(["Confidence", "Deck"], ascending=[False, True])
    return _safe_to_csv(result_df, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Buduje plik wejściowy do MTG-Metagame-Analyzer: tygodniowy metagame + "
            "My Deck Winrate z dłuższego okna matchupów (np. Domain Zoo)."
        )
    )
    parser.add_argument("--format", dest="format_name", default="Modern")
    parser.add_argument("--week-start", help="YYYY-MM-DD (tryb ręczny)")
    parser.add_argument("--week-end", help="YYYY-MM-DD (tryb ręczny)")
    parser.add_argument("--metagame-window-days", type=int, default=14, help="okno metagame, domyślnie 14 dni")
    parser.add_argument("--history-points", type=int, default=1, help="ile kolejnych punktów tygodniowych wygenerować")
    parser.add_argument("--anchor-sunday", help="YYYY-MM-DD, domyślnie ostatnia niedziela")
    parser.add_argument("--history-output-dir", default="outputs/history", help="katalog na serię snapshotów")
    parser.add_argument("--my-deck", default="Domain Zoo")
    parser.add_argument("--my-window-days", type=int, default=90, help="np. 30 lub 90")
    parser.add_argument("--my-fallback-window-days", type=int, default=180, help="okno fallback dla brakow, np. 180")
    parser.add_argument("--rogue-threshold", type=float, default=0.5, help="próg Meta (%) poniżej którego deck wpada do Rogue")
    parser.add_argument("--metagame-limit", type=int, default=64)
    parser.add_argument("--matchup-limit", type=int, default=300)
    parser.add_argument(
        "--rules-file",
        default="docs/archetype_rules.csv",
        help="CSV z regułami mapowania archetypów",
    )
    parser.add_argument(
        "--aliases-file",
        default="docs/deck_aliases.csv",
        help="CSV z aliasami nazw decków do nazw kanonicznych",
    )
    parser.add_argument(
        "--user-mapping-file",
        default="docs/user_deck_mapping.csv",
        help="Twoj plik mapowan: raw_name, canonical_name, archetype",
    )
    parser.add_argument(
        "--output-csv",
        default="outputs/metagame_input.csv",
    )
    parser.add_argument(
        "--output-xlsx",
        default="outputs/metagame_input.xlsx",
    )
    parser.add_argument(
        "--output-csv-rogue-grouped",
        default="outputs/metagame_input_rogue_grouped.csv",
    )
    parser.add_argument(
        "--output-xlsx-rogue-grouped",
        default="outputs/metagame_input_rogue_grouped.xlsx",
    )
    parser.add_argument(
        "--unknown-output",
        default="outputs/unknown_archetypes.csv",
    )
    parser.add_argument(
        "--alias-suggestions-output",
        default="outputs/alias_suggestions.csv",
    )
    return parser.parse_args()


def resolve_windows(args: argparse.Namespace) -> List[tuple[date, date]]:
    if args.history_points < 1:
        raise ValueError("history-points musi być >= 1")

    if args.week_start or args.week_end:
        if not (args.week_start and args.week_end):
            raise ValueError("Podaj oba parametry: --week-start i --week-end")
        start = parse_date(args.week_start)
        end = parse_date(args.week_end)
        if end < start:
            raise ValueError("week-end musi być >= week-start")
        return [(start, end)]

    anchor = parse_date(args.anchor_sunday) if args.anchor_sunday else latest_sunday(date.today())
    windows: List[tuple[date, date]] = []
    for i in range(args.history_points):
        weeks_back = args.history_points - 1 - i
        end = anchor - timedelta(days=7 * weeks_back)
        start = end - timedelta(days=max(1, args.metagame_window_days) - 1)
        windows.append((start, end))
    return windows


def main() -> None:
    args = parse_args()
    windows = resolve_windows(args)

    rules = load_rules(Path(args.rules_file))
    aliases = load_aliases(Path(args.aliases_file))
    user_mappings = load_user_deck_mappings(Path(args.user_mapping_file))
    user_mapping = mapping_lookup(user_mappings)
    history_mode = len(windows) > 1
    history_output_dir = Path(args.history_output_dir)

    print(f"✅ User mapping rows loaded: {len(user_mappings)}")
    for idx, (week_start, week_end) in enumerate(windows, start=1):
        dataset, mapped_from_user, my_wr_stats = build_dataset(
            format_name=args.format_name,
            week_start=week_start,
            week_end=week_end,
            my_deck=args.my_deck,
            my_window_days=args.my_window_days,
            my_fallback_window_days=args.my_fallback_window_days,
            rogue_threshold=args.rogue_threshold,
            rules=rules,
            aliases=aliases,
            user_mapping=user_mapping,
            metagame_limit=args.metagame_limit,
            matchup_limit=args.matchup_limit,
        )

        if history_mode:
            history_output_dir.mkdir(parents=True, exist_ok=True)
            range_dir = history_output_dir / f"{week_start.isoformat()}_to_{week_end.isoformat()}"
            range_dir.mkdir(parents=True, exist_ok=True)
            output_csv = range_dir / "metagame_input.csv"
            output_xlsx = range_dir / "metagame_input.xlsx"
            final_csv, final_xlsx = export_outputs(dataset, output_csv=output_csv, output_xlsx=output_xlsx)
            grouped = aggregate_rogue_bucket(dataset)
            grouped_csv = range_dir / "metagame_input_rogue_grouped.csv"
            grouped_xlsx = range_dir / "metagame_input_rogue_grouped.xlsx"
            grouped_final_csv, grouped_final_xlsx = export_outputs(grouped, output_csv=grouped_csv, output_xlsx=grouped_xlsx)
            print(
                f"✅ P{idx} {week_start.isoformat()}..{week_end.isoformat()} | "
                f"rows={len(dataset)} | primary={my_wr_stats['primary']} | "
                f"180d={my_wr_stats['fallback']} | 50%={my_wr_stats['imputed']}"
            )
            print(f"✅ Rogue threshold: Meta < {args.rogue_threshold}%")
            print(f"✅ Dir: {range_dir}")
            print(f"✅ Files: {final_xlsx}")
            print(f"✅ Files (Rogue grouped): {grouped_final_xlsx}")
            continue

        output_csv = Path(args.output_csv)
        output_xlsx = Path(args.output_xlsx)
        output_csv_grouped = Path(args.output_csv_rogue_grouped)
        output_xlsx_grouped = Path(args.output_xlsx_rogue_grouped)
        unknown_output = Path(args.unknown_output)
        alias_suggestions_output = Path(args.alias_suggestions_output)

        run_dir = output_csv.parent / f"{week_start.isoformat()}_to_{week_end.isoformat()}"
        run_dir.mkdir(parents=True, exist_ok=True)

        output_csv = run_dir / output_csv.name
        output_xlsx = run_dir / output_xlsx.name
        output_csv_grouped = run_dir / output_csv_grouped.name
        output_xlsx_grouped = run_dir / output_xlsx_grouped.name
        unknown_output = run_dir / unknown_output.name
        alias_suggestions_output = run_dir / alias_suggestions_output.name

        final_csv, final_xlsx = export_outputs(dataset, output_csv=output_csv, output_xlsx=output_xlsx)
        grouped = aggregate_rogue_bucket(dataset)
        grouped_csv, grouped_xlsx = export_outputs(grouped, output_csv=output_csv_grouped, output_xlsx=output_xlsx_grouped)
        final_unknown = export_unknown_archetypes(dataset, path=unknown_output)
        final_alias_suggestions = export_alias_suggestions(dataset, aliases=aliases, path=alias_suggestions_output)

        print(f"✅ Rows matched by user mapping: {mapped_from_user}")
        print(f"✅ Rows exported: {len(dataset)}")
        print(f"✅ My Deck Winrate primary ({args.my_window_days}d): {my_wr_stats['primary']}/{len(dataset)}")
        print(f"✅ My Deck Winrate fallback ({args.my_fallback_window_days}d): {my_wr_stats['fallback']}")
        print(f"✅ My Deck Winrate fallback 50%: {my_wr_stats['imputed']}")
        print(f"✅ Rogue threshold: Meta < {args.rogue_threshold}%")
        print(f"✅ CSV: {final_csv}")
        print(f"✅ XLSX: {final_xlsx}")
        print(f"✅ CSV (Rogue grouped): {grouped_csv}")
        print(f"✅ XLSX (Rogue grouped): {grouped_xlsx}")
        print(f"✅ Unknown archetypes report: {final_unknown}")
        print(f"✅ Alias suggestions report: {final_alias_suggestions}")
        print(f"✅ Output dir: {run_dir}")


if __name__ == "__main__":
    main()
