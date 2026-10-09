---
title: Cafe Music Clips
emoji: 🎵
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 6.2.0
python_version: "3.12"
app_file: app.py
# A FREE account can only host Gradio Spaces on ZeroGPU (see below).
# This key is only a hint shown to people who duplicate the Space; the real
# hardware is picked when you create the Space (or in Settings).
suggested_hardware: zero-a10g
startup_duration_timeout: 1h
models:
  - ACE-Step/Ace-Step1.5
license: mit
short_description: Short instrumental cafe/lo-fi clips from ACE-Step 1.5
---

# Cafe Music Clips

Makes short instrumental clips (lo-fi, cafe jazz, bossa nova, ambient, solo
piano) with [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) turbo
(MIT licence). It has one API endpoint, `generate(style, words)`, which returns
an audio file.

## Read this first: which free hardware?

Hugging Face changed its rules. **On a free account you can no longer create a
Gradio Space on "CPU basic"**. CPU basic itself costs nothing per hour, but
creating a Gradio or Docker Space now needs the PRO plan ($9/month). What a
free account *can* do is host up to **2 Gradio Spaces on ZeroGPU**, as long as
the account has a verified email and is more than 30 days old.

This app works on either one and detects which it is on:

| Hardware | Cost | Clip | Time per clip |
|---|---|---|---|
| **ZeroGPU** (recommended, free) | free; each caller gets a daily GPU allowance | 30 s | a few seconds of GPU time, plus queue wait |
| CPU basic (2 vCPU, 16 GB) | needs PRO plan | 10 s by default | roughly 5 to 15 min for 10 s (estimate); RAM is tight |

The ZeroGPU allowance belongs to whoever calls the Space: about 2 minutes of
GPU per day for anonymous callers and 5 minutes for a logged-in free account.
Each call reserves up to `ZEROGPU_SECONDS` (45 s by default), but you are
charged for the time actually used.

## How to create the Space (no coding needed)

1. Log in at huggingface.co (a free account is fine for ZeroGPU).
2. Open <https://huggingface.co/new-space>.
3. Pick a **Space name** such as `cafe-music`. Set **SDK** to **Gradio**.
   Set **Hardware** to **ZeroGPU** (choose **CPU basic** only if you are on
   PRO and accept slow clips). Leave visibility as **Public**.
4. Click **Create Space**.
5. Open the **Files** tab, then **Add file → Upload files**. Drag in
   `app.py`, `requirements.txt` and this `README.md` (replace the one the Space
   made for you). Click **Commit**.
   * For a CPU Space, upload `requirements-cpu.txt` renamed to
     `requirements.txt` instead. It is smaller because it skips the GPU libraries.
6. Wait. The **Logs** tab shows the build. The first start downloads about
   6.3 GB of model files, which can take 10–20 minutes. When it says
   `Model ready on ...`, the status badge turns **Running**.
7. Try it on the **App** tab. Then copy the Space name, which looks like
   `your-username/cafe-music`. Your website needs this name. The API address is
   `https://your-username-cafe-music.hf.space` (lowercase; `/` and `_` become `-`).

The Space goes to sleep after 48 hours without visits. The next request wakes
it, but that request waits for the full start-up (minutes, because the model has
to load again), so your site should allow for a slow first call.

## Calling it from your website's server

Two HTTP steps (the Gradio REST API). A public Space does not need a token.

```bash
# 1) Start a job. "data" is [style, words].
curl -X POST https://your-username-cafe-music.hf.space/gradio_api/call/generate \
     -H "Content-Type: application/json" \
     -d '{"data": ["lofi", "rainy morning"]}'
# -> {"event_id":"abc123"}

# 2) Wait for the result (Server-Sent Events; keep the connection open).
curl -N https://your-username-cafe-music.hf.space/gradio_api/call/generate/abc123
# event: heartbeat   (repeats while it works)
# event: complete
# data: [{"path": "...", "url": "https://...hf.space/gradio_api/file=/tmp/.../x.wav", ...}]
```

Download the `url` from the `complete` event. It is a 48 kHz stereo WAV file,
about 5.8 MB for 30 s, so convert it to MP3/Opus on your server if you plan to
store it. An `event: error` line means it failed. Files are temporary, so
download them right away.

Optional: add the header `Authorization: Bearer hf_...` with a free read token
to both requests. On ZeroGPU this makes calls use *your account's* larger daily
allowance instead of the anonymous one.

## Settings (Space → Settings → Variables)

* `CLIP_SECONDS`: clip length (default 30 on GPU, 10 on CPU).
* `STEPS`: diffusion steps (default 8, the turbo model's native count; 4 is faster but rougher).
* `ZEROGPU_SECONDS`: GPU time reserved per call on ZeroGPU (default 45).

## Notes

* Instrumental only: lyrics are fixed to `[Instrumental]`. Your `words` only
  add mood to the description, and anything except letters, digits and basic
  punctuation is removed (80 characters max).
* ACE-Step's "LM planner" (3.8 GB) is deliberately not used. Instrumental clips
  don't need it, and on CPU it would not fit in RAM.
* On CPU the weights run in fp32 and take about 12.7 GB, which is close to CPU
  basic's 16 GB. Jobs run one at a time.
