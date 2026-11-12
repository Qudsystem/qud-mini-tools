#!/usr/bin/env node
// read-events.js — طباعة الأحداث الجديدة فقط منذ آخر قراءة
const fs = require('fs');
const path = require('path');

const file = process.argv[2] || 'events.jsonl';
const stateFile = file + '.offset';

let offset = 0;
try { offset = parseInt(fs.readFileSync(stateFile, 'utf8')) || 0; } catch(e) {}

let data;
try { data = fs.readFileSync(file); }
catch(e) { console.error('cannot read:', file); process.exit(1); }

const slice = data.slice(offset);
const text = slice.toString('utf8');
const lines = text.split(/\r?\n/);
const events = [];

for (const line of lines) {
  if (!line.trim()) continue;
  try {
    const o = JSON.parse(line);
    if (o.meta === 'start') { console.log('[START] fps='+o.fps+' scale='+o.scale+' screen='+o.screenW+'x'+o.screenH); continue; }
    if (o.meta === 'end') { console.log('[END] frames='+o.frames+' totalEvents='+o.events); continue; }
    events.push(o);
  } catch(e) {}
}

if (process.argv.includes('--quiet')) {
  console.log(JSON.stringify({ newEvents: events.length, lastOffset: data.length }));
} else {
  console.log('New events since offset ' + offset + ': ' + events.length);
  for (const o of events.slice(-30)) {
    console.log('  frame='+o.frame+' pct='+o.pct+'% ('+o.x+','+o.y+') '+o.w+'x'+o.h);
  }
}

fs.writeFileSync(stateFile, String(data.length));
