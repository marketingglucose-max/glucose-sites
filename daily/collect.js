// Вставить в javascript_tool на странице https://www.instagram.com/<аккаунт>/ (браузер приложения Claude).
// Перед запуском заменить DAY на дату дня анализа, например '2026-11-10' (сутки по Алматы, UTC+5).
// Сохраняет результат в localStorage.dly и возвращает короткую строку.
const DAY='2026-11-10';
const [y,m,d]=DAY.split('-').map(Number);const S=Date.UTC(y,m-1,d)-5*3600e3,E=S+864e5;
const dec=c=>{const A='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';let n=0n;for(const ch of c.slice(0,11))n=n*64n+BigInt(A.indexOf(ch));return Number((n>>23n)+1314220021721n)};
for(let i=0;i<8&&!document.querySelector('main a[href*="/p/"],main a[href*="/reel/"]');i++){window.scrollBy(0,300);await new Promise(r=>setTimeout(r,1500))}
const o=[];for(let i=0;i<8;i++){document.querySelectorAll('main a[href*="/p/"],main a[href*="/reel/"]').forEach(a=>{const mm=a.getAttribute('href').match(/\/(?:p|reel)\/([^/]+)/);if(mm&&!o.includes(mm[1]))o.push(mm[1])});const r=o.slice(3).map(dec);if(r.length&&Math.min(...r)<S)break;window.scrollBy(0,2000);await new Promise(r=>setTimeout(r,1500))}
const L=o.filter(c=>{const t=dec(c);return t>=S&&t<E});const out=[];
for(const c of L){const t=await (await fetch('/p/'+c+'/')).text();const og=(t.match(/og:url" content="([^"]*)"/)||[])[1]||'';const ds=(t.match(/<meta (?:name|property)="(?:og:)?description" content="([^"]*)"/)||[])[1]||'';const lm=ds.match(/^([\d,.]+K?)\s*likes/);const ta=document.createElement('textarea');ta.innerHTML=(t.match(/og:title" content="([^"]*)"/)||[])[1]||'';let lk=lm?lm[1]:null;if(lk){lk=lk.endsWith('K')?Math.round(parseFloat(lk)*1000):parseInt(lk.replace(/,/g,''))}out.push({c,t:/\/reel\//.test(og)?'reel':'p',likes:lk,cap:ta.value.replace(/^.*?Instagram\s*:\s*"/,'').replace(/"\s*$/,'').replace(/\s+/g,' ').slice(0,90)})}
const rec={a:location.pathname.split('/')[1],posts:out};let all={};try{all=JSON.parse(localStorage.dly||'{}')}catch(e){};if(all.__day!==DAY)all={__day:DAY};all[rec.a]=rec;localStorage.dly=JSON.stringify(all);rec.a+': '+out.map(p=>p.t+' '+p.likes).join(', ')
