# SuanLinFang AI Capabilities for Dify

Speech-to-text, text-to-speech, image OCR and typed decision-making for
[Dify](https://dify.ai) workflows and agents, backed by the
[SuanLinFang](https://suanlinfang.cn) API. One provider, eleven tools,
bring your own SuanLinFang API key.

## Features

- **Speech-to-text** — short audio (≤3 min / 20MB) synchronously; long
  audio tasks up to 2 hours / 500MB with 180s segmentation and stitching.
  Auto language detection (Mandarin, English, 22 Chinese dialects) and
  hotword biasing for proper nouns.
- **Text-to-speech** — multi-voice synthesis; short text (≈1000 Chinese
  characters) synchronously; long-text tasks up to 200,000 characters.
- **Image OCR** — single images (png/jpg/webp/bmp) with
  standard/accurate tiers; accurate tier accepts custom recognition
  prompts (e.g. "extract only the amount column"). PDF document tasks up
  to 500 pages.
- **Typed decision-making** — 1-32 typed questions (choice / true-false /
  ordered grading) over a business state, answered with calibrated
  probabilities; no generated text, no conversation memory.

## Setup

1. Register at [suanlinfang.cn](https://suanlinfang.cn) (new accounts get
   a CNY 10 trial credit) and create an API key at
   [API Keys](https://suanlinfang.cn/consume-web/api-keys.html).
2. In Dify, install this plugin and paste the key (starts with `nk-`)
   into the provider credentials. The key is validated with a read-only
   request (`GET /v1/tts/voices`) that is not billed.

## Usage

Every tool returns a JSON artifact for chaining in Workflow nodes.

- Sync tools (`transcribe_audio`, `synthesize_speech`, `recognize_image`,
  `list_tts_voices`, `decide`) return results directly.
- Task tools (`submit_*` / `get_*` pairs) return a `taskNo`; poll with the
  matching `get_*` tool every 10-30 seconds until `status` is
  `success`/`failed`.

## Billing

Billed to your SuanLinFang account by usage: STT ≈ CNY 0.5/hour of audio;
TTS ≈ CNY 2 per 10k characters; OCR ≈ CNY 0.005-0.015 per page; decisions
≈ CNY 2 per million input tokens. Failed requests are not billed.

## Privacy

See [PRIVACY.md](PRIVACY.md). The plugin sends only the inputs required
by each tool (audio/image/PDF URLs, text, question sets) to
`suanlinfang.cn`; the API key stays in your Dify workspace and is never
logged.
