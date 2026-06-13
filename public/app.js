/* TubeVault — offline-first personal YouTube library. */
(() => {
  'use strict';

  // ── tiny IndexedDB wrapper ────────────────────────────────────────────
  const DB_NAME = 'tubevault';
  const STORE = 'media';

  function openDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: 'id' });
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function idb(mode, fn) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      const out = fn(tx.objectStore(STORE));
      tx.oncomplete = () => resolve(out.result !== undefined ? out.result : out);
      tx.onerror = () => reject(tx.error);
    });
  }

  const dbPut = (item) => idb('readwrite', (s) => s.put(item));
  const dbDel = (id) => idb('readwrite', (s) => s.delete(id));
  const dbGet = (id) => idb('readonly', (s) => s.get(id));
  const dbAll = () => idb('readonly', (s) => s.getAll());

  // ── elements ──────────────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const els = {
    gate: $('gate'), gateKey: $('gate-key'), gateSubmit: $('gate-submit'), gateError: $('gate-error'),
    form: $('add-form'), url: $('url-input'), fetchBtn: $('fetch-btn'), addStatus: $('add-status'),
    preview: $('preview'), pvThumb: $('pv-thumb'), pvTitle: $('pv-title'), pvSub: $('pv-sub'),
    saveVideo: $('save-video'), saveAudio: $('save-audio'),
    dlProgress: $('dl-progress'), dlBar: $('dl-bar'), dlStatus: $('dl-status'),
    playerCard: $('player-card'), player: $('player'), playerTitle: $('player-title'),
    library: $('library'), libEmpty: $('lib-empty'), libCount: $('lib-count'),
    netDot: $('net-dot'), storageInfo: $('storage-info'),
  };

  let currentInfo = null;
  let playingURL = null;

  // ── access key ────────────────────────────────────────────────────────
  const getKey = () => localStorage.getItem('tv_key') || '';
  const setKey = (k) => localStorage.setItem('tv_key', k);

  function showGate(wrong) {
    els.gate.classList.remove('hidden');
    els.gateError.classList.toggle('hidden', !wrong);
    els.gateKey.focus();
  }

  els.gateSubmit.addEventListener('click', () => {
    setKey(els.gateKey.value.trim());
    els.gate.classList.add('hidden');
    if (els.url.value) els.form.requestSubmit();
  });
  els.gateKey.addEventListener('keydown', (e) => { if (e.key === 'Enter') els.gateSubmit.click(); });

  async function api(path, params = {}) {
    const q = new URLSearchParams(params);
    const resp = await fetch(`/api/${path}?${q}`, { headers: { 'x-access-key': getKey() } });
    if (resp.status === 401) {
      showGate(Boolean(getKey()));
      throw new Error('locked');
    }
    return resp;
  }

  // ── helpers ───────────────────────────────────────────────────────────
  const fmtBytes = (n) => {
    if (!n && n !== 0) return '?';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
    return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
  };
  const fmtDur = (s) => {
    s = Math.round(s || 0);
    const m = Math.floor(s / 60), sec = s % 60;
    const h = Math.floor(m / 60);
    return h ? `${h}:${String(m % 60).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : `${m}:${String(sec).padStart(2, '0')}`;
  };
  const setStatus = (el, text) => {
    el.textContent = text || '';
    el.classList.toggle('hidden', !text);
  };

  // ── fetch info / preview ──────────────────────────────────────────────
  els.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    els.preview.classList.add('hidden');
    setStatus(els.addStatus, 'Fetching…');
    els.fetchBtn.disabled = true;
    try {
      const resp = await api('info', { url: els.url.value.trim() });
      const data = await resp.json();
      if (!resp.ok) {
        setStatus(els.addStatus, data.botCheck
          ? 'YouTube bot-checked the server. Try again, or set YT_COOKIES (see docs).'
          : `Error: ${data.error || resp.status}`);
        return;
      }
      currentInfo = data;
      setStatus(els.addStatus, '');
      els.pvThumb.src = data.thumbnail || '';
      els.pvTitle.textContent = data.title;
      els.pvSub.textContent = `${data.author || ''} · ${fmtDur(data.seconds)}`;
      els.saveVideo.textContent = data.video
        ? `Save Video ${data.video.quality || ''} (${fmtBytes(data.video.size)})` : 'No video format';
      els.saveVideo.disabled = !data.video;
      els.saveAudio.textContent = data.audio
        ? `Audio (${fmtBytes(data.audio.size)})` : 'No audio';
      els.saveAudio.disabled = !data.audio;
      els.preview.classList.remove('hidden');
    } catch (err) {
      if (err.message !== 'locked') setStatus(els.addStatus, `Error: ${err.message}`);
    } finally {
      els.fetchBtn.disabled = false;
    }
  });

  // ── download & store ──────────────────────────────────────────────────
  async function saveMedia(kind) {
    if (!currentInfo) return;
    const fmtMeta = currentInfo[kind];
    const expected = (fmtMeta && fmtMeta.size) || 0;
    els.saveVideo.disabled = els.saveAudio.disabled = true;
    els.dlProgress.classList.remove('hidden');
    els.dlBar.style.width = '0%';
    setStatus(els.dlStatus, 'Downloading…');

    try {
      const resp = await api('download', { url: els.url.value.trim(), kind });
      if (!resp.ok) {
        let msg = `HTTP ${resp.status}`;
        try { const j = await resp.json(); msg = j.botCheck ? 'Bot-check hit — retry or set YT_COOKIES.' : (j.error || msg); } catch (_) {}
        throw new Error(msg);
      }
      const total = Number(resp.headers.get('content-length')) || expected;
      const reader = resp.body.getReader();
      const chunks = [];
      let received = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        received += value.length;
        if (total) els.dlBar.style.width = `${Math.min(100, (received / total) * 100)}%`;
        setStatus(els.dlStatus, `Downloading… ${fmtBytes(received)}${total ? ` / ${fmtBytes(total)}` : ''}`);
      }
      const mime = resp.headers.get('content-type') || (kind === 'audio' ? 'audio/mp4' : 'video/mp4');
      const blob = new Blob(chunks, { type: mime });
      await dbPut({
        id: `${currentInfo.id}:${kind}`,
        videoId: currentInfo.id,
        kind,
        title: currentInfo.title,
        author: currentInfo.author,
        seconds: currentInfo.seconds,
        mime,
        size: blob.size,
        savedAt: Date.now(),
        blob,
      });
      els.dlBar.style.width = '100%';
      setStatus(els.dlStatus, `Saved ✓ (${fmtBytes(blob.size)}) — available offline`);
      renderLibrary();
      updateStorage();
    } catch (err) {
      if (err.message !== 'locked') setStatus(els.dlStatus, `Failed: ${err.message}`);
    } finally {
      els.saveVideo.disabled = !currentInfo.video;
      els.saveAudio.disabled = !currentInfo.audio;
    }
  }

  els.saveVideo.addEventListener('click', () => saveMedia('video'));
  els.saveAudio.addEventListener('click', () => saveMedia('audio'));

  // ── library & playback ────────────────────────────────────────────────
  async function renderLibrary() {
    const items = (await dbAll()).sort((a, b) => b.savedAt - a.savedAt);
    els.library.innerHTML = '';
    els.libEmpty.classList.toggle('hidden', items.length > 0);
    els.libCount.textContent = items.length ? `(${items.length})` : '';
    for (const item of items) {
      const li = document.createElement('li');

      const kindEl = document.createElement('div');
      kindEl.className = 'lib-kind';
      kindEl.textContent = item.kind === 'audio' ? '🎵' : '🎬';

      const body = document.createElement('div');
      body.className = 'lib-body';
      const t = document.createElement('p');
      t.className = 'lib-title';
      t.textContent = item.title;
      const sub = document.createElement('p');
      sub.className = 'lib-sub';
      sub.textContent = `${fmtDur(item.seconds)} · ${fmtBytes(item.size)}`;
      body.append(t, sub);
      body.addEventListener('click', () => play(item.id));

      const del = document.createElement('button');
      del.className = 'lib-del';
      del.textContent = '🗑';
      del.setAttribute('aria-label', `Delete ${item.title}`);
      del.addEventListener('click', async () => {
        await dbDel(item.id);
        renderLibrary();
        updateStorage();
      });

      li.append(kindEl, body, del);
      els.library.appendChild(li);
    }
  }

  async function play(id) {
    const item = await dbGet(id);
    if (!item) return;
    if (playingURL) URL.revokeObjectURL(playingURL);
    playingURL = URL.createObjectURL(item.blob);
    els.player.src = playingURL;
    els.playerTitle.textContent = item.title;
    els.playerCard.classList.remove('hidden');
    els.playerCard.scrollIntoView({ behavior: 'smooth' });
    els.player.play().catch(() => {});
  }

  // ── status bits ───────────────────────────────────────────────────────
  function updateNet() {
    const online = navigator.onLine;
    els.netDot.className = `dot ${online ? 'online' : 'offline'}`;
    els.netDot.title = online ? 'online' : 'offline — library still works';
    els.fetchBtn.disabled = !online;
  }
  window.addEventListener('online', updateNet);
  window.addEventListener('offline', updateNet);

  async function updateStorage() {
    if (!navigator.storage || !navigator.storage.estimate) return;
    const { usage, quota } = await navigator.storage.estimate();
    els.storageInfo.textContent = `${fmtBytes(usage)} of ${fmtBytes(quota)} used`;
  }

  // ── boot ──────────────────────────────────────────────────────────────
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist();
  updateNet();
  updateStorage();
  renderLibrary();
})();
