# Privacy Policy

_Last updated: 2026-11-12_

## What this plugin collects

This plugin (SuanLinFang AI Capabilities) does not collect, store or log
any user data by itself. It does not set persistent storage, endpoints,
or model permissions. The only credential is the SuanLinFang API key the
user pastes into the Dify provider credentials, which is stored by the
Dify platform and never logged, echoed or included in any error message.

## What this plugin sends to third parties

To run a tool, the plugin sends the tool inputs the user (or the agent)
supplies directly to the SuanLinFang API at `https://suanlinfang.cn/v1`,
authorized by the user's own API key:

- `transcribe_audio` / `submit_transcription_task`: the audio URL,
  optional language code, optional hotword list. For task submission the
  audio file is downloaded from that URL and streamed to SuanLinFang's
  object storage (presigned upload URL under `*.aliyuncs.com`).
- `synthesize_speech` / `submit_speech_task`: the text to synthesize, the
  voice code and audio format.
- `list_tts_voices`: no user content.
- `recognize_image`: the image URL, tier and optional recognition prompt.
- `submit_document_task`: the PDF URL, tier and optional prompt; the file
  is downloaded and streamed to presigned object storage as above.
- `get_*` task queries: the task number.
- `decide`: the business state text/JSON and the question set.

SuanLinFang stores these inputs as inference records for billing and
result retrieval (see
[suanlinfang.cn](https://suanlinfang.cn) for its own terms). Inputs are
used to process the request only; the plugin author sees no user data.

## Where data goes

- `suanlinfang.cn` — the API endpoint for all tools.
- `*.aliyuncs.com` — presigned object-storage URLs for large-file uploads
  and result downloads, issued per request by the SuanLinFang API.

## Contact

For privacy questions about this plugin contact wjlcuky@gmail.com.
