"""
Safe Corpus Preprocessor
SIH26151: Dark Web Threat Actor De-anonymization

Handles loading, cleaning, and normalizing anonymized dark-web forum posts
from safe_corpus.json. Extracts text intelligence, temporal patterns, topics,
and threat categories while strictly respecting all redactions.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class SafeCorpusPreprocessor:
    """Preprocesses and extracts structured intelligence from safe_corpus.json."""

    def __init__(self, file_path: str = "safe_corpus.json"):
        self.file_path = file_path
        self.raw_records: List[Dict[str, Any]] = []
        self.processed_posts: List[Dict[str, Any]] = []

    def load_corpus(self) -> List[Dict[str, Any]]:
        """Loads JSON/JSONL records from safe_corpus.json."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Safe corpus file not found: {self.file_path}")

        records = []
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError:
                    # Attempt entire document read if single JSON array
                    f.seek(0)
                    try:
                        records = json.load(f)
                    except Exception as e:
                        raise ValueError(f"Failed to parse {self.file_path}: {e}")
                    break

        self.raw_records = records
        return self.raw_records

    def clean_text(self, text: str) -> str:
        """
        Cleans text while preserving essential stylometric cues:
        punctuation, casing, structural spacing, and formatting.
        """
        if not text:
            return ""
        # Normalize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Remove null bytes or non-printable control chars except tabs/newlines
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse excessive whitespace beyond 3 newlines
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    def parse_timestamp(self, date_str: str) -> Optional[datetime]:
        """Parses forum timestamp strings into standard datetime objects."""
        if not date_str:
            return None
        date_str = date_str.strip()
        # Common forum formats: '04-08-23, 07:01 PM', '2023-04-08 19:01:00'
        formats = [
            "%m-%d-%y, %I:%M %p",
            "%d-%m-%y, %I:%M %p",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%b %d, %Y, %I:%M %p",
            "%d %b %Y, %H:%M"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def extract_posts(self) -> List[Dict[str, Any]]:
        """
        Extracts all individual posts and thread headers into flat post objects.
        """
        if not self.raw_records:
            self.load_corpus()

        extracted = []
        for thread in self.raw_records:
            thread_id = str(thread.get("thread_id", ""))
            thread_title = self.clean_text(thread.get("title", ""))
            category = thread.get("category", "Uncategorized")
            forum_name = thread.get("forum_name", "General")
            thread_author = thread.get("author", "unknown")
            date_posted = thread.get("date_posted", "")
            posts = thread.get("posts", [])

            # Add thread main body if present
            if thread_title:
                dt = self.parse_timestamp(date_posted)
                extracted.append({
                    "thread_id": thread_id,
                    "post_id": f"{thread_id}_head",
                    "author": thread_author,
                    "forum": forum_name,
                    "category": category,
                    "title": thread_title,
                    "content": thread_title,
                    "raw_date": date_posted,
                    "datetime": dt,
                    "hour": dt.hour if dt else None,
                    "day_of_week": dt.weekday() if dt else None,
                    "is_thread_op": True
                })

            for post in posts:
                p_id = str(post.get("post_id", ""))
                p_author = post.get("author", thread_author)
                p_date = post.get("post_date", date_posted)
                p_content = self.clean_text(post.get("content", ""))
                dt = self.parse_timestamp(p_date)

                if p_content:
                    extracted.append({
                        "thread_id": thread_id,
                        "post_id": p_id,
                        "author": p_author,
                        "forum": forum_name,
                        "category": category,
                        "title": thread_title,
                        "content": p_content,
                        "raw_date": p_date,
                        "datetime": dt,
                        "hour": dt.hour if dt else None,
                        "day_of_week": dt.weekday() if dt else None,
                        "is_thread_op": False
                    })

        self.processed_posts = extracted
        return self.processed_posts

    def get_actor_posts(self, author_name: str) -> List[Dict[str, Any]]:
        """Filters extracted posts by author identifier."""
        if not self.processed_posts:
            self.extract_posts()
        return [p for p in self.processed_posts if p.get("author") == author_name]
