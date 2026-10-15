/* Local HTTP bridge; loaded only when explicitly enabled with ?robot=1. */
(() => {
  if (location.protocol === 'file:' || new URLSearchParams(location.search).get('robot') !== '1') return;
  const box = document.createElement('div');
  box.style.cssText = 'position:absolute;bottom:16px;left:16px;right:16px;z-index:6;text-align:center;white-space:pre-wrap;pointer-events:none';
  box.id = 'robotSubtitle';
  document.getElementById('stage').appendChild(box);
  const button = document.createElement('button');
  button.className = 'btn'; button.textContent = '启用机器人语音';
  button.id = 'robotAudio';
  document.querySelector('header').appendChild(button);
  let context, source, analyser, samples, audio, frame, cursor = 0, generation = 0;
  let enabled = false;
  const api = window.ChinoAvatar;
  api.robotMode();
  button.onclick = async () => {
    try {
      context ||= new AudioContext();
      await context.resume(); enabled = true;
      button.textContent = '机器人语音已启用';
    } catch (e) { button.textContent = '语音启用失败，请重试'; }
  };
  function stop() {
    generation++;
    cancelAnimationFrame(frame);
    if (audio) { audio.pause(); audio.removeAttribute('src'); audio.load(); audio = null; }
    if (source) { source.disconnect(); source = null; }
    if (analyser) { analyser.disconnect(); analyser = null; }
    api.mouth(0);
  }
  async function apply(command) {
    if (command.type === 'stop') { stop(); box.textContent = ''; }
    if (command.type === 'expression') api.expression(command.name);
    if (command.type === 'params') api.params(command.values);
    if (command.type !== 'say') return;
    stop(); box.textContent = command.text || '';
    if (!command.audio) return;
    if (!enabled) { button.textContent = '请先启用语音，再重新发送'; return; }
    const url = new URL(command.audio, location.href);
    if (!(command.audio.startsWith('data:audio/') || url.origin === location.origin)) return;
    const token = generation;
    audio = new Audio(command.audio);
    source = context.createMediaElementSource(audio);
    analyser = context.createAnalyser(); analyser.fftSize = 256;
    samples = new Uint8Array(analyser.fftSize);
    source.connect(analyser); analyser.connect(context.destination);
    audio.onended = () => { if (token === generation) stop(); };
    audio.onerror = () => { if (token === generation) { stop(); button.textContent = '音频加载失败，请检查文件'; } };
    try {
      await audio.play();
      if (token !== generation) return;
      const update = () => {
        analyser.getByteTimeDomainData(samples);
        const rms = Math.sqrt(samples.reduce((sum, x) => sum + ((x - 128) / 128) ** 2, 0) / samples.length);
        api.mouth(Math.min(1, rms * 5));
        frame = requestAnimationFrame(update);
      };
      update();
    } catch (e) {
      if (token === generation) { stop(); button.textContent = '播放失败，请启用语音后重发'; }
    }
  }
  async function poll() {
    try {
      const response = await fetch('/api/commands?after=' + cursor, {cache: 'no-store'});
      if (!response.ok) throw new Error('Bridge unavailable');
      const data = await response.json();
      for (const command of data.commands) {
        try { await apply(command); } catch (e) { console.error('Robot command failed', e); }
      }
      cursor = data.cursor;
    } catch (e) { /* A stopped server can reconnect on the next poll. */ }
    setTimeout(poll, 100);
  }
  poll();
})();
