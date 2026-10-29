#!/bin/bash
# Full build for one run folder. Usage: bash run.sh r28      (run from the package root)
# Stops at the first error. Read the printed validation lines - see RUNBOOK 'What good output looks like'.
set -e
R=$1; [ -d "$R" ] || { echo "no $R"; exit 1; }
export PYTHONPATH=. PYTHONHASHSEED=0
# use the preinstalled Chromium if the local playwright wants a browser that is not installed
[ -z "$CHROMIUM" ] && C=$(ls /opt/pw-browsers/chromium-*/chrome-linux*/chrome 2>/dev/null | head -1) && [ -n "$C" ] && export CHROMIUM=$C
if [ "$FROM" != seg ]; then
cp B2C-Marketing.html "bak_before_$R.html"
echo "## 1 prep";      python3 prep.py csvs $R; python3 prep.py custs $R; python3 prep.py drows $R
echo "## 2 exec";      python3 $R/ref_exec.py
echo "## 3 mkt";       python3 $R/ref_mkt.py
echo "## 4 custs";     python3 $R/build_custs.py
echo "## 5 mk";        python3 $R/mk.py
echo "## 6 prod";      python3 $R/ref_prod.py; python3 prep.py pminsert $R
fi
echo "## 7 seg";       python3 prep.py pcjson $R; python3 prep.py miss $R
if [ -s $R/miss.txt ] && [ -z "$SKIP_MISS" ]; then echo "!! $(wc -l < $R/miss.txt | tr -d ' ')+ customers missing from the segment map: run queries/_missmap_TEMPLATE.dax with ids from $R/miss.txt, save raw/<id>.txt, python3 prep.py mapadd <id>, then rerun with: FROM=seg bash run.sh $R  (or SKIP_MISS=1 to accept '(Unknown)')"; exit 2; fi
python3 build_seg.py; python3 build_top2.py
echo "## 8 vip";       python3 prep.py vipm $R; python3 $R/build_vip2s.py; python3 $R/build_vip3s.py
echo "## 9 mg";        python3 $R/build_mg.py; python3 $R/mg_rd.py
echo "## 10 final";    python3 $R/final.py
echo "## 11 check";    node t60.js
echo DONE
