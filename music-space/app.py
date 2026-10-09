"""Tiny music-clip generator for a hobby website, built on ACE-Step 1.5 (turbo).

Exposes ONE API endpoint, `/generate(style, words) -> audio file`, that an
outside server calls through the Gradio REST API. Instrumental only.

Runs on either:
  * ZeroGPU (the only Gradio hardware a FREE Hugging Face account can host), or
  * plain CPU (CPU Basic / CPU Upgrade; needs a paid HF plan to create, and slow).
The same file works on both; the hardware is detected at startup.
"""
import os
import re
import sys
import shutil
import tempfile
import time
import urllib.request
import zipfile

# On ZeroGPU the `spaces` package must be imported before torch so it can
# intercept CUDA. HF sets SPACES_ZERO_GPU=true on ZeroGPU hardware.
ON_ZEROGPU = os.environ.get("SPACES_ZERO_GPU", "").lower() in ("1", "true")
if ON_ZEROGPU:
    import spaces  # noqa: F401  (provided by the ZeroGPU runtime / requirements)

import gradio as gr
import torch
from huggingface_hub import snapshot_download

# ---------------------------------------------------------------------------
# Settings (env vars let you tune the Space from Settings > Variables without
# editing code).
# ---------------------------------------------------------------------------
DEVICE = "cuda" if (ON_ZEROGPU or torch.cuda.is_available()) else "cpu"
# Clip length in seconds. 30 s on GPU. On CPU the default is 10 s, because even
# that took ~4 min on a fast Mac limited to 2 threads (see README).
CLIP_SECONDS = float(os.environ.get("CLIP_SECONDS", "30" if DEVICE == "cuda" else "10"))
# Diffusion steps. The turbo model is distilled for 8 steps; fewer is faster
# but sounds rougher. Do not go above 8 for turbo.
STEPS = int(os.environ.get("STEPS", "8"))
# GPU seconds reserved per call on ZeroGPU (counts against the caller's quota).
ZEROGPU_SECONDS = int(os.environ.get("ZEROGPU_SECONDS", "45"))

# ACE-Step aborts any generation that takes longer than this (default 600 s).
# A CPU clip can exceed that, so raise it there. Must be set before import.
os.environ.setdefault("ACESTEP_GENERATION_TIMEOUT", "600" if DEVICE == "cuda" else "1800")
# Note: on CPU, weights stay fp32 (ACE-Step's default). We measured bf16 on
# CPU to be over 3x SLOWER, so the RAM saving is not worth it.

# ACE-Step is not on PyPI, and its pyproject pulls CUDA wheels and flash-attn,
# so we fetch its source at a pinned commit and import it from disk instead
# of pip-installing it. Pinning keeps the Space reproducible.
ACE_COMMIT = "ca1e85fe9430179831e6bc6be790c332190a3866"
ACE_DIR = os.environ.get("ACE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "ace_src")
CKPT_DIR = os.path.join(ACE_DIR, "checkpoints")

# Style -> tag prompt. Keep these plain; the model reads them as a caption.
STYLES = {
    "lofi": "lo-fi hip hop, chill, mellow, dusty drums, warm Rhodes piano, vinyl crackle, relaxed",
    "jazz": "cafe jazz, smooth, upright bass, brushed drums, soft piano trio, cozy coffee shop",
    "bossa": "bossa nova, nylon guitar, gentle shaker, light percussion, warm, Brazilian",
    "ambient": "ambient, atmospheric pads, slow evolving textures, calm, spacious, dreamy",
    "piano": "solo piano, gentle, intimate, felt piano, expressive, soft dynamics",
}
BPM = {"lofi": 80, "jazz": 110, "bossa": 120, "ambient": 70, "piano": 72}


def fetch_ace_source():
    """Download ACE-Step source at ACE_COMMIT once (skipped if already present)."""
    if os.path.isdir(os.path.join(ACE_DIR, "acestep")):
        return
    url = f"https://github.com/ace-step/ACE-Step-1.5/archive/{ACE_COMMIT}.zip"
    tmp = tempfile.mkdtemp()
    zpath = os.path.join(tmp, "ace.zip")
    print(f"Downloading ACE-Step source {ACE_COMMIT[:8]} ...", flush=True)
    urllib.request.urlretrieve(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(tmp)
    src = os.path.join(tmp, f"ACE-Step-1.5-{ACE_COMMIT}")
    shutil.move(src, ACE_DIR)
    shutil.rmtree(tmp, ignore_errors=True)


def fetch_weights():
    """Download only what instrumental text-to-music needs (~6.3 GB).

    We skip the 3.8 GB "5Hz LM" planner: it writes lyrics/structure, which
    instrumental clips don't need, and it would not fit CPU RAM alongside the DiT.
    """
    snapshot_download(
        "ACE-Step/Ace-Step1.5",
        local_dir=CKPT_DIR,
        allow_patterns=["acestep-v15-turbo/*", "vae/*", "Qwen3-Embedding-0.6B/*", "config.json"],
    )


# ---------------------------------------------------------------------------
# Load everything ONCE at startup.
# ---------------------------------------------------------------------------
t0 = time.time()
fetch_ace_source()
fetch_weights()
sys.path.insert(0, ACE_DIR)
os.environ.setdefault("ACESTEP_PROJECT_ROOT", ACE_DIR)

# ACE-Step's precheck insists the LM folder exists and would auto-download
# it. We deliberately don't use the LM, so tell the precheck the bundle is
# complete (the DiT/VAE/text-encoder checks still run normally).
import acestep.core.generation.handler.init_service_downloads as _dl  # noqa: E402

_dl.check_main_model_exists = lambda *a, **k: True

from acestep.handler import AceStepHandler  # noqa: E402
from acestep.inference import GenerationConfig, GenerationParams, generate_music  # noqa: E402

if DEVICE == "cpu":
    torch.set_num_threads(os.cpu_count() or 2)

HANDLER = AceStepHandler()
_status, _ok = HANDLER.initialize_service(
    project_root=ACE_DIR,
    config_path="acestep-v15-turbo",
    device=DEVICE,
    use_mlx_dit=False,  # MLX is Apple-only; never relevant on a Space
)
if not _ok:
    raise RuntimeError(f"ACE-Step failed to load: {_status}")
print(f"Model ready on {DEVICE} in {time.time() - t0:.0f}s "
      f"(clip={CLIP_SECONDS}s, steps={STEPS})", flush=True)

OUT_DIR = os.path.join(tempfile.gettempdir(), "clips")
os.makedirs(OUT_DIR, exist_ok=True)


def clean_words(words: str) -> str:
    """Keep plain words only: letters, digits, spaces, basic punctuation; <=80 chars."""
    words = re.sub(r"<[^>]*>", " ", words or "")          # drop HTML tags whole
    words = re.sub(r"[^A-Za-z0-9 ,.'-]+", " ", words)
    words = re.sub(r"\s+", " ", words).strip()
    return words[:80].rstrip()


def _generate(style: str, words: str) -> str:
    style = (style or "").strip().lower()
    if style not in STYLES:
        raise gr.Error(f"style must be one of: {', '.join(STYLES)}")
    extra = clean_words(words)
    # The user's words only colour the mood ("rainy morning"); they are
    # never sung, because lyrics are fixed to [Instrumental].
    caption = STYLES[style] + (f", {extra}" if extra else "") + ", instrumental, no vocals"
    params = GenerationParams(
        caption=caption,
        lyrics="[Instrumental]",
        instrumental=True,
        duration=CLIP_SECONDS,
        bpm=BPM[style],
        inference_steps=STEPS,
        thinking=False,          # no LM planner (not loaded)
        use_cot_caption=False,
        use_cot_language=False,
        use_cot_metas=False,
    )
    config = GenerationConfig(batch_size=1, audio_format="wav", use_random_seed=True)
    result = generate_music(HANDLER, None, params, config, save_dir=OUT_DIR)
    if not result.success or not result.audios:
        raise gr.Error(f"generation failed: {getattr(result, 'error', 'unknown')}")
    return result.audios[0]["path"]


# On ZeroGPU, wrap the handler so a GPU is attached only while it runs.
generate = spaces.GPU(duration=ZEROGPU_SECONDS)(_generate) if ON_ZEROGPU else _generate


with gr.Blocks(title="Cafe music clips") as demo:
    gr.Markdown("Short instrumental clips (ACE-Step 1.5 turbo). "
                f"Running on **{'ZeroGPU' if ON_ZEROGPU else DEVICE.upper()}**, "
                f"{CLIP_SECONDS:.0f} s per clip.")
    style_in = gr.Dropdown(list(STYLES), value="lofi", label="style")
    words_in = gr.Textbox(label="words (optional mood, max 80 chars)", max_lines=1)
    btn = gr.Button("Generate")
    audio_out = gr.Audio(label="clip", type="filepath")
    btn.click(generate, [style_in, words_in], audio_out, api_name="generate")

# One job at a time: a second concurrent generation would double RAM on CPU.
demo.queue(default_concurrency_limit=1, max_size=8)

if __name__ == "__main__":
    demo.launch()
