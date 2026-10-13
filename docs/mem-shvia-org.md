# mem.shvia.org — the memory server

> **Status:** `ACTIVE` · Production runs the **upstream's published Docker image**,
> not a build of this fork (the fork carries no code of its own). Since
> 13/10/2026 18:02 UTC that image is **`2.6.6`**, the release this fork's
> upstream point contains.

| | |
|---|---|
| Machine | `blue3site`, `100.64.100.125`, office network only |
| Access | `ssh samir@100.64.100.125`, then `sudo` |
| Public address | `https://mem.shvia.org`, an Apache vhost on the same machine proxying to `http://127.0.0.1:49374/` |
| Deploy | `docker compose` in `/srv/ai-memory`. `docker-compose.yml` holds the bearer token (mode 600); `./data` is bind-mounted at `/data` |
| Image | `akitaonrails/ai-memory:2.6.6`, **pinned on purpose**: an upgrade migrates the database one way |
| Data | `data/db/memory.sqlite` is about 45 GB: 1,444 latest pages (60,298 versions) and 655,901 observations. The wiki is about 0.6 GB. `/srv` has about 30 GB free, and the volume group has no free extents |

**Not** `shvia-site` (`100.64.100.242`, the app server), and **not** `170.233.231.20`
(the public IP, which appears in `AI_MEMORY_ALLOWED_HOSTS` and was once read as the
address). `deploy/ai-memory-servidor.md` in shvia-web still names `shvia-site` and
`2.0.0`.

## Upgrading: what worked on 13/10/2026, from 2.1.2 to 2.6.6

The script is on the server, `/srv/ai-memory/upgrade-2.6.6.sh`, with its log next
to it. It is the template for the next upgrade: change the two tags.

1. Run the checks below, stop the container, and confirm that nothing else holds
   the database open.
2. **Take a cold backup, compressed and verified, on `/srv` itself:**
   `tar --exclude=data/logs -cf - data docker-compose.yml | zstd -3 --long=27 -T0`,
   then `zstd -t --long=27`. The data compresses about 60:1. 45 GB became
   751 MB in five minutes, so it fits on the same disk with room to spare.
   Decompressing needs `--long=27` too.
3. Switch the tag in `docker-compose.yml`, `docker compose up -d`, and watch free
   space. The API answers nothing until the startup migrations finish. The
   script stops the container below 4 GB free.
4. Run the checks again. The service was down for **38 minutes** (17:24 to
   18:02 UTC). The V62 backfill took 33 of them: 60,199 page versions in 13
   batches, slowing from 30 s to 8 min a batch. Extra disk peaked near 3 GB.

Rollback, which was not needed: stop; delete `data/db`;
`zstd -dc --long=27 backup-2.1.2-20261013-142356.tar.zst | tar -C /srv/ai-memory -xf - data`;
restore `docker-compose.yml.bak-20261013-142356-pre-2.6.6`; `docker compose up -d`.
A pre-2.6 binary does not open a migrated database. The `2.1.2` image is still on
the machine.

## What not to do: the first attempt, same day

It was rolled back after 14 minutes, with nothing lost. The backup was a reflink
copy of `data/` (XFS: instant, no space used at first). After a reflink copy,
**every page the migration writes costs new disk**, because the live file stops
sharing those blocks with the copy, and V62 rewrites every page version. On top
of that, a `dbstat` scan started for sizing held a read transaction open, which
pinned the WAL. There were 13.6 GB of WAL after 20,000 pages, and free space fell
from 31 GB to 8 GB.

- **No other process may hold the database open during a migration**, not even
  a read-only `sqlite3`. `ai-memory-web` reads per request and did not get in
  the way.
- **No reflink copy as the backup** of a migration that rewrites much.
- **Not `/srv/ai-memory/update.sh`.** Its backup would fit, given the
  compression, but it waits 120 s for health. A migration like V62 takes half an
  hour, so the script would declare failure in the middle of it.

## Checks, before and after

With the bearer: `GET /api/v1/workspaces`, `GET /api/v1/search?q=…` and
`POST /mcp` (`initialize`). Run them directly on `127.0.0.1:49374` and through
Apache with `curl --resolve mem.shvia.org:443:127.0.0.1 https://mem.shvia.org/…`.
Expected: 200, and 401 without the token. Then:

- `docker exec ai-memory ai-memory status` shows FTS and embedding coverage, the
  write queue and the ingest counters.
- `ai-memory-web` reads the file as `www-data` through the `aimemory-read` group:
  `sudo -u www-data sqlite3 -readonly data/db/memory.sqlite 'SELECT COUNT(*) FROM pages WHERE is_latest=1'`.

On 13/10/2026 every check matched before and after. The workspaces were default
125 projects / 1,392 pages, samirhv-shvia 21 / 41 and shvia 1 / 4. In the first
minutes after the restart, 104 hook events were accepted and stored, with none
failed or unauthorized. 2.6.x logs one `WARN` at start about auth on a plain-HTTP
bind. That is expected in this layout, where TLS ends at Apache.
