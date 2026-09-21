"""List the lines changed since a git revision that no test executes.

    python -m pytest -m "" --cov --cov-report=json:coverage.json --timeout=300
    python tools/diff_coverage.py coverage.json 81688e5

For each measured file, prints the uncovered lines that were added or
modified since REV (default: HEAD), with their source, so a coverage pass
can concentrate on the code it touched.
"""

import json
import re
import subprocess
import sys

HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')


def changed_lines(rev, path):
    """Line numbers of PATH (as it is now) added or changed since REV."""
    diff = subprocess.run(['git', 'diff', '-U0', rev, '--', path],
                          capture_output=True, text=True, check=True).stdout
    lines = set()
    for line in diff.splitlines():
        m = HUNK.match(line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            lines.update(range(start, start + count))
    return lines


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    report_path = sys.argv[1]
    rev = sys.argv[2] if len(sys.argv) == 3 else 'HEAD'
    with open(report_path) as f:
        report = json.load(f)

    total = 0
    for path, data in sorted(report['files'].items()):
        missed = sorted(set(data['missing_lines']) & changed_lines(rev, path))
        if not missed:
            continue
        total += len(missed)
        with open(path) as f:
            source = f.read().splitlines()
        print(f'--- {path}: {len(missed)} changed line(s) not covered')
        for n in missed:
            print(f'{n:5d}  {source[n - 1]}')
    print(f'\n{total} changed line(s) not covered since {rev}')


if __name__ == '__main__':
    main()
