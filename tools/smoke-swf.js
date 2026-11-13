const {chromium}=require('playwright');const http=require('http');const fs=require('fs');const path=require('path');
const root=process.argv[2];const urls=JSON.parse(process.argv[3]);const out=process.argv[4];const wait=+process.argv[5]||6000;
const types={'.html':'text/html','.js':'text/javascript','.wasm':'application/wasm','.swf':'application/x-shockwave-flash','.xml':'text/xml'};
const log=[];
const srv=http.createServer((req,res)=>{let u=decodeURIComponent(req.url.split('?')[0]);let f=path.join(root,u);
 fs.readFile(f,(e,d)=>{if(e){log.push('404 '+u);res.writeHead(404);res.end();return}res.writeHead(200,{'content-type':types[path.extname(f)]||'application/octet-stream'});res.end(d)})}).listen(8765,async()=>{
 const b=await chromium.launch();const pg=await b.newPage({viewport:{width:820,height:620}});
 pg.on('console',m=>log.push('console '+m.type()+': '+m.text().slice(0,300)));
 for(const [i,u] of urls.entries()){log.push('== '+u);await pg.goto('http://localhost:8765'+u);await pg.waitForTimeout(wait);
  // click to start
  await pg.mouse.click(200,200);await pg.waitForTimeout(1500);
  await pg.screenshot({path:out+'_'+i+'.png'});}
 await b.close();srv.close();console.log(log.filter(l=>!/WebGL|GPU/.test(l)).join('\n'));});
