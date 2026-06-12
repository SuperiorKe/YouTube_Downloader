// Shared helpers for the TubeVault API functions.
const { Innertube } = require('youtubei.js');

// Clients tried in order. ANDROID/IOS innertube clients are less likely to hit
// YouTube's datacenter bot-check than WEB.
const CLIENTS = ['ANDROID', 'IOS', 'WEB'];

let ytPromise = null;

function getYT() {
  if (!ytPromise) {
    const opts = {};
    // Optional escape hatch if the datacenter IP gets bot-checked:
    // set YT_COOKIES to a logged-in cookie header string in Vercel env vars.
    if (process.env.YT_COOKIES) opts.cookie = process.env.YT_COOKIES;
    ytPromise = Innertube.create(opts);
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

module.exports = {
  getYT,
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  sanitizeFilename,
};
