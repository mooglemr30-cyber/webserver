#!/usr/bin/env python3
"""Document Scanner for AI Intelligence

Scans configured agent storage directory for .md and .txt files, ingests
contents into AIIntelligenceManager, and generates improvement ideas.

Usage (programmatic):
    from document_scanner import DocumentScanner
    scanner = DocumentScanner()
    report = scanner.scan()

Environment overrides:
    AGENT_STORAGE_PATH - directory to scan for documents
    SCAN_MAX_FILES     - limit number of files per run
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List
import traceback
from datetime import datetime, timezone

from path_config import PATHS
from ai_intelligence import get_ai_intelligence


class DocumentScanner:
    SUPPORTED_EXT = {'.md', '.txt'}

    def __init__(self, base_path: str | None = None, max_files: int | None = None):
        self.base_path = Path(base_path or os.environ.get('AGENT_STORAGE_PATH', PATHS['agent_storage']))
        self.max_files = max_files or int(os.environ.get('SCAN_MAX_FILES', '200'))
        self.ai = get_ai_intelligence()
        self.last_report: Dict | None = None

    def _gather_files(self) -> List[Path]:
        files: List[Path] = []
        if not self.base_path.exists():
            return files
        for p in self.base_path.rglob('*'):
            if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXT:
                files.append(p)
                if len(files) >= self.max_files:
                    break
        return files

    def scan(self) -> Dict:
        """Scan the configured base path and produce a structured report with a summary section."""
        return self._scan_paths([self.base_path])

    def scan_multi(self, extra_paths: List[str | Path]) -> Dict:
        """Scan multiple root paths (each treated independently).

        extra_paths: list of path strings or Path objects to include alongside the base path.
        Returns combined aggregated report.
        """
        roots: List[Path] = [self.base_path]
        for p in extra_paths:
            try:
                path_obj = Path(str(p)).resolve()
                if path_obj not in roots:
                    roots.append(path_obj)
            except Exception:
                continue
        return self._scan_paths(roots)

    def _scan_paths(self, roots: List[Path]) -> Dict:
        aggregate_files = 0
        aggregate_ingested = 0
        aggregate_errors: List[Dict] = []
        per_root: List[Dict] = []

        for root in roots:
            gathered: List[Path] = []
            if root.exists():
                for p in root.rglob('*'):
                    if p.is_file() and p.suffix.lower() in self.SUPPORTED_EXT:
                        gathered.append(p)
                        if len(gathered) >= self.max_files:
                            break
            ingested = 0
            errors: List[Dict] = []
            for f in gathered:
                try:
                    text = f.read_text(encoding='utf-8', errors='ignore')
                    if text.strip():
                        ok = self.ai.ingest_document(text, str(f), tags=['scan'])
                        if ok:
                            ingested += 1
                except Exception as e:
                    errors.append({'file': str(f), 'error': str(e)})
            per_root.append({
                'root': str(root),
                'files_considered': len(gathered),
                'files_ingested': ingested,
                'errors': errors,
            })
            aggregate_files += len(gathered)
            aggregate_ingested += ingested
            aggregate_errors.extend(errors)

        ideas = self.ai.generate_ideas()
        report = {
            'scanned_at': datetime.now(timezone.utc).isoformat(),
            'roots': [str(r) for r in roots],
            'total_files_considered': aggregate_files,
            'total_files_ingested': aggregate_ingested,
            'idea_count': len(ideas),
            'ideas': ideas,
            'errors': aggregate_errors,
            'per_root': per_root,
            'summary': {
                'success': True,
                'considered': aggregate_files,
                'ingested': aggregate_ingested,
                'idea_count': len(ideas),
                'error_count': len(aggregate_errors),
                'roots': [str(r) for r in roots]
            }
        }
        self.last_report = report
        self.ai.store_memory('scan_report', report, retention_priority=1)
        return report

    def get_last_report(self) -> Dict | None:
        return self.last_report


if __name__ == '__main__':
    scanner = DocumentScanner()
    rep = scanner.scan()
    import json
    print(json.dumps(rep, indent=2))