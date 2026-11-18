---
name: sync-upstream
description: Update this fork of earendil-works/pi-claude-code to the latest upstream main and bring in fixes published by other forks. Use when the user asks to sync with upstream, pull in fork fixes, or refresh the all-fixes branch.
---

# Sync with upstream and fork fixes

The fork's working branch is `all-fixes`: upstream `main` plus cherry-picked fixes
from other forks. The README table at the top lists every fix and the fork it came
from. That table is the record of what is already applied.

Analyze and propose first. Do not change branches or commit until the user approves
a list of fixes.

## 1. Find what changed

```sh
git fetch upstream
git log --oneline HEAD..upstream/main           # new upstream commits
git log --oneline upstream/main..HEAD           # fork-only commits
git merge-base HEAD upstream/main
```

If upstream moved, rebase or merge `all-fixes` onto it first, and drop any fork
fix that upstream now carries (compare against upstream PRs that merged).

List forks by last push, so only recently active ones are fetched:

```sh
gh api 'repos/earendil-works/pi-claude-code/forks?per_page=100' --paginate \
  --jq '.[] | "\(.full_name) \(.pushed_at)"' | sort -k2 -r
```

Fetch each fork pushed since the last sync into a separate ref namespace instead of
adding remotes, then count the commits each branch has ahead of upstream:

```sh
for f in <owner> ...; do
  git fetch -q "https://github.com/$f/pi-claude-code" "+refs/heads/*:refs/forks/$f/*"
done
for r in $(git for-each-ref --format='%(refname:short)' refs/forks); do
  n=$(git rev-list --count upstream/main..$r); [ "$n" -gt 0 ] && echo "$n $r"
done
```

Fork branches carry both PR branches and personal `main` branches that merge several
PRs; read `git log --format='%h %cs %an %s' upstream/main..forks/<branch>` for each.

Read upstream PRs and issues. A PR body usually explains the failure, the evidence and
how it interacts with other PRs, and comments report whether it fixed real sessions:

```sh
gh pr list -R earendil-works/pi-claude-code --state all --limit 100 \
  --json number,title,state,author,headRefName,createdAt
gh pr view <n> -R earendil-works/pi-claude-code --json title,body,comments
gh issue list -R earendil-works/pi-claude-code --state all --limit 40
```

## 2. Choose fixes

- Group commits that fix the same problem and pick one per group. Prefer the version
  that is an upstream PR with tests, that several forks adopted, or that covers the
  other versions' cases (for example, ariofrio's effort fix also replaced two
  `output_config` replay fixes).
- Compare each candidate with code already on `all-fixes`. A newer version of a fix
  we carry is a refinement to apply on top, not a duplicate.
- Rank by impact: errors that break every later turn of a session first, then
  cost and cache fixes, then cosmetic or situational ones.
- Skip large rewrites of retry and process lifecycle unless the user asks; they
  overlap the retry classification already carried.
- Note open upstream issues that no fork fixes, so the user knows about them.

Propose the list (fix, source, problem it solves), the skipped ones with a reason,
and the plan. Wait for approval.

## 3. Apply

Note the starting commit so the user can roll back with `git reset --hard <sha>`.
Work on `all-fixes` unless the user asks for a new branch.

Run the baseline first: `npm run check` and `npm test` (Node test runner through
`tsx`). Then apply one fix at a time and run both after each:

```sh
git cherry-pick -x <sha>
npm run check 2>&1 | grep error; npm test 2>&1 | grep -E '^ℹ (pass|fail)|^✖'
```

Conflicts:

- Most conflicts in `tests/*.test.ts` come from two tests added at the same spot.
  `scripts/resolve_test_conflicts.py` keeps both. Git sometimes interleaves the two
  tests line by line instead; then rebuild that region from each commit's added lines.
  After any resolution, run `npm run check`, because a test file can still parse wrong.
- Resolve `src/` conflicts by hand. `rewriteInitialRequest` in `src/claude-cli.ts`
  conflicts most often, because the cache, TTL, reminder and replay fixes all edit it.
  Keep the order it has: restore canonical user content, restore the initial system
  messages, drop repeated system messages, inject native system history, strip
  reminders, set replay breakpoints, cap breakpoints, enforce TTL order.
- If `cherry-pick --continue` already committed a broken resolution, fix it and
  `git commit --amend --no-edit`.

When a fix targets code we have since reshaped, apply it with `git cherry-pick -n`,
rewrite the conflicting part, and commit with the original author and a reference:

```sh
git commit --author="$(git log -1 --format='%an <%ae>' <sha>)" -m "fix: ...

(adapted from commit <sha>, earendil-works/pi-claude-code#<n>)"
```

If a fix breaks an existing test, find out which behaviour each side protects before
changing the test. Drop the fix when another applied fix already covers its case
(oskarrough's message-marker strip was dropped because the request-wide breakpoint cap
handled its five-marker case and the strip broke arhen's TTL ordering), and tell
the user.

Model catalog changes: `src/model-catalog.ts` takes limits and compat flags from
pi-ai's built-in Anthropic models, so a new model needs a pi-ai version that lists it.
Check with `npm pack @earendil-works/pi-ai@<version>` in the scratchpad and search
`package/dist/providers/data/anthropic.json`; bump the dev dependencies with npm
(the repo has `package-lock.json`).

## 4. Finish

- Add a row to the README table for each fix (problem, fork), and update the catalog
  sentence when models change. Commit as `docs: ...`.
- Delete the temporary refs:
  `git for-each-ref --format='%(refname)' refs/forks | xargs -n1 git update-ref -d`
- Report the commits applied, anything adapted or dropped and why, the test count
  before and after, and the rollback commit. Push only when the user asks.
