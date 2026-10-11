const { chromium } = require('C:/Users/jo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{
  const browser=await chromium.launch({channel:'msedge',headless:true,args:['--no-proxy-server']});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1050}});
    const errors=[];
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
    page.on('pageerror',e=>errors.push(String(e)));
    page.on('requestfailed',r=>errors.push(r.url()+' '+r.failure().errorText));
    const response=await page.goto('http://127.0.0.1:8504',{waitUntil:'domcontentloaded'});
    await page.waitForTimeout(5000);
    const body=await page.locator('body').innerText();
    const buttons=await page.getByRole('button').allTextContents();
    const button=page.getByRole('button',{name:/开始核验/});
    const hit=await button.evaluate(el=>{const r=el.getBoundingClientRect(); const target=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {rect:r.toJSON(),pointer:getComputedStyle(el).pointerEvents,hit:target?.outerHTML.slice(0,600)}});
    await page.screenshot({path:'F:/project/qiye/runtime/browser_debug.png',fullPage:true});
    const result={status:response.status(),errors,buttons,hit,body:body.slice(0,5000)};
    fs.writeFileSync('F:/project/qiye/runtime/browser_debug.json',JSON.stringify(result,null,2));
    console.log(JSON.stringify(result));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
