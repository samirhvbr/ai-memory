# mem.shvia.org — the memory server

> **Status:** `ACTIVE` · Production runs the **upstream's published Docker image**,
> not a build of this fork (the fork carries no code of its own). Since
> 27/10/2026 22:06 UTC that image is **`3.2.8`** (schema 88). Before that it was
> `2.6.6`, from 13/10. The fork's code has since moved on to upstream `3.2.10`
> and 38 commits (version `0.3.3`); the server has not.

| | |
|---|---|
| Machine | `blue3site`, `100.64.100.125`, office network only |
| Access | `ssh samir@100.64.100.125`, then `sudo` |
| Public address | `https://mem.shvia.org`, an Apache vhost on the same machine proxying to `http://127.0.0.1:49374/` |
| Deploy | `docker compose` in `/srv/ai-memory`. `docker-compose.yml` holds the bearer token (mode 600); `./data` is bind-mounted at `/data` |
| Image | `akitaonrails/ai-memory:3.2.8`, **pinned on purpose**: an upgrade migrates the database one way |
| Data | `data/db/memory.sqlite` is about 45 GB: 1,444 latest pages (60,298 versions) and 655,901 observations. The wiki is about 0.6 GB. `/srv` has about 30 GB free, and the volume group has no free extents |

**Not** `shvia-site` (`100.64.100.242`, the app server), and **not** `170.233.231.20`
(the public IP, which appears in `AI_MEMORY_ALLOWED_HOSTS` and was once read as the
address). `deploy/ai-memory-servidor.md` in shvia-web still names `shvia-site` and
`2.0.0`.

## Upgrading: what worked on 27/10/2026, from 2.6.6 to 3.2.8

`/srv/ai-memory/upgrade-3.2.8.sh`, with its log next to it, ran the procedure
below unattended. All times UTC.

| Step | Time |
|---|---|
| Image pulled while 2.6.6 still served | 21:44:14 |
| Checks before, then stop | 21:44:19 – 21:44:20 |
| Cold backup `backup-2.6.6-20261027-184414.tar.zst`, verified | 21:44:22 – 21:49:27, **825 MB** |
| `3.2.8` started; V77 to V88 | 21:49:27 – **22:05:58**, when the API answered |
| Checks after and the `ai-memory-web` probe | 22:05:58 – 22:06:02, all green |

Down for **21 minutes 38 seconds**: 5 for the backup, 16 for the migrations. The
rehearsal had predicted about 15 for the migrations. Free space stayed at 28 GB,
and the WAL was empty until the server came up. The container reports
`unhealthy` while it migrates, as it did on 13/10; that is the API not answering
yet, not a failure.

- Before and after, directly and through Apache: `workspaces` and `search` 200,
  401 without the token, MCP `initialize` 200. Workspaces: default 136 / 950,
  samirhv-shvia 23 / 41, shvia 1 / 2, the same on both sides.
- `refinery_schema_history` ends at 88, and the `ai-memory-web` probe printed
  `array ()`.
- `status` after: 993 latest pages (60,759 versions), 3,063 sessions, 794,432
  observations, FTS complete, `auth: bearer token`.
- While the server was down, Apache answered the hooks with 500 and 502. From the
  first minute back the hooks flushed what they had held: 125 events accepted
  and stored, none failed, in the first minute.

Rollback, which was not needed: stop; delete `data/db`;
`zstd -dc --long=27 backup-2.6.6-20261027-184414.tar.zst | tar -C /srv/ai-memory -xf - data`;
restore `docker-compose.yml.bak-20261027-184414-pre-3.2.8`; `docker compose up -d`.
A 2.x binary refuses a store migrated to 3.x. The `2.6.6` image is still on the
machine.

**Still to do: the clients.** Each machine with the hooks keeps its own 2.x
client until `ai-memory upgrade` runs there.

## The 3.2.8 rehearsal, 27/10/2026

The fork moved onto `v3.2.8` (version `0.3.0`). Before touching the server, the
upgrade was rehearsed on a workstation, on a copy of the 13/10 cold backup
(`backup-2.1.2-20261013-142356.tar.zst`, checksum verified), first brought to
`2.6.6` the way production is, then started on `3.2.8`:

| | Result |
|---|---|
| Migrations | V77 to V88, applied on the first start; `refinery_schema_history` ends at 88 |
| Time to the API answering | **4 min 17 s** on the workstation. The same machine ran the 2.6.6 step in 9 min 31 s, which took 38 min on the server, so expect roughly **15 minutes** there, plus the five-minute backup |
| Extra disk | none: the database stayed at 43 GB through the migration |
| Counts | the same before and after: 1,437 pages (60,199 versions), 2,955 sessions, 655,798 observations, FTS complete |
| Checks | `workspaces`, `search` and MCP `initialize` 200 with the bearer, 401 without it; workspaces default 125 / 1,392, samirhv-shvia 21 / 41, shvia 1 / 4 |
| `ai-memory-web` | the schema probe returns `array ()` against schema 88, in 1.4 s |
| Auth | `AI_MEMORY_AUTH_TOKEN` in the environment still authenticates; `status` now prints `auth: bearer token` |

The probe needs PHP with `pdo_sqlite`; the workstation has none, so it ran in
`php:8.4-cli`. A probe that cannot open the database reports `could not find
driver` for every read, which is a missing tool, not a schema answer.

What changes for clients: nothing has to change first. Upgrade the server, then
run `ai-memory upgrade` on each machine with the hooks. In 3.x `memory_query`
also searches observations by default; `[retrieval] observation_stream = false`
restores the 2.x ranking.

The script is `upgrade-3.2.8.sh`, the 2.6.6 one with the tags changed, the image
pulled before the stop so the download is not downtime, and the
`ai-memory-web` probe added to the after-checks.

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
- `ai-memory-web` (`/srv/www/admin.shvia.org/ai-memory-web`) reads the file as
  `www-data` through the `aimemory-read` group. Its schema canary needs
  phpunit, which the production checkout does not have. The probe behind the
  canary runs with a plain bootstrap, though, and repeats every read the panel
  makes, read-only:

  ```sh
  cd /srv/www/admin.shvia.org/ai-memory-web
  sudo -u www-data env HOME=/tmp php -r 'require "vendor/autoload.php"; $app = require "bootstrap/app.php";
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
    require "tests/Support/AiMemorySchemaProbe.php";
    var_export(Tests\Support\AiMemorySchemaProbe::failures());'
  ```

  `array ()` is the pass.
- Apache keeps no log of its own for this vhost. Requests land in
  `/var/log/apache2/other_vhosts_access.log` under `mem.shvia.org:443`.

On 13/10/2026 every check matched before and after. The workspaces were default
125 projects / 1,392 pages, samirhv-shvia 21 / 41 and shvia 1 / 4. The
ai-memory-web probe found no failures against schema 76, in 17 s. In the first
38 minutes after the restart:

- Apache served 1,144 requests to the vhost, all 2xx apart from the checks' own
  no-token probes.
- The server accepted and stored 1,109 hook events, with none failed or
  unauthorized.

2.6.x logs one `WARN` at start about auth on a plain-HTTP bind. That is expected
in this layout, where TLS ends at Apache.
