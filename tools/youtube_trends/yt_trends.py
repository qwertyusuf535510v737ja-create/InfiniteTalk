#!/usr/bin/env python3
"""YouTube trend snapshot va hisobot vositasi (faqat standart kutubxona).

Google YouTube Data API v3 orqali tanlangan mamlakatlar bo'yicha "mostPopular"
ro'yxatini oladi, har video uchun soatiga ko'rish tezligini (VPH) hisoblaydi,
CSV ga yozadi va kategoriya bo'yicha qisqa hisobot chiqaradi.

Buyruqlar:
    python yt_trends.py fetch  [--regions UZ,RU,US] [--max 200] [--out data/]
    python yt_trends.py report [--data data/] [--days 14]

Kvota: har mamlakat uchun taxminan 5 birlik (kunlik bepul limit 10 000).

Muhit o'zgaruvchisi: YOUTUBE_API_KEY (yoki --api-key).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

API_BASE = "https://www.googleapis.com/youtube/v3/"
DEFAULT_REGIONS = "UZ,RU,US"
SHORT_MAX_SECONDS = 180  # <= 3 daqiqa Shorts deb hisoblanadi

CSV_FIELDS = [
    "snapshot_date",
    "snapshot_time_utc",
    "region",
    "rank",
    "video_id",
    "title",
    "channel_id",
    "channel_title",
    "category",
    "format",
    "duration_sec",
    "published_at",
    "hours_since_publish",
    "view_count",
    "like_count",
    "comment_count",
    "views_per_hour",
    "engagement_rate",
    "url",
]


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def api_get(endpoint: str, params: dict, api_key: str) -> dict:
    params = dict(params, key=api_key)
    url = API_BASE + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            message = json.loads(body)["error"]["message"]
        except (ValueError, KeyError):
            message = body[:300]
        raise SystemExit(f"YouTube API xatosi ({exc.code}): {message}") from exc


def fetch_categories(region: str, api_key: str) -> dict[str, str]:
    data = api_get(
        "videoCategories",
        {"part": "snippet", "regionCode": region, "hl": "en"},
        api_key,
    )
    return {item["id"]: item["snippet"]["title"] for item in data.get("items", [])}


def fetch_most_popular(region: str, max_results: int, api_key: str) -> list[dict]:
    items: list[dict] = []
    page_token = None
    while len(items) < max_results:
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": min(50, max_results - len(items)),
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get("videos", params, api_key)
        items.extend(data.get("items", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return items[:max_results]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
_DURATION_RE = re.compile(
    r"P(?:(?P<d>\d+)D)?T?(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?"
)


def parse_iso_duration(value: str) -> int:
    """ISO 8601 davomiylikni (PT1H2M3S) soniyaga aylantiradi."""
    match = _DURATION_RE.fullmatch(value or "")
    if not match:
        return 0
    parts = {k: int(v) for k, v in match.groupdict().items() if v}
    return (
        parts.get("d", 0) * 86400
        + parts.get("h", 0) * 3600
        + parts.get("m", 0) * 60
        + parts.get("s", 0)
    )


def parse_timestamp(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_rows(region: str, items: list[dict], categories: dict[str, str], now: dt.datetime) -> list[dict]:
    rows = []
    for rank, item in enumerate(items, start=1):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        details = item.get("contentDetails", {})

        published = parse_timestamp(snippet.get("publishedAt", now.strftime("%Y-%m-%dT%H:%M:%SZ")))
        hours = max((now - published).total_seconds() / 3600.0, 1.0)
        views = to_int(stats.get("viewCount"))
        likes = to_int(stats.get("likeCount"))
        comments = to_int(stats.get("commentCount"))
        duration = parse_iso_duration(details.get("duration", ""))

        rows.append(
            {
                "snapshot_date": now.strftime("%Y-%m-%d"),
                "snapshot_time_utc": now.strftime("%H:%M"),
                "region": region,
                "rank": rank,
                "video_id": item.get("id", ""),
                "title": snippet.get("title", "").replace("\n", " "),
                "channel_id": snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "category": categories.get(snippet.get("categoryId", ""), snippet.get("categoryId", "")),
                "format": "short" if 0 < duration <= SHORT_MAX_SECONDS else "long",
                "duration_sec": duration,
                "published_at": snippet.get("publishedAt", ""),
                "hours_since_publish": round(hours, 1),
                "view_count": views,
                "like_count": likes,
                "comment_count": comments,
                "views_per_hour": round(views / hours, 1),
                "engagement_rate": round((likes + comments) / views, 4) if views else 0.0,
                "url": f"https://www.youtube.com/watch?v={item.get('id', '')}",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def read_snapshots(data_dir: Path, days: int) -> list[dict]:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    rows: list[dict] = []
    for path in sorted(data_dir.glob("trends_*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["snapshot_date"] >= cutoff:
                    rows.append(row)
    return rows


def fmt_num(value: float) -> str:
    value = float(value)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
def print_snapshot_summary(rows: list[dict]) -> None:
    by_region: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_region[row["region"]].append(row)

    for region, region_rows in by_region.items():
        print(f"\n=== {region}: {len(region_rows)} ta trend video ===")

        category_vph: dict[str, float] = defaultdict(float)
        category_count: dict[str, int] = defaultdict(int)
        format_count: dict[str, int] = defaultdict(int)
        for row in region_rows:
            category_vph[row["category"]] += float(row["views_per_hour"])
            category_count[row["category"]] += 1
            format_count[row["format"]] += 1

        print("Kategoriya bo'yicha (jami VPH, video soni):")
        for category, vph in sorted(category_vph.items(), key=lambda kv: kv[1], reverse=True)[:8]:
            print(f"  {category:<24} {fmt_num(vph):>8} VPH   {category_count[category]:>3} ta")

        print(f"Format: long={format_count.get('long', 0)}  short={format_count.get('short', 0)}")

        print("Eng tez o'sayotgan 10 video (VPH):")
        top = sorted(region_rows, key=lambda r: float(r["views_per_hour"]), reverse=True)[:10]
        for row in top:
            title = row["title"][:60]
            print(
                f"  {fmt_num(row['views_per_hour']):>7} VPH  {fmt_num(row['view_count']):>7} ko'rish  "
                f"[{row['format']}] {row['channel_title'][:22]:<22} | {title}"
            )


def print_history_report(rows: list[dict], days: int) -> None:
    if not rows:
        print("Ma'lumot topilmadi. Avval `fetch` buyrug'ini ishga tushiring.")
        return

    dates = sorted({r["snapshot_date"] for r in rows})
    regions = sorted({r["region"] for r in rows})
    print(f"Davr: {dates[0]} .. {dates[-1]} ({len(dates)} kun), mamlakatlar: {', '.join(regions)}")

    for region in regions:
        region_rows = [r for r in rows if r["region"] == region]
        print(f"\n=== {region} ===")

        # Kategoriya ulushi (trend ro'yxatida necha marta paydo bo'ldi)
        category_days: dict[str, set] = defaultdict(set)
        category_hits: dict[str, int] = defaultdict(int)
        for r in region_rows:
            category_hits[r["category"]] += 1
            category_days[r["category"]].add(r["snapshot_date"])
        total = sum(category_hits.values())
        print("Kategoriya ulushi (trend ro'yxatidagi o'rinlar):")
        for category, hits in sorted(category_hits.items(), key=lambda kv: kv[1], reverse=True)[:8]:
            print(f"  {category:<24} {hits / total * 100:5.1f}%   {len(category_days[category])}/{len(dates)} kun")

        # Barqaror kanallar: turli kunlarda va turli videolar bilan chiqqanlar
        channel_videos: dict[str, set] = defaultdict(set)
        channel_days: dict[str, set] = defaultdict(set)
        channel_name: dict[str, str] = {}
        for r in region_rows:
            channel_videos[r["channel_id"]].add(r["video_id"])
            channel_days[r["channel_id"]].add(r["snapshot_date"])
            channel_name[r["channel_id"]] = r["channel_title"]
        stable = sorted(
            channel_videos.items(),
            key=lambda kv: (len(kv[1]), len(channel_days[kv[0]])),
            reverse=True,
        )[:10]
        print("Eng barqaror kanallar (turli videolar soni / kunlar):")
        for channel_id, videos in stable:
            print(f"  {channel_name[channel_id][:30]:<30} {len(videos):>3} video  {len(channel_days[channel_id]):>3} kun")

        # Eng katta VPH ko'rsatgan videolar (har video bo'yicha maksimum)
        best: dict[str, dict] = {}
        for r in region_rows:
            current = best.get(r["video_id"])
            if current is None or float(r["views_per_hour"]) > float(current["views_per_hour"]):
                best[r["video_id"]] = r
        print(f"So'nggi {days} kundagi eng tez uchgan 10 video:")
        for r in sorted(best.values(), key=lambda r: float(r["views_per_hour"]), reverse=True)[:10]:
            print(
                f"  {fmt_num(r['views_per_hour']):>7} VPH  {r['snapshot_date']}  [{r['format']}] "
                f"{r['channel_title'][:20]:<20} | {r['title'][:55]}"
            )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def cmd_fetch(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("YOUTUBE_API_KEY muhit o'zgaruvchisi yoki --api-key kerak.", file=sys.stderr)
        return 2

    regions = [r.strip().upper() for r in args.regions.split(",") if r.strip()]
    now = dt.datetime.now(dt.timezone.utc)
    out_dir = Path(args.out)
    all_rows: list[dict] = []

    for region in regions:
        categories = fetch_categories(region, api_key)
        items = fetch_most_popular(region, args.max, api_key)
        rows = build_rows(region, items, categories, now)
        all_rows.extend(rows)
        print(f"{region}: {len(rows)} ta video olindi", file=sys.stderr)

    csv_path = out_dir / f"trends_{now.strftime('%Y-%m-%d')}.csv"
    write_csv(csv_path, all_rows)
    print(f"Yozildi: {csv_path} ({len(all_rows)} qator)", file=sys.stderr)

    if not args.quiet:
        print_snapshot_summary(all_rows)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    rows = read_snapshots(Path(args.data), args.days)
    print_history_report(rows, args.days)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Bugungi trend ro'yxatini olib CSV ga yozish")
    fetch.add_argument("--regions", default=DEFAULT_REGIONS, help=f"Vergul bilan ISO kodlar (standart: {DEFAULT_REGIONS})")
    fetch.add_argument("--max", type=int, default=200, help="Har mamlakat uchun maksimal video (1..200)")
    fetch.add_argument("--out", default=str(Path(__file__).parent / "data"), help="CSV papkasi")
    fetch.add_argument("--api-key", default=None, help="YOUTUBE_API_KEY o'rniga")
    fetch.add_argument("--quiet", action="store_true", help="Ekranga hisobot chiqarmaslik")
    fetch.set_defaults(func=cmd_fetch)

    report = sub.add_parser("report", help="Yig'ilgan snapshotlar bo'yicha hisobot")
    report.add_argument("--data", default=str(Path(__file__).parent / "data"), help="CSV papkasi")
    report.add_argument("--days", type=int, default=14, help="Necha kunlik ma'lumot")
    report.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
