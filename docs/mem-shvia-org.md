# mem.shvia.org — the memory server

> **Status:** `ACTIVE` · Production runs the **upstream's published Docker image**,
> not a build of this fork (the fork carries no code of its own). Since
> 02/11/2026 16:38 UTC that image is **`3.3.1`** (schema 96). Before that it was
> `3.2.8` (27/10) and `2.6.6` (13/10). The fork's code is upstream `main` at
> `v3.4.2` plus one commit (version `0.3.6`), so the server is one step behind:
> the `3.4.2` rehearsal is recorded below and the upgrade itself is not done yet.

| | |
|---|---|
| Machine | `blue3site`, `100.64.100.125`, office network only |
| Access | `ssh samir@100.64.100.125`, then `sudo` |
| Public address | `https://mem.shvia.org`, an Apache vhost on the same machine proxying to `http://127.0.0.1:49374/` |
| Deploy | `docker compose` in `/srv/ai-memory`. `docker-compose.yml` holds the bearer token (mode 600); `./data` is bind-mounted at `/data` |
| Image | `akitaonrails/ai-memory:3.3.1`, **pinned on purpose**: an upgrade migrates the database one way |
| Data | `data/db/memory.sqlite` is about 45.7 GB (42.6 GiB): 909 latest pages (61,080 versions) and 839,441 observations on 02/11/2026. The file grew by about 100 MB between 27/10 and 02/11. The wiki is about 0.6 GB. `/srv` has about 25 GB free, and the volume group has no free extents |

**Not** `shvia-site` (`100.64.100.242`, the app server), and **not** `170.233.231.20`
(the public IP, which appears in `AI_MEMORY_ALLOWED_HOSTS` and was once read as the
address). `deploy/ai-memory-servidor.md` in shvia-web still names `shvia-site` and
`2.0.0`.

## The machine, measured on 02/11/2026

`blue3site` is a **Hyper-V guest** (the ACPI tables read `VRTUAL MICROSFT`), and it
is not dedicated to this server.

| | |
|---|---|
| CPU | 8 vCPU: Intel Xeon Silver 4214R @ 2.40 GHz, 1 socket, 4 cores × 2 threads as the guest sees it |
| Memory | 7.7 GiB (7,850 MB) and 1.9 GiB of swap, none in use. About 6.8 GB of it is page cache, mostly the database |
| Disk | One 126 GB virtual disk, LVM: `/srv` 94.5 GB (69 GB used), `/` 7.6 GB (79% used), `/var` 7.6 GB, `/var/log` 11.4 GB, `/tmp` 1.9 GB, `/boot` 976 MB |
| Also on it | Apache, PHP-FPM 8.4, MariaDB, `notes-server`, `fail2ban`. The `ai-memory` container is the only Docker container |
| ai-memory footprint | 250 MiB of memory and 0.4% CPU a minute after the 3.3.1 start. CPU and memory pressure (PSI) read 0; IO pressure read 4 to 6% only while the cold backup ran |

What limits this server is **IO and the one-way, offline upgrade**, not CPU or
memory: a 45 GB SQLite file on a single virtual disk, with the only backups on
the same volume (`/srv`). An upgrade needs the container stopped for the backup,
so the downtime is the backup time (about 2 min 40 s of `tar` plus 50 s of
verification on 02/11).

On 02/11/2026 the guest restarted twice within two minutes, the first time
abruptly (below). The cause is not established. The guest journal shows no panic,
no out-of-memory kill and no disk error (the `fd0` I/O error is the virtual
floppy), so the place to look is the Hyper-V host, which this repository cannot see.

The guest restarted once more on 04/11/2026 at 16:42 (-03): the journal of the
previous boot ends at 16:42:17 and the next boot starts at 16:42:29, so it was an
orderly restart this time. The container came back by itself (`Up 25 hours` the
next day) and the log holds no `ERROR` line. The cause is not established either.

## Rehearsal for 3.3.1 to 3.4.2, 05/11/2026

The range is `v3.3.1` to `v3.4.2` (five releases): three new migrations, V97 to
V99. V98 creates `query_page_signals`, a small table, and V99 adds a nullable
`observations.file_path` with a partial index; neither rewrites a table. **V97
drops and rebuilds `pages_fts` and `observations_fts`** to stop treating `/` as a
token character, so `ops.rs` and `ops` now match `crates/store/src/ops.rs`. That
rebuild reads every page version and every observation, which is why this range
is minutes and the last one was seconds.

Rehearsal on a workstation, on the cold backup taken just before the `3.3.1`
upgrade (schema 88, 45.7 GB), first brought to `3.3.1` and then to `3.4.2`. The
token was a fake one and the copy was deleted afterwards:

| | Result |
|---|---|
| `3.3.1` on the copy (V89 to V96) | applied within about a second; the counts were those of production on 02/11: 909 latest pages, 3,089 sessions, 839,396 observations |
| `3.4.2` start to "ready" (V97 to V99) | **7 min 38 s** (20:40:14 to 20:47:52 UTC). The log has no per-migration times, but V98 and V99 are instant by their text, so this is V97 |
| Write-ahead log | grew steadily to **5.37 GB** at the end of V97, then the checkpoint cut it back to 64 MB. `memory.sqlite` went from 45,736,001,536 to 45,743,325,184 bytes, **7 MB more**: the pages freed by the dropped indexes are reused. The workstation's free space dipped by up to 15 GB in the last minute and came back; I could not attribute all of it to the WAL, so treat 5.4 GB as the floor and 15 GB as the ceiling. On the server's XFS `/srv` (about 24 GB free once the backup is written) the script's watchdog stops the container below 4 GB |
| Restart with nothing to migrate | healthy in **7 s**, no `ERROR` in the log |
| Counts after | 909 latest pages, 3,089 sessions, 839,396 observations, workspaces `default` 138 / 866, `samirhv-shvia` 24 / 41, `shvia` 1 / 2: the same as before |
| Index | `status`: FTS 61,172 / 61,172 pages and 839,396 / 839,396 observations, 0 latest pages missing an embedding. `PRAGMA quick_check` `ok`, and the FTS5 `integrity-check` `ok` on both indexes |
| New tokenizer | `observations_fts` matched the phrase `memory sqlite` in 182 observations, `docker-compose yml` in 738 and `src main rs` in 573 |
| HTTP | `workspaces` and `search` 200, 401 without the token, MCP `initialize` 200 (`serverInfo` `3.4.2`, 27 `memory_*` tools). A bare `server/discover` POST answers `-32601`, as the `3.3.1` production log already shows for the probes clients send |
| Search API | seven queries (`sqlite`, `memory.sqlite`, `docker-compose.yml`, `upgrade-3.2.8.sh`, `src/main.rs`, `ai-memory`, `memory sqlite`) returned the same number of hits as production's `3.3.1`: 4, 0, 0, 0, 0, 5, 5 |
| `ai-memory-web` probe | `array ()` with the **deployed** `0.1.6` code against schema 99, plus a positive control (a missing database path made it list the failures). The first run listed failures against the production database path, because the copied tree carried the production `bootstrap/cache/config.php`, which pins it; deleting that cache file in the copy made the probe read the rehearsal database |
| Client `2.5.2` | its shell hooks stored one session with 5 observations (`session-start`, `user-prompt`, `post-tool-use`, `stop`, `session-end`) in `default/ensaio-hooks-teste`, created the summary page, left the spool empty, and redacted a fake `db_password` inside a Claude Code-shaped tool result (the `3.3.3` fix) |

After the start the server ran its scheduled maintenance, which is not a fault:
the forget sweep evicted 52 pages, the hollow-project sweep removed 4 empty
project rows and 432 abandoned sessions were closed, so `default` read 135 / 814
afterwards. The copy was three days older than the clock, and production's own
sweep had evicted 25 pages at 15:08 UTC that day. The count of page versions also
rose by 143 across the two starts (61,029 to 61,172) with the same 909 latest
pages: the earliest rows touched were per-project `index.md` pages written at
20:40:00 UTC, so I take them to be regenerated indexes. That was not checked
further, because the copy is gone.

**What it means for production.** The server runs about 3.5 to 4 times slower
than this workstation (V77 to V88 took 4 min 34 s here and about 16 min there),
so V97 should take **27 to 32 minutes**, plus about 4 minutes of cold backup and
verification: **roughly 31 to 36 minutes down**, against 4 minutes for `3.3.1`.
`/srv/ai-memory/upgrade-3.4.2.sh` is the `3.3.1` script with the tags changed and
the expected schema 99 (it was only copied and syntax-checked; the diff against
the `3.3.1` one is the header comments and that one line).

## Upgrading: 3.2.8 to 3.3.1 on 02/11/2026

The range was `v3.2.8` to `v3.3.1`: eight new migrations, V89 to V96. V89 rebuilds
`sessions` (about 3,000 rows) and V95 rebuilds `agent_messages` (empty); the other
six add columns, indexes or small side tables. None touches `observations` or
`pages`, which is why this was seconds and not the sixteen minutes of V77 to V88.

**Rehearsal**, on a workstation, on a copy of the 27/10 cold backup (the 2.6.6
state), first brought to `3.2.8` and then to `3.3.1`:

| | Result |
|---|---|
| Start to "ready" on `3.3.1` | **2.1 s** (V89 to V96 applied together). On `3.2.8` the same copy had taken 4 min 34 s |
| Counts before and after | identical: 895 latest pages (60,659 versions), 794,307 observations, 3,063 sessions; workspaces `default` 122 / 852, `samirhv-shvia` 23 / 41, `shvia` 1 / 2 |
| HTTP | `workspaces` and `search` 200, 401 without the token, MCP `initialize` 200 |
| Index | FTS complete (60,752 / 60,752 pages; 794,311 / 794,311 observations), 0 latest pages missing an embedding |
| Wiki on disk | 0 of 46,929 files modified by the start |
| `ai-memory-web` probe | `array ()` with the **deployed** `0.1.6` code, plus a positive control (a missing database path made it report failures) |
| Client `2.5.2` | its shell hooks (`session-start`, `user-prompt-submit`, `post-tool-use`, `session-end`) stored one `claude-code` session with 4 observations and left the spool empty |

The native `ai-memory hook` subcommand of `2.5.2` failed with "error sending
request" before opening a socket, against a `3.2.8` server just the same, so it is
not a `3.3.x` regression. It is not what the machines run (their hooks are the
shell scripts), and it stayed untested.

**Production**, in three runs of `upgrade-3.3.1.sh` (all UTC):

| Run | What happened |
|---|---|
| 15:36:22 | Aborted at 15:41:35 in the backup step. `tar` reported that `memory.sqlite-wal` and `-shm` had been removed while it read, and that `data/db` changed; the script treated any `tar` warning as a failure, removed the partial archive and started `3.2.8` again. Nothing else had changed. Down 5 min 7 s |
| 15:43:41 | The backup finished (15:48:50). The VM stopped abruptly at about 15:49:47: the journal ends with no shutdown messages, and the cause is not established. It booted at 15:50:49, shut down in an orderly way at 15:51:13 and booted again at 15:54:50. The container had been stopped by the script, so it was started by hand between the two boots; the memory server was out of service for about 12 minutes. The data was intact (the same counts as before, FTS complete) and the archive that finished before the reset verified (`zstd -t`, `memory.sqlite` at its full 45,733,642,240 bytes) |
| 16:34:02 | **Completed**, started by the owner from the root console with the same `systemd-run` command. Stop 16:34:04; `tar` 16:34:06 to 16:36:47; verified and `backup ok: 850M` at 16:37:38; `3.3.1` started 16:37:38 and answered at 16:38:22; healthy 16:39:14; `DONE` 16:39:31 |

Downtime of the last run: **about 4 min 18 s** (16:34:04 to 16:38:22). The
checks matched before and after, directly and through Apache: `workspaces` 200,
`search` 200, 401 without the token, MCP `initialize` 200; workspaces
`default` 138 / 866, `samirhv-shvia` 24 / 41, `shvia` 1 / 2. Counts: 909 latest
pages, 3,089 sessions and schema 88 before; 909, 3,089 and schema **96** after,
with observations 839,396 and 839,418 (events that arrived in between). The
`ai-memory-web` probe printed `array ()`. After the start, `status` showed FTS
complete, 0 errors in the container log and 45 events accepted and stored with
none failed; this session's own MCP tools (`memory_status`, `memory_query`)
answered through `mem.shvia.org`.

What the two interrupted runs changed in the script, now in
`/srv/ai-memory/upgrade-3.3.1.sh`:

- The "before" numbers come from `ai-memory status` on the **running** server.
  Nothing opens the database file while it is stopped: any `sqlite3` or PHP reader
  that does so creates and removes `-wal` and `-shm` files, which is what `tar`
  tripped on. (A read-only query run by hand during the final backup did create
  empty ones, with the database's owner and group, so the container could use them.)
- The backup excludes `memory.sqlite-wal` and `memory.sqlite-shm`, after checking
  that no non-empty WAL exists. It accepts `tar` exit status 1 only if the size
  and modification time of `memory.sqlite` did not change during the copy, and it
  checks that the archive lists `memory.sqlite` at its full size.
- It is launched with `systemd-run` and a log file, never as a background job of
  an SSH session: the first launch left the SSH session hanging, and a unit
  survives the session dropping.

Rollback, not needed: stop; delete `data/db`;
`zstd -dc --long=27 backup-3.2.8-20261102-133402.tar.zst | tar -C /srv/ai-memory -xf - data`;
restore the `docker-compose.yml.bak-…-pre-3.3.1` the script wrote; start with the
`3.2.8` image. A `3.2.x` binary refuses a store migrated to `3.3.x`. The archive of
the interrupted second run (`backup-3.2.8-20261102-124341.tar.zst`, 849 MB,
verified) is also on the machine, 50 minutes older.

**Still to do: the clients.** The machines keep their `2.x` clients, which work
with this server (shown above), until `ai-memory upgrade` runs on each. `ai-memory
status` from `3.x` warns when client and server differ in major version.

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
