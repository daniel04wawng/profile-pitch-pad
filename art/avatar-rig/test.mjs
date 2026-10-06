import assert from 'node:assert/strict';
import fs from 'node:fs';
import { CafeAvatar, loadCafeAvatar } from './src/cafe-avatar.mjs';
const manifest=JSON.parse(fs.readFileSync(new URL('./assets/green/manifest.json',import.meta.url)));
const sheets=Object.fromEntries(Object.keys(manifest.animations).map(n=>[n,{}]));
const avatar=new CafeAvatar(manifest,sheets);
assert.equal(avatar.frameIndex,0);avatar.update(1500);assert.equal(avatar.frameIndex,1);
avatar.setAction('sit-down');const first=avatar.update(1000);assert.equal(first.justCompleted,true);assert.equal(avatar.frameIndex,7);assert.equal(avatar.update(50).justCompleted,false);
avatar.setAction('seated-idle');assert.equal(avatar.frameIndex,0);
avatar.setAction('walk-front');const travel=avatar.update(1000);assert.equal(avatar.frameIndex,0);const end=manifest.animations['walk-front'].rootMotion.at(-1);assert.ok(Math.abs(travel.dx-end[0])<1e-8);assert.ok(Math.abs(travel.dy-end[1])<1e-8);
const parts=new CafeAvatar(manifest,sheets);parts.setAction('walk-front');let sum=0;for(let i=0;i<20;i++)sum+=parts.update(50).dx;assert.ok(Math.abs(sum-travel.dx)<1e-8);
assert.throws(()=>avatar.update(-1));assert.throws(()=>avatar.update(NaN));assert.throws(()=>avatar.setAction('missing'));
const calls=[];const ctx={globalAlpha:1,save(){},restore(){},translate(...v){calls.push(['translate',...v])},scale(){},drawImage(...v){calls.push(v)}};avatar.draw(ctx,{x:80,y:90});assert.deepEqual(calls[0],['translate',80,90]);assert.deepEqual(calls[1].slice(5),[-32,-64.5,64,70]);
const fetched=[];const loaded=await loadCafeAvatar('http://example.test/assets/green/manifest.json',{fetchImpl:async url=>({ok:true,json:async()=>manifest}),imageFactory:()=>({naturalWidth:512,naturalHeight:70,set src(url){fetched.push(url);queueMicrotask(()=>this.onload())}})});assert.equal(fetched.length,12);assert.ok(fetched.every(x=>x.startsWith('http://example.test/assets/green/')));assert.equal(loaded.action,'idle-front');
await assert.rejects(loadCafeAvatar('http://example.test/assets/green/manifest.json',{fetchImpl:async()=>({ok:false,status:404})}),/404/);
console.log('PASS: variable timing, one-shot completion, loops, root motion, import paths, draw anchor, input validation and loader errors.');

for(const [direction,signX,signY] of [['SE',1,1],['SW',-1,1],['NE',1,-1],['NW',-1,-1]]) {
 const unit=new CafeAvatar(manifest,sheets);unit.setDirection(direction);unit.play('walk');const delta=unit.update(1000);
 assert.equal(Math.sign(delta.dx),signX);assert.equal(Math.sign(delta.dy),signY);
 unit.update(375);const index=unit.frameIndex,time=unit.elapsedMs;unit.setDirection(direction==='NE'?'SE':'NE');assert.equal(unit.frameIndex,index);assert.equal(unit.elapsedMs,time);
 for(const motion of ['idle','sit-down','stand-up','coffee-sip','seated-idle']){unit.setDirection(direction);unit.play(motion);assert.equal(unit.action,manifest.directions[direction].actions[motion]);}
}
const mirrored=new CafeAvatar(manifest,sheets);mirrored.setDirection('SW');mirrored.play('sit-down');assert.deepEqual(mirrored.attachmentPoints.chairSeat,[64-manifest.attachments['sit-down'].chairSeat[0],manifest.attachments['sit-down'].chairSeat[1]]);
assert.throws(()=>mirrored.setDirection('north'));assert.throws(()=>mirrored.play('missing'));
mirrored.setAction('walk-back');assert.equal(mirrored.direction,'NW');
console.log('PASS: four facing directions, motion signs, phase preservation, directional actions, mirrored attachments and legacy clip selection.');
