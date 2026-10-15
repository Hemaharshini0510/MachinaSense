const fs=require('fs');
const file=process.argv[2]||require('path').join(__dirname,'..','index.html');
const html=fs.readFileSync(file,'utf8');
const script=html.split('<script>')[1].split('</script>')[0];
// syntax check of full script
new Function(script);
const eng=script.split('// ==ENGINE START==')[1].split('// ==ENGINE END==')[0];
const api=new Function(eng+'; return {trainAll,makeTest,buildView,aggregate,PRESETS,FAULTS,simulate,fit,score,extract,SENSORS};')();
const t0=Date.now();
const T=api.trainAll();
console.log('train ms',Date.now()-t0,'theta',T.P.theta,'baseline c',T.bc);
console.log('templates',Object.fromEntries(Object.entries(T.templates).map(([k,v])=>[k,v.map(x=>x.toFixed(2)).join(',')])));
for(const key of ['clean','hidden','harsh']){
  const set=api.makeTest(api.PRESETS[key]); const tm={ms:0,n:0};
  const views=set.map(ds=>api.buildView(ds,T,tm)); const A=api.aggregate(views);
  const med=a=>{if(!a.length)return NaN;const t=[...a].sort((x,y)=>x-y);return t[t.length>>1];};
  console.log(`\n[${key}] faults ${A.faults} | ours TP ${A.d.tp} FP ${A.d.fp} medDelay ${med(A.d.delays).toFixed(1)}h | base TP ${A.b.tp} FP ${A.b.fp} medDelay ${med(A.b.delays).toFixed(1)}h | diag ${A.diagOk}/${A.diagN} | days ${A.days.toFixed(0)} | ${(tm.ms*1000/tm.n).toFixed(2)} us/sample`);
  console.log(' conf',JSON.stringify(A.conf));
  if(key==='hidden'){ views.forEach(v=>{const t=v.ds.truth; console.log(' ',v.ds.id,(t.fault||'healthy').padEnd(9),'shift',t.shiftAt!=null?'Y':'-','noise',t.noise.toFixed(1),'miss',(t.miss*100).toFixed(0)+'%','mag',t.mag.toFixed(2),'| ours',v.jd.hit?('hit '+((v.jd.hit.raiseIdx-t.onset)/6).toFixed(0)+'h '+(v.jd.hit.diag.key||'none')):'-', 'fp',v.jd.fp,'| base',v.jb.hit?'hit':'-','fp',v.jb.fp);}); }
}
