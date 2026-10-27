const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch(process.env.CHROMIUM?{executablePath:process.env.CHROMIUM}:{});const p=await b.newPage({viewport:{width:1500,height:950}});
const errs=[];p.on('pageerror',e=>errs.push(e.message.slice(0,200)));
await p.route(/chart\.umd/,r=>r.fulfill({path:__dirname+'/node_modules/chart.js/dist/chart.umd.js',contentType:'text/javascript'}));
await p.goto('file://'+__dirname+'/B2C-Marketing.html');await p.waitForTimeout(2500);
await p.$eval('nav button[data-tab="t2"][data-sub="s1"]',b=>b.click());await p.waitForTimeout(1200);
console.log('monthly',await p.$$eval('#brandCards h4',x=>x.map(e=>e.innerText.replace(/\s+/g,' '))));
const dl=await p.$$('#s1 button'); for(const b of dl){ if((await b.innerText()).trim()==='Daily'){await b.click();break;} }
await p.waitForTimeout(1000);
console.log('daily',await p.$$eval('#brandCards h4',x=>x.map(e=>e.innerText.replace(/\s+/g,' '))));
console.log('errors',errs);await b.close();})();
