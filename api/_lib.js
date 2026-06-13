// Shared helpers for the TubeVault API functions.
import { Innertube } from 'youtubei.js';
import { BG } from 'bgutils-js';
import { JSDOM } from 'jsdom';

// YouTube's web BotGuard request key (public, stable).
const REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo';

// Clients tried in order. WEB carries the poToken we mint below; the mobile
// clients are kept as a fallback.
const CLIENTS = ['WEB', 'ANDROID', 'IOS'];

let ytPromise = null;

/**
 * Mint a session-bound BotGuard proof-of-origin token (poToken). YouTube
 * requires this for playback from flagged/datacenter IPs (otherwise every
 * request returns LOGIN_REQUIRED). Runs the BotGuard VM inside a throwaway
 * jsdom; the browser globals are removed afterwards so youtubei.js still sees
 * a clean Node environment.
 */
async function generatePoToken(visitorData) {
  const dom = new JSDOM('<!DOCTYPE html><html><head></head><body></body></html>', {
    url: 'https://www.youtube.com/',
    referrer: 'https://www.youtube.com/',
  });

  const installed = [];
  for (const key of ['window', 'document', 'location', 'origin', 'navigator']) {
    if (globalThis[key] === undefined && dom.window[key] !== undefined) {
      Object.defineProperty(globalThis, key, { value: dom.window[key], configurable: true, writable: true });
      installed.push(key);
    }
  }

  try {
    const bgConfig = {
      fetch: (input, init) => fetch(input, init),
      globalObj: globalThis,
      identifier: visitorData,
      requestKey: REQUEST_KEY,
    };

    const challenge = await BG.Challenge.create(bgConfig);
    if (!challenge) throw new Error('BotGuard challenge was empty');

    const interpreterJs = challenge.interpreterJavascript?.privateDoNotAccessOrElseSafeScriptWrappedValue;
    if (!interpreterJs) throw new Error('BotGuard interpreter missing');
    new Function(interpreterJs)();

    const { poToken } = await BG.PoToken.generate({
      program: challenge.program,
      globalName: challenge.globalName,
      bgConfig,
    });
    if (!poToken) throw new Error('poToken was empty');
    return poToken;
  } finally {
    for (const key of installed) {
      try { delete globalThis[key]; } catch { /* ignore */ }
    }
  }
}

async function createInnertube() {
  // Bootstrap a player-less client just to obtain visitor data for the poToken.
  const bootstrap = await Innertube.create({ retrieve_player: false });
  const visitorData = bootstrap.session.context.client.visitorData;

  let poToken;
  try {
    poToken = await generatePoToken(visitorData);
    console.log('poToken minted (%d chars)', poToken.length);
  } catch (e) {
    console.error('poToken generation failed:', String((e && e.message) || e));
  }

  const opts = {};
  // Optional extra escape hatch: a logged-in cookie header via env var.
  if (process.env.YT_COOKIES) opts.cookie = process.env.YT_COOKIES;
  if (poToken && visitorData) {
    opts.po_token = poToken;
    opts.visitor_data = visitorData;
  }
  return Innertube.create(opts);
}

function getYT() {
  if (!ytPromise) {
    ytPromise = createInnertube().catch((e) => {
      ytPromise = null; // allow a fresh attempt on the next request
      throw e;
    });
  }
  return ytPromise;
}

/** Enforce the ACCESS_KEY passcode when configured. Returns true if allowed. */
function checkKey(req, res) {
  const required = process.env.ACCESS_KEY;
  if (!required) return true; // unlocked until the env var is set
  const provided = req.headers['x-access-key'] || (req.query && req.query.key);
  if (provided === required) return true;
  res.status(401).json({ error: 'unauthorized', locked: true });
  return false;
}

const ID_PATTERNS = [
  /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|live\/|embed\/))([a-zA-Z0-9_-]{11})/,
  /youtu\.be\/([a-zA-Z0-9_-]{11})/,
  /^([a-zA-Z0-9_-]{11})$/,
];

function extractVideoId(input) {
  if (!input) return null;
  for (const re of ID_PATTERNS) {
    const m = String(input).trim().match(re);
    if (m) return m[1];
  }
  return null;
}

/** getBasicInfo with a client fallback chain. Returns {info, client}. */
async function getInfoWithFallback(videoId) {
  const yt = await getYT();
  let lastErr = null;
  for (const client of CLIENTS) {
    try {
      const info = await yt.getBasicInfo(videoId, { client });
      const status = info.playability_status;
      if (status && status.status !== 'OK') {
        lastErr = new Error(`${status.status}: ${status.reason || 'not playable'} (client ${client})`);
        continue;
      }
      if (!info.streaming_data) {
        lastErr = new Error(`no streaming data (client ${client})`);
        continue;
      }
      return { info, client };
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error('extraction failed');
}

/** Pick the best progressive (muxed) video format and best mp4 audio format. */
function pickFormats(info) {
  const sd = info.streaming_data || {};
  const progressive = (sd.formats || []).slice().sort((a, b) => (b.height || 0) - (a.height || 0));
  const video = progressive.find((f) => (f.mime_type || '').includes('mp4')) || progressive[0] || null;

  const audios = (sd.adaptive_formats || [])
    .filter((f) => f.has_audio && !f.has_video)
    .sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0));
  const audio = audios.find((f) => (f.mime_type || '').includes('mp4a')) || audios[0] || null;

  return { video, audio };
}

function isBotCheck(message) {
  return /sign in to confirm|not a bot|login_required|captcha|consent/i.test(String(message || ''));
}

function sanitizeFilename(name) {
  return (
    String(name || 'media')
      .replace(/[^\w\s.-]/g, '')
      .trim()
      .slice(0, 80) || 'media'
  );
}

export {
  getYT,
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  sanitizeFilename,
};
