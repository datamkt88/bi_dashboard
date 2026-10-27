# B2C Marketing & OP: daily refresh runbook

This is a handoff pack. With it, any Claude conversation on any computer can refresh the **B2C Marketing & OP** dashboard: it pulls the data from Power BI, rebuilds the HTML, checks it, and publishes it.

Last good build: **27 Oct 2026, data pulled 16:25 MYT** (run folder `r27c`).

---

## 0. Where everything lives

| What | Where |
|---|---|
| Published dashboard (single HTML, about 30 MB) | GitHub `datamkt88/bi_dashboard` (private), branch **`main`**, file `index.html` |
| This pack: scripts, state, raw pulls, queries | the same repo, branch **`pipeline`** |
| Artifact copy of the dashboard | https://claude.ai/artifact/U2tWfjN39JkawcfuKumBDq (built by `make_art.py`) |
| This runbook (copy) | claude.ai project "Marketing & Ops Report", doc `claude/b2c-dashboard-refresh-runbook.md` |
| Power BI | Fabric workspace **B2C-AI**: models `AI Report_Marketing` (MK) and `AI Report_Product` (PR). Workspace **B2C-Player Profile**: model `Player Profile 360` (PP) |

The repo contains player IDs and revenue, so **keep it private**.

---

## 1. One-time setup on a new laptop

1. Install the **Claude desktop app** and sign in with the same account (nova88best@gmail.com).
2. In Claude desktop, add the **Power BI Modeling MCP server** (`powerbi-modeling-mcp`). It must appear in the conversation as `powerbi-modeling-mcp__connection_operations` / `dax_query_operations`.
3. In a browser on that laptop, sign in to Power BI / Fabric with the account that can read the two workspaces. The first `ConnectFabric` call opens a sign-in prompt **on the laptop**. Someone has to accept it, or calls time out.
4. In claude.ai, make sure **GitHub is connected** (Settings → Connectors) so the session can reach `datamkt88/bi_dashboard`.
5. Start the conversation **inside the project "Marketing & Ops Report"**. Open it in the desktop app on that laptop and choose **"Link to this computer"**. The cloud session reaches Power BI only through the linked laptop.
6. If a scheduled refresh will run on this laptop, it must be **awake, online and have Claude desktop open** at 09:00.

---

## 2. Start of every session (cloud workspace)

```bash
cd /home/claude
git clone -b pipeline https://github.com/datamkt88/bi_dashboard pipe   # needs the repo attached to the session (add_repo, push access)
cd pipe
git show origin/main:index.html > B2C-Marketing.html                   # the current dashboard = the pipeline's state
npm install                                                            # chart.js + playwright for the page check
export PYTHONPATH=. CHROMIUM=/opt/pw-browsers/chromium                 # CHROMIUM = whatever chromium the container has
```

Connect the three models (names get a suffix such as " 4"; use the name the tool returns):

```
connection_operations  ConnectFabric  workspace "B2C-AI"                model "AI Report_Marketing"   -> MK
connection_operations  ConnectFabric  workspace "B2C-AI"                model "AI Report_Product"     -> PR
connection_operations  ConnectFabric  workspace "B2C-Player Profile"    model "Player Profile 360"    -> PP
```

If a query returns "Refreshing the expired access-token has failed", reconnect. If calls say the device did not respond, the laptop is asleep or waiting on a sign-in.

---

## 3. Daily run (same month): step by step

`D` is the report date (normally today; the dashboard treats `D` as the partial day). `NN` is the new run folder, e.g. `r28`.

### 3.1 Generate the queries

```bash
python3 queries.py 2026-10-28          # writes queries/*.dax + queries/INDEX.txt (connection + expected header for each)
```

### 3.2 Run the pulls

Run each `queries/<name>.dax` with `dax_query_operations` → `Execute`, `maxRows 300000`, `timeoutSeconds 300`, on the connection listed in INDEX.txt.

- **Each result must be saved to a file.** The tool saves results bigger than its inline limit to `tool-results/...-<id>.txt`. Small queries carry a `"pad",REPT("x",150)` column so they are always big enough. If a result still comes back inline, raise the pad to `REPT("x",400)`.
- The pulls are read-only, so retrying one is harmless.
- `pcD1` / `pcD2` / `pcD3` are per-customer daily chunks. If a chunk times out, cut its date range smaller.
- Then copy the results into the pack and note each id:

```bash
python3 grab.py /root/.claude/projects/<proj>/<session>/tool-results    # prints id | rows | header for each new pull
```

Write `ids_rNN.json` with the same keys as `r27c/ids.json`: `date`, `time` (MK/PR pull time `HH:MM`), `time2` (PP pull time), then one id per pull. `pcD` is a list of 1 to 3 chunk ids, in date order.

| key | query | conn | key | query | conn |
|---|---|---|---|---|---|
| exec | exec.dax | MK | pcM | pcM.dax | PR |
| mkt | mkt.dax | MK | pcD | pcD1..3.dax | PR |
| pc_oct | pc_oct.dax | MK | list1, list2 | list1/list2.dax | PP |
| drows | drows.dax | MK | tags | tags.dax | PP |
| srows | srows.dax | MK | l2 | l2.dax | PP |
| aff | aff.dax | MK | RM, FM | RM/FM.dax | PP |
| bonus | bonus.dax | MK | FD_daily | FD_daily.dax | PP |
| vipm_fd, vipm_nr | vipm_*.dax | MK | base | base.dax | PP |
| mg_m, mg_d | mg_*.dax | MK | T C P V VC VP | T..VP.dax | PR |
| RDoct, RD_daily | RD*.dax | MK | | | |

### 3.3 Make the run folder and build

```bash
python3 newrun.py r27c r28 ids_r28.json   # previous folder -> new folder; prints every id/date swap. Check them.
bash run.sh r28
```

`run.sh` runs these steps in order:
prep (CSVs, customer bitmask, daily rows) → `ref_exec` → `ref_mkt` → `build_custs` → `mk` → `ref_prod` + pmdata insert → segment check → `build_seg` → `build_top2` → VIP state → `build_vip2s` / `build_vip3s` → `build_mg` / `mg_rd` → `final` → page check (`t60.js`).

If it stops with **"customers missing from the segment map"**:

1. Put the ids from `rNN/miss.txt` into `queries/_missmap_TEMPLATE.dax` in place of `{IDS}`, and run it on PP.
2. `python3 grab.py ...`, then `python3 prep.py mapadd <id>`.
3. Restart from that point with `FROM=seg bash run.sh rNN`.

### 3.4 What good output looks like (stop and investigate if not)

- **mk:** `2026-10-xx old N new N row diffs 0` for every older day. Only the last one or two days may differ, because the partial day fills in. `master list 49x`. No `Traceback`.
- **ref_prod:** per-day `p a -> a` unchanged for older days. Only `D-1` and `D` move. `miss set()`.
- **build_seg:** every `m/d T C P V VC VP (x, x, 0, [])`. The **third number must be 0**: the segment cubes have to reconcile with the product cube.
- **vip2s:** `FDU cust rows X exec X | NRU Y Y` (equal pairs). `saba mismatch 0`.
- **build_mg:** `mismatches 0`.
- **mg_rd:** `missing 2` on `m` is known and accepted (Sep redepositors 11,171 vs 11,179). `Depr mismatch 0`.
- **t60.js:** `errors []` and a K2 line with real numbers.
- Output: `B2C-Marketing.html`, about 30 MB.

### 3.5 Publish

```bash
cp B2C-Marketing.html "/mnt/user-data/outputs/B2C Marketing & OP.html"     # then SendUserFile to the user
# dashboard -> main
git fetch origin main && git worktree add ../site origin/main && cp B2C-Marketing.html ../site/index.html
cd ../site && git add index.html && git commit -m "Refresh dashboard data to <D> <time>" && git push origin HEAD:main && cd ../pipe
# artifact (same URL every time)
python3 make_art.py B2C-Marketing.html     # -> art/index.html + art/d_*.js (each < 16 MB)
```

Republish the artifact with the Artifact tool:

- `url` = https://claude.ai/artifact/U2tWfjN39JkawcfuKumBDq
- `file_path` = `art/index.html`
- `files` = every `art/d_*.js`

A new conversation must `read` the artifact first. Optionally check the page with `tart2.js` after serving `art/` over http.

### 3.6 Save the state back (do not skip this)

The next run, wherever it happens, starts from this branch:

```bash
git add -A raw state r28 ids_r28.json *.json *.csv pmtop.b64 build_top.py queries
git commit -m "pipeline state after <D> <time> run" && git push origin HEAD:pipeline
```

`B2C-Marketing.html` itself is **not** committed to `pipeline`. It lives on `main` as `index.html`.

Commit identity used so far:

```
git -c user.name="datamkt88" -c user.email="nova88best@gmail.com" commit ...
```

### 3.7 If anything fails

If Power BI is unreachable, a sign-in is pending, or a validation line in 3.4 is wrong:

- **Publish nothing.** The live dashboard stays on the last good build.
- Tell the user in one short message what is needed (e.g. "please wake the laptop and accept the Power BI sign-in").
- `run.sh` makes `bak_before_rNN.html` before it starts, so `cp bak_before_rNN.html B2C-Marketing.html` undoes a half-finished build.

---

## 4. Query calibration (done 27 Oct 2026 16:25)

All 29 pulls in `queries.py` were run on 27 Oct 16:25 and compared with the 12:16 pulls:

- Headers and row structure are identical.
- Past months and days match apart from floating-point noise. MK/PR monthly September is identical.
- The PP lifetime values and the last days differ only because they are live.

Four column names were corrected during calibration:

- `Acquisition Report Consolidate New[Impressions]`
- `Acquisition Report Consolidate New[Clicks/Views]`
- master list `[SiteName]`
- master list `[Owner (Eg)]`

The full 16:25 build passed every check in 3.4. If a query errors after the model changes, run the matching `queries/_schema_*.dax` to list the real column names. Fix `queries.py` and commit it.

Notes:

- `base` (48 rows) needs a big pad (`REPT("x",2500)`) to be saved to a file. `queries.py` already does this.
- `pcD` chunks are 10 days, then 6-day pieces. A 12-day chunk timed out once.

## 5. Month rollover (first run in November): not automated yet

`newrun.py` refuses to cross a month on purpose. Do the 1 Nov run **interactively with the user present**, not unattended.

These are the places tied to October:

- **FX:** `D['fx']` needs `2026-11|<CurrencyId>` rates for every currency. They come from the exec/model FX (RateType 2). Check that `ref_exec` / `mk` find them; a `KeyError: '2026-11|..'` means they are missing.
- **Month lists:** `PM['m']` and `PM['cd']['m']` (product), the data-block month lists, `build_vip2s/3s` month loop `(2026,10)`, `build_mg` `partial`, and RM/FM/mg 14-month windows (queries.py shifts these automatically).
- **Customer bitmask** (`build_custs`, `prep.py custs`): Oct is bit 12. Nov is bit 13.
  - Set `state/config.json` to `{"cut":"2026-11-01","month":"2026-11","month_bit":13}`.
  - Make `state/custs_base.json` = the last October `rNN/custs_in.json`, so final October actives are frozen.
  - `build_custs.py` compares bits `0xFFF`; widen it to `0x1FFF`.
  - Check how the page decodes the mask (`custs`): 13 vs 14 months.
- **ref_mkt / mk:**
  - `prows` keep 'sep'/'oct' pairs. For Nov this becomes Oct (now final) plus Nov.
  - `ref_mkt` reads a fixed Sep pull (`1791784745621`). For Nov it needs a final **October** per-customer pull as the "previous month".
- **ref_prod:** `mi`/`si` month indexes, `DAYS` start date, and `cdOct`. Product daily `days` and per-customer `pc_day` history:
  - move the October chunks into `state/pc_day_hist.json`;
  - set `pc_month.json["2026-10"]` to a final full-October pcM pull.
- **vipm cut, pcD and bonus start:** move `cut` to 2026-11-01 only after the October rows are final in the state files.
- **Display text:** "Oct 26 partial month" labels are generated from the data; check the header after building.

Validate everything in 3.4 before publishing.

---

## 6. Scheduled daily refresh from another conversation or laptop

The current schedule (09:00 MYT daily, incl. weekends) is bound to the **original conversation and laptop-ih2a3dmt**. If you move to another laptop, first **turn off the old scheduled task** in the original conversation, so two runs don't both push. Then create a new scheduled task in the new, linked conversation with this prompt:

> Daily 9am refresh of B2C Marketing & OP (every day incl. weekends). Follow the runbook in project doc claude/b2c-dashboard-refresh-runbook.md (also RUNBOOK.md on branch `pipeline` of datamkt88/bi_dashboard). Set up the session (section 2). Run queries for today. Build a new rNN with newrun.py and run.sh. Check every validation line in 3.4. Then:
> 1. send the user the HTML file;
> 2. push index.html to main;
> 3. republish the artifact https://claude.ai/artifact/U2tWfjN39JkawcfuKumBDq;
> 4. push the pipeline state back (3.6).
>
> If it is the first run of a new month, stop after the pulls and ask the user (section 5). If Power BI is unreachable or a check fails, publish nothing and send the user a short note saying what is needed.

---

## 7. Known facts and caveats

- **Retention Performance** is still on its 5 Oct snapshot. It is not part of the daily refresh.
- **Marketing pages** map site from the affiliate master list. The other pages use the customer's SiteName.
- **NG** (daily net GGR) = G1 − BO − RB − PRO − ADJ, where G1 = −WinLostAmount.
- **drows** uses a registration cutoff of `RegTime_utc8 >= 2025-01-01`. It was verified against the original report.
- Two monthly redepositor segment rows are missing, so Sep redepositors show 11,171 vs 11,179. Known and accepted.
- **GitHub Pages** on a private repo needs a paid plan. Until then, view the dashboard via the downloaded file or the artifact link.
- **Reproducibility check:** this pack was smoke-tested by rebuilding the 27 Oct 12:16 dashboard from the 09:14 one. Every data block came out identical (only the tag order inside the VIP block differed; `run.sh` now sets `PYTHONHASHSEED=0`).
