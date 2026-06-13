// Shared helpers for the TubeVault API functions.
import { Innertube } from 'youtubei.js';
import { BG, buildURL, getHeaders } from 'bgutils-js';
import { JSDOM } from 'jsdom';

// YouTube's web BotGuard request key (public, stable).
const REQUEST_KEY = 'O43z0dpjhgX20SCx4KAo';

// WEB client carries the proof-of-origin token. Mobile clients need their own
// attestation and just fail from datacenter IPs, so we use WEB only.
const CLIENTS = ['WEB'];

let ytPromise = null;

// Cached BotGuard integrity-token minter. It can mint many per-identifier
// tokens until the integrity token expires, so we reuse it across requests.
let minterPromise = null;
let minterExpiresAt = 0;

// Diagnostics surfaced in API responses (collapsed runtime logs are unreadable).
const diag = { poToken: 'not-attempted', visitor: 'none', auth: 'anon' };
function getPoTokenStatus() {
  return `${diag.poToken}|visitor:${diag.visitor}|auth:${diag.auth}`;
}

/** Install a throwaway jsdom so the BotGuard VM has browser globals. */
function ensureDom() {
  if (Object.getOwnPropertyDescriptor(globalThis, 'window')) return;
  const dom = new JSDOM('<!DOCTYPE html><html><head></head><body></body></html>', {
    url: 'https://www.youtube.com/',
    referrer: 'https://www.youtube.com/',
  });
  for (const key of ['window', 'document', 'location', 'origin', 'navigator']) {
    if (globalThis[key] === undefined && dom.window[key] !== undefined) {
      Object.defineProperty(globalThis, key, { value: dom.window[key], configurable: true, writable: true });
    }
  }
}

/**
 * Build a BotGuard WebPoMinter. Runs the BotGuard challenge + VM, takes a
 * snapshot, exchanges it for an integrity token, and returns a minter that can
 * produce proof-of-origin tokens bound to any identifier (visitor data for the
 * session token, video id for the per-request content token).
 */
async function buildMinter(visitorData) {
  ensureDom();
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

  const botguard = await BG.BotGuardClient.create({
    program: challenge.program,
    globalName: challenge.globalName,
    globalObj: globalThis,
  });

  const webPoSignalOutput = [];
  const botguardResponse = await botguard.snapshot({ webPoSignalOutput });

  const itResponse = await fetch(buildURL('GenerateIT', true), {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify([REQUEST_KEY, botguardResponse]),
  });
  if (!itResponse.ok) throw new Error(`GenerateIT HTTP ${itResponse.status}`);
  const itData = await itResponse.json();
  const integrityToken = itData?.[0];
  if (!integrityToken) throw new Error('integrity token missing');

  const ttlSecs = Number(itData?.[1]) || 3600;
  minterExpiresAt = Date.now() + Math.max(60, ttlSecs - 120) * 1000;

  return BG.WebPoMinter.create({ integrityToken, estimatedTtlSecs: ttlSecs }, webPoSignalOutput);
}

function getMinter(visitorData) {
  if (!minterPromise || Date.now() > minterExpiresAt) {
    minterPromise = buildMinter(visitorData).catch((e) => {
      minterPromise = null;
      throw e;
    });
  }
  return minterPromise;
}

/** Mint a proof-of-origin token bound to `identifier` (visitor data or video id). */
async function mintPoToken(visitorData, identifier) {
  const minter = await getMinter(visitorData);
  return minter.mintAsWebsafeString(identifier);
}

async function createInnertube() {
  const cookie = process.env.YT_COOKIES || undefined;

  // Bootstrap a player-less client (with cookie, if any) so the visitor data
  // and minted poToken match the session we will actually use.
  const bootstrap = await Innertube.create({ retrieve_player: false, cookie });
  const visitorData = bootstrap.session.context.client.visitorData;
  diag.visitor = visitorData ? `len${visitorData.length}` : 'none';
  diag.auth = cookie ? 'cookie' : 'anon';

  let sessionPoToken;
  try {
    sessionPoToken = await mintPoToken(visitorData, visitorData);
    diag.poToken = `minted:${sessionPoToken.length}`;
    console.log('session poToken minted (%d chars)', sessionPoToken.length);
  } catch (e) {
    diag.poToken = `failed:${String((e && e.message) || e)}`.slice(0, 300);
    console.error('minter/poToken failed:', diag.poToken);
  }

  const opts = {};
  if (cookie) opts.cookie = cookie;
  if (sessionPoToken && visitorData) {
    opts.po_token = sessionPoToken;
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

/** getBasicInfo using a content-bound poToken for the requested video. */
async function getInfoWithFallback(videoId) {
  const yt = await getYT();

  // Mint a proof-of-origin token bound to THIS video id — the player rejects
  // the session-bound token with LOGIN_REQUIRED otherwise.
  let contentPoToken;
  try {
    const visitorData = yt.session.context.client.visitorData;
    contentPoToken = await mintPoToken(visitorData, videoId);
  } catch (e) {
    console.error('content poToken failed:', String((e && e.message) || e));
  }

  let lastErr = null;
  for (const client of CLIENTS) {
    try {
      const options = contentPoToken ? { client, po_token: contentPoToken } : { client };
      const info = await yt.getBasicInfo(videoId, options);
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
  getPoTokenStatus,
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  sanitizeFilename,
};
