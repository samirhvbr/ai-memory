# Version — samirhvbr fork of ai-memory

**Current version:** `0.3.9`
**Upstream:** [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) @ `957b1dd0` (`main`, `v3.4.4`)

The **first semver in this file is ours**, and that is not cosmetic: everything
that reads a version here takes the first one it finds. Pointing that at the
upstream's number would hand our tooling a value we do not control, cannot bump,
and that moves on somebody else's schedule — including backwards, when an
upstream reverts ([repodocs ADR-012 and ADR-023][adr]).

**Our history starts where our changes start**, not at the upstream's number, so
this begins at `0.1.0` regardless of how far along they are.

**The upstream's own version fields are theirs and are not edited here.**
Editing them conflicts on every sync.

**A sync is a delivery.** Pulling from `upstream` changes what this fork is, so
it bumps the version above and its entry names the upstream point we moved to —
even when not a line of our own code changed.

Where this fork's CI runs: [`docs/ci.md`](docs/ci.md).
Where the memory server runs and which upstream release it is on: [`docs/mem-shvia-org.md`](docs/mem-shvia-org.md).

[adr]: https://github.com/samirhvbr/repodocs/blob/master/docs/decisions.md

---

## Changelog

Newest first. Each `##` heading is literally the commit subject. The upstream's
own changelog, where it has one, is left alone: it is their record, not ours.

## 0.3.9 - the 3.4.4 rehearsal: V100 needs about 27 GB of free disk and the server has 24

The server is still on `3.4.2`. Before moving it to `3.4.4` the range was rehearsed
on a copy of production data, and it does not fit as things stand. V100, the
owner's PR #2019, rebuilds both full-text indexes and indexes each text a second
time: **22 min 40 s** on the workstation, a write-ahead log of **14.26 GB** (V97
peaked at 5.98 GB in production), and a database file that went from 46.4 to
**54.6 GB** while the whole log was still on disk. That is about 22.5 GB above the
current database at the peak, plus 0.9 GB for the cold backup, and the script stops
the container below 4 GB free: about 27.5 GB needed against 24 free, with no free
extent in the volume group. The page index grew **2.7 times**, not the "roughly
twice" the upstream changelog states. On the V97 ratio (3.5 to 4.2 times slower
there) the downtime would be 85 to 100 minutes, an estimate.

Checks on the migrated copy matched: the same 867 latest pages, 3,127 sessions and
887,167 observations, the index complete, `quick_check` and the FTS5
`integrity-check` `ok`, the endpoints answering. The copy was deleted afterwards.
`upgrade-3.4.4.sh` is on the server and was not run; the way forward is a larger
virtual disk for `blue3site` (about 30 GB more, an owner decision on the
Hyper-V host), then the script. The same measurement showed that the 596 MB of
growth on `3.4.2` was not the tokenizer, which the `0.3.7` entry had said: the
index tables moved by 4 MB. [`docs/mem-shvia-org.md`](docs/mem-shvia-org.md) has the
table, the estimate and a reading of the nine advisories in the range.

## 0.3.8 - the fork moves onto upstream v3.4.4

The fork was on upstream `main` at `5d9660df` (`v3.4.2` plus one docs commit).
Upstream has since published `v3.4.3` (06/11/2026) and `v3.4.4` (08/11/2026), and
`main` moved 161 commits. This sync merges upstream `main` at `957b1dd0`, which is
the `v3.4.4` release commit itself. It came in as a merge again, merged clean, no
upstream commit rewritten and no force-push. After it the tree differs from
`upstream/main` in our three files (`version.md`, `docs/ci.md`,
`docs/mem-shvia-org.md`) and nothing else.

What the range brings that matters to the server, which still runs `3.4.2`:

- **Migration V100** is the owner's PR #2019 (merged upstream on 06/11 with three
  maintainer commits on top). It indexes the parts of a hyphenated or underscored
  word, so `alpha` finds `foo-bar-alpha`. Like V97 it **drops and rebuilds both
  full-text indexes** (`pages_fts` and `observations_fts`), and the changelog says
  they grow to roughly twice their size. Neither the rebuild time on this
  server's data nor the new index size has been measured yet; the V97 run took
  31 min 48 s here, and V100 indexes each text twice.
- **Migration V101** adds a `manual` flag to handoffs; nothing heavy.
- **Security:** `v3.4.4` lists eight advisories and `v3.4.3` one (`ai-memory
  restore` bringing back a backup's git hooks). Which of them reach this
  installation has not been triaged.

`mem.shvia.org` is still on the `3.4.2` image: the server follows the published
image, not this branch, and moves only by the procedure in
[`docs/mem-shvia-org.md`](docs/mem-shvia-org.md), after a rehearsal that measures
V100 on a copy of production data. The upstream tags (`v3.4.3`, `v3.4.4`) were
fetched here and not pushed, so the Releases box of this repository still reads
`v2.0.1`.

## 0.3.7 - mem.shvia.org runs 3.4.2, after a cold backup and 35 minutes down

The server moved from `3.3.1` to `3.4.2` on 05/11/2026, so it is level with the
code this fork carries since `0.3.6`. `upgrade-3.4.2.sh` completed on its first
run on the right machine: a verified cold backup of 873 MiB in 3 min 22 s, then V97
to V99 in 31 min 48 s, ready at 21:50:54 UTC, **down 35 min 13 s** in all. That
matches the 31 to 36 minutes the rehearsal predicted, and the shape was the one it
showed: V97 rebuilds both full-text indexes, the write-ahead log peaked at 5.98 GB
(5.37 GB on the rehearsal's smaller copy), and the database file grew by 596 MB
(0.3.9 corrects the reason given here: the index tables grew by 4 MB, so it was not the tokenizer, and the cause was not found). Every check matched before and
after, directly and through Apache; the schema is 99, the index is complete (FTS
61,323 / 61,323 pages and 887,171 / 887,171 observations), the container log has no
`ERROR` line, and the `ai-memory-web` probe is clean.

The command that starts the script was first typed in the root console of the
application server by mistake; `blue3site` was untouched until the second attempt.
The page in [`docs/mem-shvia-org.md`](docs/mem-shvia-org.md) now says to check the
prompt, and records the timings, the rollback and what is still open: the clients
are `2.x`, and nobody has checked whether observations stored before the `3.3.3`
redaction fix hold a password printed by a tool.

The upstream tags are still not pushed to this fork, so its Releases box still
reads `v2.0.1`; publishing `v3.4.2` there is the owner's decision.

## 0.3.6 - the fork moves onto upstream main past v3.4.2

The fork was on upstream `main` at `72e4f427` (`v3.3.1` plus one commit) since
02/11/2026. By 05/11 upstream had published five releases (`v3.3.2` and `v3.3.3`
on 03/11, `v3.4.0` on 04/11, `v3.4.1` and `v3.4.2` on 05/11) and `main` had moved
285 commits. This sync merges upstream `main` at `5d9660df` (`v3.4.2` plus one
docs commit). It came in as a merge again, with no upstream commit rewritten and
no force-push, and it merged clean. After it the tree differs from
`upstream/main` in our three files (`version.md`, `docs/ci.md`,
`docs/mem-shvia-org.md`) and nothing else: not a line of our own code changed,
and none exists.

What the range brings that matters to the server: three migrations, V97 to V99.
V98 adds a small table and V99 a nullable column with a partial index, but **V97
drops and rebuilds both full-text indexes** (`pages_fts` and `observations_fts`),
so unlike V89 to V96 it is not seconds. The rehearsal on a copy of production
data is recorded in [`docs/mem-shvia-org.md`](docs/mem-shvia-org.md): 7 min 38 s
on a workstation, a 5.4 GB write-ahead log at its peak, no net growth of the
database file. On the server's measured speed that is about half an hour of
downtime on top of the cold backup. `3.3.3` also carries a security fix that
matters to this server: a password or key printed by a tool is now redacted when
Claude Code's `PostToolUse` result arrives as an object, which is the shape it
always takes.

`mem.shvia.org` is still on the `3.3.1` image when this is written: the server
follows the published image, not this branch, and moves only by the procedure in
that document. The upstream tags (`v3.3.2` to `v3.4.2`) were fetched here and not
pushed to this fork. The reason in `0.3.3` is gone, since the Actions lock lifted
on 03/11 and the scheduled `windows` run is green again, but a `v*.*.*` tag still
starts `release.yml` and publishes a Release with its binaries, so it is left for
the owner to decide. The Releases box of this repository still reads `v2.0.1`.

## 0.3.5 - mem.shvia.org runs 3.3.1, after a cold backup and 4 minutes down

The server moved from `3.2.8` to `3.3.1` on 02/11/2026, so it is level with the
code this fork carries since `0.3.4`. The last of three runs of `upgrade-3.3.1.sh`
completed: a verified cold backup of 850 MB, `3.3.1` ready at 16:38:22 UTC, down
about 4 min 18 s. V89 to V96 are applied (schema 96), every check matched before
and after, directly and through Apache, the `ai-memory-web` probe is clean and the
index is complete. The rehearsal on a copy of production data had started `3.3.1`
in 2.1 s, which is what the migrations' shape predicted.

Two earlier runs did not complete, and both are recorded in
[`docs/mem-shvia-org.md`](docs/mem-shvia-org.md). The first aborted in the backup
because the script treated a `tar` warning about transient SQLite files as a
failure: a defect in the script, fixed (the backup now excludes `-wal` and `-shm`
and guards the database file's size and time instead), with no change to the
server. The second was interrupted by the virtual machine stopping abruptly after
the backup had finished, an event of unestablished cause that is outside what this
repository can see; the memory server was out of service for about 12 minutes and
lost no data. The same document now also records the machine's measured
configuration: an 8 vCPU, 7.7 GiB Hyper-V guest that shares the host with the
websites, where ai-memory itself uses 250 MiB and 0.4% CPU.

The clients on each machine are still `2.x`, which works against this server
until `ai-memory upgrade` runs there.

## 0.3.4 - the fork moves onto upstream main past v3.3.1

The fork was on upstream `main` at `6ac0ebce` (`v3.2.10` plus 38 commits) since
29/10/2026. By 02/11 upstream had published `v3.3.0` (29/10) and `v3.3.1` (31/10)
and `main` had moved 300 commits. This sync merges upstream `main` at `72e4f427`
(`v3.3.1` plus one commit, a consolidation of GitHub Actions bumps). It came in
as a merge, with no upstream commit rewritten and no force-push, and it merged
clean. After it the tree differs from `upstream/main` in our three files
(`version.md`, `docs/ci.md`, `docs/mem-shvia-org.md`) and nothing else: not a
line of our own code changed, and none exists.

What the range brings that matters to the server: eight migrations, V89 to V96.
Two rebuild a table (V89 `sessions`, V95 `agent_messages`); neither touches
`observations` or `pages`, and the other six add columns, indexes or small side
tables (`session_usage`, `token_calls`, `token_call_tools`). That is a different
shape from the V77 to V88 run that took sixteen minutes on 27/10, but the
timing on the real 45 GB database is not measured here: see
[`docs/mem-shvia-org.md`](docs/mem-shvia-org.md) for the state of the server.

`mem.shvia.org` is still on the `3.2.8` image when this is written: the server
follows the published image, not this branch, and moves only by the procedure in
that document. The upstream tags (`v3.3.0`, `v3.3.1`) were fetched here and not
pushed to this fork, for the reason in `0.3.3`: a `v*.*.*` tag starts
`release.yml`, and the Releases box of this repository still reads `v2.0.1`.

## 0.3.3 - the fork moves onto upstream main past v3.2.10, and why Releases still read v2.0.1

The fork was on `v3.2.8` (`0e548807`) since 27/10/2026 and by 29/10 was 188
upstream commits behind: the `v3.2.9` and `v3.2.10` releases plus 38 commits on
`main`. This sync merges upstream `main` at `6ac0ebce`. It came in as a merge
again, with no upstream commit rewritten and no force-push, and it merged clean.
After it the tree differs from `upstream/main` in our three files
(`version.md`, `docs/ci.md`, `docs/mem-shvia-org.md`) and nothing else, so no
customization was lost and none exists in code: not a line of our own changed.

Five of the 38 commits are ours, merged upstream earlier from this account
(#1844, #1845, #1846, #1848, #1849: the macOS LaunchAgent paths and output
drain, the grouped CJK column filters, the device-authorization polling
deadline, the ephemeral SDK test port).

**The "Latest" release of this repository still reads `v2.0.1`, and that is not
the code.** The Releases box lists what was tagged *here*, and the only tags
ever pushed to this fork are `v2.0.0`, `v2.0.1` and `v2.0.2` (02 and 03/09/2026,
each built by `release.yml`). The syncs since then merged the code and never
pushed the upstream's tags, so the page stayed where it was. The code is `3.2.10`
(`Cargo.toml`); the image production runs is the upstream's, not a build of this
fork. Pushing a `v*.*.*` tag here starts `release.yml`, which builds on the
hosted runners (the account is billing-locked at the time of writing), so the
fork's tags were not touched.

`mem.shvia.org` is still on the `3.2.8` image: the server follows the published
image, not this branch, and moves only by the procedure in
[`docs/mem-shvia-org.md`](docs/mem-shvia-org.md).

## 0.3.2 - mem.shvia.org runs 3.2.8, after a cold compressed backup and 22 minutes down

The server moved from `2.6.6` to `3.2.8` on 27/10/2026 with `upgrade-3.2.8.sh`:
the image pulled before the stop, a verified cold backup of 825 MB in five
minutes, then V77 to V88 in sixteen. Down 21 min 38 s in all. Every check
matched before and after, directly and through Apache; the schema is 88 and the
`ai-memory-web` probe is clean. The hooks flushed what they held in the first
minute back: 125 events stored, none failed. The clients on each machine are
still 2.x until `ai-memory upgrade` runs there.

## 0.3.1 - the 3.2.8 upgrade of mem.shvia.org is rehearsed on a copy first

`docs/mem-shvia-org.md` records a rehearsal on a workstation, on a copy of the
13/10 cold backup brought to 2.6.6 first: V77 to V88 applied in 4 min 17 s with
no extra disk, the same counts before and after, the production checks green
(200 with the bearer, 401 without), and `ai-memory-web`'s schema probe clean
against schema 88. On the server's speed that is about 15 minutes down plus the
backup. The server itself is still on 2.6.6.

## 0.3.0 - the fork moves onto upstream v3.2.8, past the 3.0 major release

The fork sat on `d408450d` (`v2.6.6` plus nine commits) since 13/10/2026. By
27/10/2026 that was **1,552 upstream commits and fifteen releases behind**:
`v2.6.7`, the **`v3.0.0` major release** on 14/10, and `v3.0.1` through
`v3.2.8`. This sync merges upstream `main` at `0e548807`, which is exactly the
`v3.2.8` tag: nothing after the release, so the fork is the code the published
`3.2.8` image runs.

It came in as a merge again: no upstream commit rewritten, no force-push, and it
merged clean. After the merge the tree differs from `v3.2.8` in our three files
(`version.md`, `docs/ci.md`, `docs/mem-shvia-org.md`) and nothing else. Not a
line of our own code changed.

**What 3.0 means for the server** ([`docs/upgrading-to-3.0.md`](docs/upgrading-to-3.0.md)
upstream): the 1.x token commands are gone (the server authenticates with the
`AI_MEMORY_AUTH_TOKEN` variable, which 3.x still honours), `memory_query` now
searches observations by default, and the first start applies migrations
**V77 to V88**, forward only. `mem.shvia.org` is still on `2.6.6` at this
version; the upgrade and its measurements go in `docs/mem-shvia-org.md`.

## 0.2.3 - the post-upgrade checks reach ai-memory-web through its schema probe

The server was reviewed an hour after the 2.6.6 restart. Nothing in it needed
a fix for the upgrade:

- The server had stored 1,109 hook events, with none failed.
- Every request to the vhost was 2xx, apart from the checks' own no-token
  probes.
- The Apache proxy errors in that hour all came from PHP-FPM on other vhosts.

One check was missing from `docs/mem-shvia-org.md`, and it is the one that
covers the other reader of this database. `ai-memory-web`'s schema canary needs
phpunit, which its production checkout does not have. The probe behind the
canary runs with a plain Laravel bootstrap, though, and it repeats every read
the panel makes. Against schema 76 it found no failures. The page now carries
that command, and it says where Apache logs this vhost.

## 0.2.2 - mem.shvia.org runs 2.6.6, after a cold compressed backup and 38 minutes down

The server moved from `2.1.2` to `2.6.6` on 13/10/2026, the release this
fork's upstream point contains. This was the day's second attempt, and
`docs/mem-shvia-org.md` now describes it as the procedure:

1. Stop the container.
2. Take a cold backup on the same disk with `tar` and `zstd --long=27`, and
   verify it before going on. 45 GB became 751 MB in five minutes.
3. Switch the pinned tag and start.
4. Watch free space.

The V62 backfill took 33 of the 38 minutes down. Every check matched before
and after: the same workspaces and counts, and 200 with the bearer and 401
without it, both directly and through Apache. Hook events were stored again
within the first minutes.

The page keeps the first attempt as what not to do. It also corrects 0.2.1 on
one point. `update.sh`'s backup would fit, because the data compresses about
60:1. What breaks that script is its 120 s health timeout.

## 0.2.1 - docs/mem-shvia-org.md says where the memory server runs and why it is still on 2.1.2

The fork is on `v2.6.6` and the server is not, and nothing in this repository
said where the server is. The page names the machine, the deploy and the pinned
image, and records the 13/10/2026 attempt. V62 rewrites every page version.
After a reflink backup, each rewritten page costs new disk, and a reader left
open pinned the WAL: free space fell from 31 GB to 8 GB in 14 minutes. The
attempt was rolled back with no data lost, and the page lists what a retry needs.
It is a file of our own, so it never conflicts on a sync.

## 0.2.0 - the fork moves onto upstream main, the v2.6.6 release plus nine commits

The fork had sat on `8629adc6` since 25/09/2026, an upstream `main` point
between `v2.4.0` and `v2.4.1`. By 13/10/2026 that was **1,137 upstream commits
and twelve releases behind** (`v2.4.1` through `v2.6.6`). This sync merges
upstream `main` at `d408450d`: the `v2.6.6` release plus nine later commits
(the wrapper no longer checks for updates on the hook path and runs lifecycle
hooks through the native host client, a Windows relay retry, docs and tests).

**It came in as a merge, not a rebase.** Upstream commits keep their own
subjects and hashes, and nothing already published on `origin/main` was
rewritten, so no force-push. It merged clean: our only files, this one and
`docs/ci.md`, have no counterpart upstream. After the merge the tree differs
from upstream `main` in those two files and nothing else. Not a line of our
own code changed, and the bump is still owed (rule 4 of ADR-023).

**This clone had no `upstream` remote**, which ADR-023 makes mandatory. A clone
on the other machine needs the same line before its next sync:

```sh
git remote add upstream https://github.com/akitaonrails/ai-memory.git
git fetch upstream && git merge upstream/main   # then bump the version here
```

## 0.1.0 - docs/ci.md says where this fork's CI runs

The fleet's CI machine is open to every repository since 07/10/2026, this
one included. The rule arrives in a file of **our own** rather than in the
upstream's `CLAUDE.md` or `README.md`: a file they do not have never
conflicts on a sync, and their agent context is theirs.

This repository is **public**, so the page says the part that is not
optional: fork pull request approval has to be on before any job of this
repository runs on that machine. A public repository on a self-hosted
runner without it executes a stranger's pull request with effective root
inside the office network.

## 0.1.0 - the fork gets a version of its own, and the upstream point it sits on

Until now this repository had no version of ours at all. It is a fork we own and
modify, so the `X.Y.Z` of the upstream is theirs and there was nothing recording
what *we* had done to it, or from which point. Both questions matter the moment
the fork breaks: *which upstream point is this, and how far past it are we?*

This file answers both, in the shape [repodocs ADR-023][adr] prescribes: our
version first, the upstream point declared on its own line with the project and
the ref, and no edit to the upstream's own version fields.

At this point the fork carries **no commits of our own** beyond the
upstream — this file and `docs/ci.md` are the first. That is still `0.1.0`
rather than nothing: the version records our repository, and our repository
now exists as something other than a mirror.
