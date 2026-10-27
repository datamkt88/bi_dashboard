"""Copy dax_query results saved by this session into raw/<id>.txt.
python3 grab.py /root/.claude/projects/<proj>/<session>/tool-results     (path is printed in each 'Output has been saved to ...' message)
Prints id, header and row count of every new file so you can fill ids_rNN.json."""
import sys, glob, shutil, os, json
src=sys.argv[1]
for f in sorted(glob.glob(os.path.join(src,'*dax_query_operations-*.txt'))):
    i=f.rsplit('-',1)[1][:-4]; dst=f'raw/{i}.txt'
    if os.path.exists(dst): continue
    shutil.copy(f,dst)
    t=''.join(x.get('text','') for x in json.load(open(f))); body=t[t.find('] ')+2:].split('\n')
    print(i, len([l for l in body[1:] if l]), 'rows |', body[0][:150])
