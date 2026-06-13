import { Readable } from 'stream';
import {
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  sanitizeFilename,
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
