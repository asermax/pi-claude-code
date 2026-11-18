"""Resolve conflicts where both sides added a test at the same spot: keep ours, then theirs.

When the conflict sits right before a shared closing line ("});"), git has folded that
line out of both sides, so ours is closed before theirs is appended.

Only use it on test files, and only when every conflict hunk is "two new tests". If git
interleaved the two tests line by line instead, rebuild the region from each commit's
added lines (`git show <sha> -- <file> | grep '^+'`) and run `npm run check`.

Usage: python3 -I resolve_test_conflicts.py tests/a.test.ts [tests/b.test.ts ...]
"""

import sys

for path in sys.argv[1:]:
    with open(path) as handle:
        lines = handle.read().split("\n")

    out: list[str] = []
    i = 0

    while i < len(lines):
        if not lines[i].startswith("<<<<<<< "):
            out.append(lines[i])
            i += 1
            continue

        ours: list[str] = []
        theirs: list[str] = []

        i += 1
        while not lines[i].startswith("======="):
            ours.append(lines[i])
            i += 1

        i += 1
        while not lines[i].startswith(">>>>>>> "):
            theirs.append(lines[i])
            i += 1

        i += 1
        closing = i < len(lines) and lines[i] == "});"

        out += ours
        if ours and theirs and closing:
            out += ["});", ""]
        out += theirs

    with open(path, "w") as handle:
        handle.write("\n".join(out))
