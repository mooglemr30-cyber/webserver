#!/usr/bin/env python3
"""Run a one-off or looped document scan feeding AI intelligence.

Options:
  LOOP=1            - continuously scan (with sleep interval)
  INTERVAL=300      - seconds between scans when looping
  MAX_FILES=100     - limit files per scan

Environment uses AGENT_STORAGE_PATH for scan root; see path_config.py.
"""
import os
import time
import json
from document_scanner import DocumentScanner

def main():
    loop = os.environ.get('LOOP') == '1'
    interval = int(os.environ.get('INTERVAL', '300'))
    max_files_env = os.environ.get('MAX_FILES')
    scanner = DocumentScanner(max_files=int(max_files_env) if max_files_env else None)

    def run_once():
        rep = scanner.scan()
        print(json.dumps(rep, indent=2))
        return rep

    if loop:
        while True:
            run_once()
            time.sleep(interval)
    else:
        run_once()

if __name__ == '__main__':
    main()