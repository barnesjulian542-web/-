const { chromium } = require('C:/Users/jo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true,args:['--no-proxy-server']});
  try {
  const page = await browser.newPage({viewport:{width:1440,height:1050},deviceScaleFactor:1});
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  const response = await page.goto('http://127.0.0.1:8504', {waitUntil:'domcontentloaded'});
  await page.getByRole('heading', {name:'售前需求核验', exact:true}).waitFor({timeout:30000});
  if (!await page.getByRole('button', {name:/开始核验/}).isVisible()) await page.getByText('新建客户核验',{exact:true}).click();
  await page.waitForFunction(()=>{const button=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('开始核验'));if(!button)return false;const r=button.getBoundingClientRect();return button.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))},{},{timeout:15000});
  await page.screenshot({path:'F:/project/qiye/runtime/home.png', fullPage:true});
  await page.getByRole('button', {name:/开始核验/}).click({position:{x:15,y:20}});
  await page.getByText('核验结果', {exact:true}).waitFor({timeout:30000});
  await page.getByRole('button',{name:/导出核验草稿/}).waitFor({timeout:30000});
  const creation=page.locator('[data-testid="stExpander"]').filter({has:page.getByText('新建客户核验',{exact:true})});
  if(await creation.locator('details').getAttribute('open')!==null) await page.getByText('新建客户核验',{exact:true}).click();
  await page.locator('[data-testid="stMain"]').evaluate(el=>el.scrollTop=0);
  await page.screenshot({path:'F:/project/qiye/runtime/workbench.png', fullPage:true});
  await page.getByText('查看依据',{exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:'F:/project/qiye/runtime/evidence.png',fullPage:true});
  const mobile=await browser.newPage({viewport:{width:390,height:844}});
  await mobile.goto('http://127.0.0.1:8504',{waitUntil:'domcontentloaded'});
  await mobile.getByRole('button',{name:/导出核验草稿/}).waitFor({timeout:30000});
  await mobile.screenshot({path:'F:/project/qiye/runtime/mobile.png',fullPage:true});
  const health=await page.request.get('http://127.0.0.1:8504/_stcore/health');
  fs.writeFileSync('F:/project/qiye/runtime/browser_check.json', JSON.stringify({url:page.url(),status:response.status(),health_status:health.status(),health_body:await health.text(),page_errors:errors,checked:['initial_form','preset_submit','results_render','mobile_width'],human_approval_submitted:false},null,2));
  console.log(JSON.stringify({status:response.status(),page_errors:errors,screenshots:['runtime/home.png','runtime/workbench.png']}));
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
