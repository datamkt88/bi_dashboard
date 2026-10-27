const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});const p=await b.newPage({viewport:{width:1500,height:950}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.route(/chart\.umd/,r=>r.fulfill({path:__dirname+'/node_modules/chart.js/dist/chart.umd.js',contentType:'text/javascript'}));
await p.goto('http://localhost:8765/index.html');await p.waitForTimeout(3000);
const tabs=await p.$$eval('nav button[data-tab]',bs=>bs.map(b=>[b.dataset.tab,b.dataset.sub||'',b.innerText.replace(/\s+/g,' ').trim()]));
for(const [t,s,n] of tabs){
 const sel=`nav button[data-tab="${t}"]`+(s?`[data-sub="${s}"]`:'');
 await p.$eval(sel,b=>b.click());await p.waitForTimeout(2500);
 const txt=await p.evaluate(()=>document.body.innerText);
 console.log(n.slice(0,40),'| len',txt.length,'NaN/undef',(txt.match(/NaN|undefined/g)||[]).length);}
console.log('errors',errs);await b.close();})();
