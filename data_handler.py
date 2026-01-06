from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from typing import Dict, List, Optional


class DataHandler:
    """Store, validate, and export product records to CSV with UTF-8 BOM."""

    def __init__(self) -> None:
        self.rows: List[Dict[str, Optional[str]]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def validate_record(self, record: Dict) -> bool:
        required = ["name", "url"]
        return all(record.get(k) for k in required)

    def add_record(self, record: Dict) -> None:
        record["timestamp"] = self._timestamp()
        self.rows.append(record)

    def to_csv(self, file_path: str) -> None:
        headers = ["Name", "Price", "Rating", "Reviews", "URL", "Item_Type", "Timestamp"]
        target = file_path
        try:
            with open(target, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f, fieldnames=headers, extrasaction="ignore"
                )
                writer.writeheader()
                for r in self.rows:
                    writer.writerow(
                        {
                            "Name": r.get("name"),
                            "Price": r.get("price"),
                            "Rating": r.get("rating"),
                            "Reviews": r.get("reviews"),
                            "URL": r.get("url"),
                            "Item_Type": r.get("item_type"),
                            "Timestamp": r.get("timestamp"),
                        }
                    )
        except PermissionError:
            base, ext = os.path.splitext(file_path)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback = f"{base}_{ts}{ext or '.csv'}"
            with open(fallback, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f, fieldnames=headers, extrasaction="ignore"
                )
                writer.writeheader()
                for r in self.rows:
                    writer.writerow(
                        {
                            "Name": r.get("name"),
                            "Price": r.get("price"),
                            "Rating": r.get("rating"),
                            "Reviews": r.get("reviews"),
                            "URL": r.get("url"),
                            "Item_Type": r.get("item_type"),
                            "Timestamp": r.get("timestamp"),
                        }
                    )

