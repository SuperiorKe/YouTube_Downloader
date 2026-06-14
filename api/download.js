import { Readable } from 'stream';
import {
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  sanitizeFilename,
  getYT,
} from './_lib.js';

// Streams the media bytes through the function: googlevideo stream URLs are
// IP-locked to whoever resolved them, so the phone cannot fetch them directly.
export default async (req, res) => {
  if (!checkKey(req, res)) return;

  const videoId = extractVideoId(req.query.url);
  const kind = req.query.kind === 'audio' ? 'audio' : 'video';
  if (!videoId) {
    res.status(400).json({ error: 'missing or invalid YouTube URL' });
    return;
  }

  try {
    const { info } = await getInfoWithFallback(videoId);
    const { video, audio } = pickFormats(info);
    const format = kind === 'audio' ? audio : video;
    if (!format) {
      res.status(404).json({ error: `no ${kind} format available` });
      return;
    }

    if (req.query.debug) {
      const yt = await getYT();
      const out = {
        itag: format.itag,
        mime: format.mime_type,
        hasUrl: !!format.url,
        hasSignatureCipher: !!format.signature_cipher,
        hasCipher: !!format.cipher,
        playerPresent: !!(yt.session && yt.session.player),
        sabr: !!(info.streaming_data && info.streaming_data.server_abr_streaming_url),
      };
      // debug=fetch: decipher the URL, surface its key params (pot present? ip?),
      // and capture googlevideo's actual 403 body so we know WHY it refuses.
      if (req.query.debug === 'fetch') {
        try {
          const url = await format.decipher(yt.session.player);
          const u = new URL(url);
          out.paramKeys = [...u.searchParams.keys()];
          out.hasPot = u.searchParams.has('pot');
          out.potLen = (u.searchParams.get('pot') || '').length;
          out.ip = u.searchParams.get('ip');
          out.c = u.searchParams.get('c');
          out.mn = u.searchParams.get('mn');
          const probe = await fetch(url, {
            method: 'GET',
            headers: {
              'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              Origin: 'https://www.youtube.com',
              Referer: 'https://www.youtube.com/',
              Range: 'bytes=0-1',
            },
            redirect: 'follow',
          });
          out.upstreamStatus = probe.status;
          out.upstreamBody = (await probe.text()).slice(0, 300);
          // Compare the URL's pinned ip to this lambda's real egress ip. A
          // mismatch means Vercel's pooled egress can't fetch IP-locked media.
          try {
            const egress = await (await fetch('https://api.ipify.org')).text();
            out.egressIp = egress.trim();
            out.ipMatches = out.egressIp === out.ip;
          } catch (e) {
            out.egressIpError = String((e && e.message) || e);
          }
        } catch (e) {
          out.probeError = String((e && e.message) || e);
        }
      }
      res.status(200).json(out);
      return;
    }

    const title = sanitizeFilename(info.basic_info.title);
    const ext = kind === 'audio' ? 'm4a' : 'mp4';
    const mime = (format.mime_type || '').split(';')[0] || (kind === 'audio' ? 'audio/mp4' : 'video/mp4');

    res.setHeader('Content-Type', mime);
    res.setHeader('Content-Disposition', `attachment; filename="${title}.${ext}"`);
    if (format.content_length) res.setHeader('Content-Length', String(format.content_length));

    const webStream = await info.download({ itag: format.itag });
    const nodeStream = Readable.fromWeb(webStream);
    nodeStream.on('error', (err) => {
      console.error('stream error:', err.message);
      res.end();
    });
    nodeStream.pipe(res);
  } catch (e) {
    const msg = String((e && e.message) || e);
    console.error('download error:', msg);
    if (!res.headersSent) {
      res.status(isBotCheck(msg) ? 503 : 500).json({ error: msg, botCheck: isBotCheck(msg) });
    } else {
      res.end();
    }
  }
};
