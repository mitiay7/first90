# Automated demo video

First 90 includes a deterministic production pipeline for the OpenAI Build Week demo. It measures eight supplied narration clips, derives one shared timeline, records the real deployed product, assembles narration and licensed background music, renders a YouTube-ready MP4, and validates the deliverable.

## Safety and accuracy

- Official rules require a video shorter than three minutes. The pipeline enforces a stricter 178-second ceiling.
- The public participant and all actions recorded in the web demo are fictional.
- Recording starts and ends with a demo reset.
- The coach scene records the deterministic fallback when no API key is configured. With
  `OPENAI_API_KEY`, the same scene records a live GPT‑5.6 Responses API result.
- Journal text never enters the coach request or Team Studio.
- Telegram is demonstrated through First 90 guidance and reviewer surfaces. Personal Telegram UI, contacts, and secrets are never recorded.
- Background music is **One Cool Minute** by Loyalty Freak Music, released under CC0 1.0. Its committed checksum and provenance are verified before every render.

## Requirements

- Node.js 22
- pnpm 11.15.1
- Playwright Chromium
- FFmpeg and ffprobe 8+
- Network access to the deployed First 90 application

Install browser support once:

```bash
pnpm install
pnpm exec playwright install chromium
```

## Narration

Keep the eight unmodified source files in `demo/voiceover/`:

```text
01.mp3  02.mp3  03.mp3  04.mp3
05.mp3  06.mp3  07.mp3  08.mp3
```

The pipeline normalizes generated intermediates to 48 kHz stereo PCM. Source MP3 files are never modified.

## Commands

```bash
pnpm demo:inspect-audio
pnpm demo:timeline
pnpm demo:record
pnpm demo:render
pnpm demo:validate
pnpm demo:video --no-captions
```

Default target:

```text
https://first90.hub.lea-dev.site
```

Override it when needed:

```bash
DEMO_BASE_URL=http://127.0.0.1:8000 pnpm demo:video --no-captions
```

## Output

```text
artifacts/video/first90-demo.mp4
```

Generated evidence includes exact audio inspection, timeline, browser recording report with the
recorded coach mode, console and API logs, Playwright trace, FFmpeg command and log, and final
codec/state validation.

The final video is 1920×1080, 30 fps, H.264 High, yuv420p, and AAC 192 kbps with `faststart` enabled. Music is ducked under narration and raised during the opening and ending card.

Optional burned-in captions:

```bash
pnpm demo:video --captions
```

This requires `demo/voiceover/captions.srt`.
