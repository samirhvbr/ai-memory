# Version — samirhvbr fork of ai-memory

**Current version:** `0.2.1`
**Upstream:** [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) @ `d408450d` (`main`: the `v2.6.6` release plus nine commits)

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
