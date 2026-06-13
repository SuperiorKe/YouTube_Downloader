# TubeVault — Personal Offline-First YouTube PWA

*Design doc produced via gstack office-hours (2026-06-12). Owner: SuperiorKe.*

## Segment research (summary)

- The ad-free Snaptube-alternative space on Android is dominated by sideloaded
  open-source native apps: NewPipe, Seal, ytdlnis. All require APK sideloading
  and manual updates.
- Web downloader sites (y2mate-style) are ad-riddled — the exact pain the user
  is escaping.
- **Gap / wedge:** a *personal*, passcode-protected, ad-free PWA on the user's
  own Vercel account, installable from the browser (no sideloading), with an
  offline library. Not a product for the public — a tool for one person.

## Office-hours forcing questions

| Question | Answer |
|---|---|
| Desperate specificity — what do you grab 9/10 times? | **Videos to watch offline** |
| Demand reality — current workaround? | Snaptube, hates the ads |
| Status quo competitors | NewPipe/Seal (sideload friction), ad-sites (ads) |
| Narrowest wedge | YouTube-only, video-first, single user |
| Access model | **Passcode** (`ACCESS_KEY` env var, enforced server-side) |
| Future-fit | Multi-source later; HD merge later; this v1 must work on a phone this week |

## v1 scope (the wedge)

Paste a YouTube URL → preview title/thumbnail → save **Video (progressive MP4,
~360p)** or **Audio (M4A)** into an in-browser offline library (IndexedDB) →
watch/listen offline. Installable PWA (manifest + service worker).

Explicitly **out** of v1: HD video (needs ffmpeg merge → impossible on
serverless), playlists, multi-source, search, accounts.

## Architecture

```
public/            static PWA (vanilla JS, no framework)
  index.html       gate → add → preview → library → player
  app.js           IndexedDB library, download-with-progress, key handling
  sw.js            offline-first app shell (cache-first static, network-only API)
  manifest.webmanifest + icons
api/               Vercel Node serverless functions
  info.js          GET ?url= → {title, author, seconds, thumbnail, video{}, audio{}}
  download.js      GET ?url=&kind=video|audio → streams bytes (proxy; stream URLs are IP-locked)
  health.js        GET → {ok, locked}
  _lib.js          shared: youtubei.js client w/ ANDROID→IOS→WEB fallback, key check
```

- Extractor: **youtubei.js** (Innertube). Client fallback chain ANDROID → IOS →
  WEB to mitigate datacenter bot-checks. Optional `YT_COOKIES` env escape hatch.
- Auth: `ACCESS_KEY` env var. If set, API returns 401 without matching
  `x-access-key` header / `?key=` param. Client stores the key in localStorage
  after first entry.
- Streaming: the function proxies media bytes (googlevideo URLs are IP-locked
  to the resolver), `maxDuration: 60`.

## Known risks / open questions

1. **Datacenter bot-check** — YouTube increasingly blocks cloud IPs
   ("Sign in to confirm you're not a bot", yt-dlp #15865). Mitigations shipped:
   client fallback chain + `YT_COOKIES` env. May still fail; verified in QA.
2. **360p cap** — progressive formats only. HD requires an ffmpeg-merge backend
   (e.g. a small VPS or container job) — candidate v2.
3. **60s function cap** — very long videos may not finish streaming through the
   function on the Hobby plan.
4. **Extractor rot** — youtubei.js breaks when YouTube changes; pin + bump cadence.
5. **ACCESS_KEY must be set manually** in Vercel project settings (no env
   management from this session). Until set, the app runs unlocked.
