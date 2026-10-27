import re,json,os,sys
src=sys.argv[1] if len(sys.argv)>1 else '/mnt/user-data/outputs/B2C Marketing & OP.html'
out='art'; os.makedirs(out,exist_ok=True)
s=open(src,encoding='utf-8').read()
loads=[]
def rep(m):
    attrs,body=m.group(1),m.group(2)
    im=re.search(r'id="([a-z]+)"',attrs)
    if not im or len(body)<200000 or 'src=' in attrs: return m.group(0)
    i=im.group(1); fn=f'd_{i}.js'
    open(f'{out}/{fn}','w',encoding='utf-8').write(
        'document.getElementById(%s).textContent=%s;\n'%(json.dumps(i),json.dumps(body,ensure_ascii=True).replace('</','<\\/')))
    loads.append(fn)
    return f'<script{attrs}></script>'
s=re.sub(r'<script([^>]*)>(.*?)</script>',rep,s,flags=re.S)
# insert loaders right before the main inline script (first script that reads data)
k=s.index("JSON.parse(document.getElementById('data').textContent)")
k=s.rindex('<script',0,k)
s=s[:k]+''.join(f'<script src="{f}"></script>\n' for f in loads)+s[k:]
open(f'{out}/index.html','w',encoding='utf-8').write(s)
for f in ['index.html']+loads: print(f,os.path.getsize(f'{out}/{f}'))
