import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {writeFile} from 'node:fs/promises';
import path from 'node:path';
const root=process.argv[2];
const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?
  {executablePath:process.env.CHROME_PATH}:{})});
try{
  const page=await browser.newPage({viewport:{width:1500,height:920},deviceScaleFactor:1});
  const reports=[];
  for(const name of ['folha-anatomica','folha-movimento']){
    await page.goto(pathToFileURL(path.join(root,name+'.html')).href);
    await page.waitForFunction(()=>!!window.ensaioRig);
    await page.addScriptTag({path:fileURLToPath(new URL('./auditoria_anatomica.js',import.meta.url))});
    reports.push(await page.evaluate(()=>window.AuditoriaAnatomica.avaliar(window.ensaioRig,document)));
    if(name==='folha-movimento'){
      const poses=await page.evaluate(()=>window.ensaioRig.sequences);
      await writeFile(path.join(root,'poses-ensaio.json'),JSON.stringify({fps:30,unidade:'cabeças',poses})+'\n');
    }
    if(name==='folha-anatomica'&&process.argv.includes('--testar')){
      await page.addScriptTag({path:fileURLToPath(new URL('./testar_mutacoes_anatomicas.js',import.meta.url))});
      const results=await page.evaluate(()=>window.testarMutacoesAnatomicas());
      await writeFile(path.join(root,'mutacoes-anatomicas.json'),JSON.stringify(results,null,2)+'\n');
    }
    await page.locator('main').screenshot({path:path.join(root,name+'.png')});
  }
  const [anatomy,motion]=reports;
  const measurements={...motion,checks:{...anatomy.checks,...motion.checks},
    issues:[...anatomy.issues.filter(issue=>issue.ensaio==='folha anatômica'),...motion.issues]};
  await writeFile(path.join(root,'medicoes.json'),JSON.stringify(measurements,null,2)+'\n');
}finally{
  await browser.close();
}
