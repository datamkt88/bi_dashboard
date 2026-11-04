#!/bin/bash
# Re-pull and rebuild LAST month, then roll over and build the current month on top (RUNBOOK section 3.8).
# Used on days 1..15 of a month (state/prev_snapshot.json 'until'), after the normal current-month pull.
#
#   bash prevmonth.sh rNN          (ids_rNN.json = this run's current-month pull, already done)
#
# 1. restore the page + state as they were right after last month's final build (before rollover.py)
# 2. pull last month again (D = its last day) into folder <final>_<rNN>, e.g. r31_r05a, and rebuild it
# 3. rollover.py, mkmonth.py <final>_<rNN> rNN, bash run.sh rNN
# Stops at the first error. Segment-map misses: the build stops with exit 2 in folder <final>_<rNN> or rNN;
# top it up (RUNBOOK 3.3, ids from that folder's miss.txt), then rerun: plain (redoes last month, reusing its
# pull) if it stopped in <final>_<rNN>, or STEP=cur (current month only) if it stopped in rNN.
set -e
R=$1; [ -f "ids_$R.json" ] || { echo "no ids_$R.json"; exit 1; }
export PYTHONPATH=. PYTHONHASHSEED=0
S=$(python3 -c "import json;s=json.load(open('state/prev_snapshot.json'));print(s['folder'],s['pipeline'],s['main'],s['month'],s['until'])")
read F PC MC OLD UNTIL <<< "$S"
P=${F}_$R
NEW=$(python3 -c "import json;print(json.load(open('ids_$R.json'))['date'][:7])")
LAST=$(python3 -c "import datetime as d;y,m=map(int,'$NEW'.split('-'));print(d.date(y,m,1)-d.timedelta(1))")
[ "${LAST:0:7}" = "$OLD" ] || { echo "snapshot month $OLD is not the month before $NEW"; exit 1; }
DATA="build_top.py custs_new.json exec_ref.json pc_day.json pc_month.json pc_new.json pmseg.json pmtop.b64 vipm_fd.json vipm_nr.json state/config.json state/custs_base.json state/mg_prev.json state/pc_day_hist.json"
if [ "$STEP" != cur ]; then
  echo "## A snapshot $OLD (pipeline $PC, main $MC)"
  git fetch -q origin main pipeline
  git checkout $PC -- $DATA
  rm -f state/pc_new_fixed.json "state/rollover_$NEW.json"
  if git ls-tree --name-only $PC state/ | grep -q pc_new_fixed; then git checkout $PC -- state/pc_new_fixed.json; fi
  git show origin/main:index.html | python3 -c "import sys,re,json;D=json.loads(re.search(r'<script id=\"data\" type=\"application/json\">(.*?)</script>',sys.stdin.read(),re.S).group(1));json.dump({k:v for k,v in D['fx'].items() if k.startswith('$NEW|')},open('_fx_keep.json','w'))"
  git show $MC:index.html > B2C-Marketing.html
  if [ ! -f "ids_$P.json" ]; then
    echo "## B pull $OLD again (D=$LAST) -> $P"
    python3 cloud/cloudpull.py "$PWD" $LAST $P 23:59 23:59
  else echo "## B ids_$P.json exists: reusing that pull"; fi
  python3 newrun.py $F $P ids_$P.json
  echo "## C build $P"
  bash run.sh $P || { rc=$?; echo "!! last-month build $P stopped (exit $rc)"; exit $rc; }
  echo "## D rollover $OLD -> $NEW"
  FX_KEEP=_fx_keep.json python3 rollover.py $P $NEW
  rm -rf _roll; cp B2C-Marketing.html "prev_rolled_$P.html"
  for f in $DATA state/pc_new_fixed.json state/rollover_$NEW.json; do mkdir -p "_roll/$(dirname $f)"; cp "$f" "_roll/$f"; done
else
  echo "## A-D skipped (STEP=cur): restoring the rolled-over page and state of $P"
  cp "prev_rolled_$P.html" B2C-Marketing.html; cp -r _roll/. .
fi
echo "## E current month $R on top of $P"
python3 mkmonth.py $P $R ids_$R.json
python3 queries.py $(python3 -c "import json;print(json.load(open('ids_$R.json'))['date'])") > /dev/null   # queries/ back to the current month
bash run.sh $R
echo PREVMONTH DONE $P $R
