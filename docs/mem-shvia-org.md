# mem.shvia.org — the memory server

> **Status:** `ACTIVE` · Production runs the **upstream's published Docker image**,
> not a build of this fork (the fork carries no code of its own). On 13/10/2026 it
> is still on **`2.1.2`**: the move to `2.6.6` was attempted and rolled back, see
> below.

| | |
|---|---|
| Machine | `blue3site`, `100.64.100.125`, office network only |
| Access | `ssh samir@100.64.100.125`, then `sudo` |
| Public address | `https://mem.shvia.org`, an Apache vhost on the same machine proxying to `http://127.0.0.1:49374/` |
| Deploy | `docker compose` in `/srv/ai-memory`. `docker-compose.yml` holds the bearer token (mode 600); `./data` is bind-mounted at `/data` |
| Image | `akitaonrails/ai-memory:<tag>`, **pinned on purpose**: an upgrade migrates the database one way |
| Data | `data/db/memory.sqlite` is about 45 GB, the wiki about 0.6 GB. `/srv` has about 31 GB free, and the volume group has no free extents |

**Not** `shvia-site` (`100.64.100.242`, the app server), and **not** `170.233.231.20`
(the public IP, which appears in `AI_MEMORY_ALLOWED_HOSTS` and was once read as the
address). `deploy/ai-memory-servidor.md` in shvia-web still names `shvia-site` and
`2.0.0`.

## Why it is still on 2.1.2

`2.6.6` brings schema migrations V61 to V76. Most are additive. V72 and V73 rebuild
`sessions`. The one that matters is **V62's backfill, which rewrites every page
version** (60,199 rows here) in batches of 5,000 before the server accepts any
traffic.

The backup was a reflink copy of `data/` (XFS, instant, no space used at first).
That is the trap: after a reflink copy, **every page the migration writes costs
new disk**, because the live file stops sharing those blocks with the copy. That
comes on top of the WAL. A long read transaction (a `dbstat` scan started for
sizing) was also open on the file, so checkpoints could not reset the WAL: 13.6 GB
of WAL after 20,000 pages, with free space down from 31 GB to 8 GB. The container
was stopped at 16:26 UTC and the copy swapped back in. Afterwards the service was
healthy, with the same workspaces and counts and schema 60. Downtime was
16:12–16:29 UTC.

## What a retry needs

1. **Nothing else holding the database open** during the migration, not even a
   read-only `sqlite3`: one reader pins the WAL. `ai-memory-web` reads this file
   directly; stop it or confirm there are no open handles.
2. **A backup that does not share blocks with the live file**, which rules out a
   reflink copy. Either stream it off the machine with the service stopped
   (`tar -C /srv/ai-memory -cf - data | zstd -T0 | ssh <host> 'cat > ai-memory-2.1.2.tar.zst'`,
   which is byte-exact, so rollback is unpack and the old tag), or add disk to `/srv` first.
3. **Migration in place with a free-space watchdog** that stops the container
   below 4 GB free. Expect downtime equal to the backup plus the V62 backfill:
   45 s to 2.5 min per 5,000 pages on this single-CPU machine. The `2.6.6` image
   is already pulled.

Rollback: stop, restore `data/`, put the old tag back, `docker compose up -d`. A
pre-2.6 binary does not open a migrated database.

## Checks, before and after

With the bearer: `GET /api/v1/workspaces`, `GET /api/v1/search?q=…`,
`POST /mcp` (`initialize`). Run them directly on `127.0.0.1:49374` and through
Apache with `curl --resolve mem.shvia.org:443:127.0.0.1 https://mem.shvia.org/…`.
Expected: 200, and 401 without the token. That is what `2.1.2` answered before and
after the rollback.

`/srv/ai-memory/update.sh` predates the current database size. It tars the whole
data directory onto the same disk, which no longer fits, and it pulls whatever tag
the compose file names.
