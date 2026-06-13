import {
  checkKey,
  extractVideoId,
  getInfoWithFallback,
  pickFormats,
  isBotCheck,
  getPoTokenStatus,
} from './_lib.js';

export default async (req, res) => {
  if (!checkKey(req, res)) return;

  const videoId = extractVideoId(req.query.url);
  if (!videoId) {
    res.status(400).json({ error: 'missing or invalid YouTube URL' });
    return;
  }

  try {
    const { info, client } = await getInfoWithFallback(videoId);
    const b = info.basic_info;
    const { video, audio } = pickFormats(info);

    const fmt = (f, kind) =>
      f
        ? {
            kind,
            itag: f.itag,
            quality: f.quality_label || (f.bitrate ? `${Math.round(f.bitrate / 1000)}kbps` : null),
            mime: (f.mime_type || '').split(';')[0],
            size: f.content_length ? Number(f.content_length) : null,
          }
        : null;

    res.status(200).json({
      id: b.id,
      title: b.title,
      author: b.author,
      seconds: b.duration || 0,
      thumbnail: (b.thumbnail && b.thumbnail[0] && b.thumbnail[0].url) || null,
      client,
      video: fmt(video, 'video'),
      audio: fmt(audio, 'audio'),
    });
  } catch (e) {
    const msg = String((e && e.message) || e);
    console.error('info error:', msg);
    res.status(isBotCheck(msg) ? 503 : 500).json({
      error: msg,
      botCheck: isBotCheck(msg),
      poToken: getPoTokenStatus(),
    });
  }
};
