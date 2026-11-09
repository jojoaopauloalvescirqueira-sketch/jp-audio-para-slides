import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {writeFile} from 'node:fs/promises';

const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE);
const [html,png,json]=process.argv.slice(2);
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try{
  const page=await browser.newPage({viewport:{width:1470,height:810},deviceScaleFactor:1});
  page.on('pageerror',error=>console.error(error));
  await page.goto(pathToFileURL(html).href);
  await page.waitForFunction(()=>window.medidasModelo?.length===12);
  await page.locator('main').screenshot({path:png});
  await page.addScriptTag({path:fileURLToPath(new URL('./auditoria_proporcoes.js',import.meta.url))});
  const data=await page.evaluate(async()=>{
    const {bible}=JSON.parse(document.querySelector('#modelo').textContent);
    const issues=[];
    for(const card of document.querySelectorAll('svg[data-pose-modelo]')){
      const {inspect}=window.auditarProporcoes(bible,(codigo,quadro,id,correcao)=>
        issues.push({codigo,quadro,id,correcao,cena:card.dataset.poseModelo}));
      await inspect(card,0,card.dataset.poseModelo);
    }
    return {poses:window.medidasModelo,issues};
  });
  if(data?.poses?.length!==12)throw Error('Folha sem as doze poses.');
  await writeFile(json,JSON.stringify(data,null,2)+'\n');
}finally{await browser.close();}
