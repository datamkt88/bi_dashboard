const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});const p=await b.newPage({viewport:{width:1500,height:950}});
const errs=[];p.on('pageerror',e=>errs.push(e.stack.slice(0,300)));
await p.route(/chart\.umd/,r=>r.fulfill({path:__dirname+'/node_modules/chart.js/dist/chart.umd.js',contentType:'text/javascript'}));
await p.goto('file://'+__dirname+'/B2C-Marketing.html');await p.waitForTimeout(2500);
await p.screenshot({path:'t60a.png'});
const tabs=await p.$$eval('nav button[data-tab]',x=>x.map(e=>[e.dataset.tab,e.dataset.sub||'',e.innerText.trim()]));
for(const [t,s,n] of tabs){ const sel=s?`nav button[data-tab="${t}"][data-sub="${s}"]`:`nav button[data-tab="${t}"]`; try{await p.click(sel,{timeout:3000});await p.waitForTimeout(900);}catch(e){} }
await p.click('nav button[data-tab="t2"]');await p.waitForTimeout(1200);
console.log('K2', await p.$$eval('#mgK2 .kpi',x=>x.map(e=>e.innerText.replace(/\s+/g,' ')).join(' | ')));
await p.screenshot({path:'t60b.png'});
console.log('errors',errs);await b.close();})();
