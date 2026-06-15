#!/usr/bin/env python3
"""Import wx-cli JSON output into copy-writing direct samples."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


SAMPLE_ID_RE = re.compile(r"^(\d{3})_")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def truncate_topic(topic: str, limit: int = 10) -> str:
    cleaned = normalize_text(topic)
    if not cleaned:
        return "微信样本"
    return cleaned[:limit]


def count_non_whitespace_chars(text: str) -> int:
    return sum(1 for char in text if not char.isspace())


def next_sample_id(samples_dir: Path) -> str:
    max_id = 0
    for path in samples_dir.glob("*_*.md"):
        match = SAMPLE_ID_RE.match(path.name)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return f"{max_id + 1:03d}"


def extract_history_entries(messages: list[Any]) -> tuple[list[str], str | None, str]:
    sender_counts: dict[str, int] = {}
    for item in messages:
        if not isinstance(item, dict):
            continue
        sender = normalize_text(item.get("sender"))
        if sender:
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

    self_sender = None
    if len(sender_counts) == 1:
        self_sender = next(iter(sender_counts))

    own_messages: list[tuple[int, str]] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        if normalize_text(item.get("type")) != "文本":
            continue
        sender = normalize_text(item.get("sender"))
        if self_sender is not None:
            if sender != self_sender:
                continue
        elif sender:
            continue
        content = normalize_text(item.get("content"))
        if not content:
            continue
        timestamp = int(item.get("timestamp") or 0)
        own_messages.append((timestamp, content))

    own_messages.sort(key=lambda pair: pair[0])
    return [content for _, content in own_messages], None, "history"


def extract_sns_entries(posts: list[Any]) -> tuple[list[str], str | None, str]:
    ordered_posts: list[tuple[int, str]] = []
    author = None
    for item in posts:
        if not isinstance(item, dict):
            continue
        content = normalize_text(item.get("content"))
        if not content:
            continue
        timestamp = int(item.get("timestamp") or 0)
        ordered_posts.append((timestamp, content))
        if not author:
            author = normalize_text(item.get("author"))

    ordered_posts.sort(key=lambda pair: pair[0])
    return [content for _, content in ordered_posts], author or None, "sns"


def extract_sample(payload: Any) -> tuple[list[str], str | None, str]:
    if isinstance(payload, dict):
        messages = payload.get("messages")
        if not isinstance(messages, list):
            raise ValueError("Unsupported wx-cli JSON object: expected a top-level 'messages' array.")
        entries, _, source_kind = extract_history_entries(messages)
        chat_name = normalize_text(payload.get("chat")) or None
        return entries, chat_name, source_kind

    if not isinstance(payload, list):
        raise ValueError("Unsupported wx-cli JSON payload: expected an array or an object.")

    if not payload:
        return [], None, "history"

    first = payload[0]
    if isinstance(first, dict) and "sender" in first:
        return extract_history_entries(payload)
    if isinstance(first, dict) and "author" in first and "content" in first:
        return extract_sns_entries(payload)
    raise ValueError("Unsupported wx-cli JSON array: expected chat messages or sns posts.")


def build_frontmatter(
    sample_id: str,
    sample_date: str,
    topic: str,
    word_count: int,
    entry_count: int,
    source_path: Path,
    source_kind: str,
) -> str:
    lines = [
        "---",
        f'id: "{sample_id}"',
        "source: direct",
        f'date: "{sample_date}"',
        f'topic: "{topic}"',
        f"word_count: {word_count}",
        'source_tool: "wx-cli"',
        f'source_kind: "{source_kind}"',
        f'source_file: "{source_path.name}"',
        f"message_count: {entry_count}",
        "---",
        "",
    ]
    return "\n".join(lines)


def import_wx_cli_json(
    input_path: str | Path,
    output_root: str | Path | None = None,
    topic: str | None = None,
    sample_date: str | None = None,
) -> Path:
    source_path = Path(input_path).expanduser().resolve()
    root_path = (
        Path(output_root).expanduser().resolve()
        if output_root
        else Path(__file__).resolve().parent.parent
    )

    with source_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    entries, topic_hint, source_kind = extract_sample(payload)
    if not entries:
        raise ValueError("No self-authored text content found in the provided wx-cli JSON.")

    samples_dir = root_path / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    sample_id = next_sample_id(samples_dir)
    chosen_topic = truncate_topic(topic or topic_hint or source_path.stem)
    chosen_date = sample_date or date.today().isoformat()
    body = "\n\n".join(entries).strip()
    word_count = count_non_whitespace_chars(body)

    markdown = build_frontmatter(
        sample_id=sample_id,
        sample_date=chosen_date,
        topic=chosen_topic,
        word_count=word_count,
        entry_count=len(entries),
        source_path=source_path,
        source_kind=source_kind,
    ) + body + "\n"

    output_path = samples_dir / f"{sample_id}_direct.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import wx-cli JSON output into the copy-writing sample library."
    )
    parser.add_argument(
        "input",
        help="Path to wx history --json output or wx export --format json output.",
    )
    parser.add_argument(
        "--output-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="copy-writing root directory. Defaults to this script's parent skill directory.",
    )
    parser.add_argument("--topic", help="Optional sample topic. Defaults to chat name or file name.")
    parser.add_argument(
        "--date",
        dest="sample_date",
        help="Optional sample date in YYYY-MM-DD format. Defaults to today.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    created = import_wx_cli_json(
        input_path=args.input,
        output_root=args.output_root,
        topic=args.topic,
        sample_date=args.sample_date,
    )
    print(created)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
