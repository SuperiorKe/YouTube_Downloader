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
      // debug=fetch: exercise the REAL youtubei.js download path (proper stream
      // headers + cpn) but only pull a 3-byte range, so we learn whether
      // googlevideo serves to this datacenter IP without ingesting the file.
      if (req.query.debug === 'fetch') {
        try {
          const webStream = await info.download({
            itag: format.itag,
            range: { start: 0, end: 2 },
          });
          let bytes = 0;
          for await (const chunk of Readable.fromWeb(webStream)) bytes += chunk.length;
          out.probeOk = true;
          out.probeBytes = bytes;
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
