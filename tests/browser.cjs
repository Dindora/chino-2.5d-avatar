const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:8765';
async function send(command) {
  const response = await fetch(base + '/api/command', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(command)
  });
  assert.equal(response.status, 200);
}
function tone() {
  const rate = 16000, count = rate * 2, wav = Buffer.alloc(44 + count * 2);
  wav.write('RIFF'); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(rate, 24); wav.writeUInt32LE(rate * 2, 28); wav.writeUInt16LE(2, 32);
  wav.writeUInt16LE(16, 34); wav.write('data', 36); wav.writeUInt32LE(count * 2, 40);
  for (let i = 0; i < count; i++) wav.writeInt16LE(Math.round(10000 * Math.sin(2 * Math.PI * 440 * i / rate)), 44 + i * 2);
  return 'data:audio/wav;base64,' + wav.toString('base64');
}
(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.BROWSER_CHANNEL ? {channel: process.env.BROWSER_CHANNEL} : {})});
  try {
    const page = await browser.newPage();
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/?robot=1');
    await page.waitForFunction(() => window.ChinoAvatar && document.querySelector('#drop').classList.contains('hidden'));
    await page.evaluate(() => {
      window.mouthValues = [];
      const original = ChinoAvatar.mouth;
      ChinoAvatar.mouth = value => { mouthValues.push(value); original.call(ChinoAvatar, value); };
    });
    await page.click('#robotAudio');
    await send({type:'expression',name:'surprise'});
    await page.waitForFunction(() => document.querySelector('[data-preset="surprise"]').classList.contains('active'));
    await send({type:'params',values:{angleX:5}});
    await page.waitForFunction(() => document.querySelector('#pAngleX').value === '1');
    await send({type:'say',text:'你好，智乃',audio:tone()});
    await page.waitForFunction(() => document.querySelector('#robotSubtitle').textContent === '你好，智乃');
    await page.waitForFunction(() => mouthValues.some(v => v > .1));
    await page.waitForFunction(() => mouthValues.length > 10 && mouthValues.at(-1) === 0);
    await send({type:'say',text:'打断测试',audio:tone()});
    await page.waitForFunction(() => document.querySelector('#robotSubtitle').textContent === '打断测试' && mouthValues.at(-1) > .1);
    await send({type:'stop'});
    await page.waitForFunction(() => document.querySelector('#robotSubtitle').textContent === '' && mouthValues.at(-1) === 0);
    await send({type:'say',text:'<img src=x onerror=alert(1)>'});
    await page.waitForFunction(() => document.querySelector('#robotSubtitle').textContent.includes('<img'));
    assert.equal(await page.locator('#robotSubtitle img').count(), 0);
    assert.deepEqual(errors, []);
    const offline = await browser.newPage();
    await offline.goto(require('node:url').pathToFileURL(require('node:path').resolve('index.html')).href);
    await offline.waitForFunction(() => document.querySelector('#drop').classList.contains('hidden'));
    assert.equal(await offline.locator('#robotAudio').count(), 0);
    console.log('PASS: model loading, expression, clamping, subtitles, audio-driven mouth, natural end, interruption, text escaping, offline mode');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
