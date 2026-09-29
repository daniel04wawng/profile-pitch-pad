// Tiny generative lo-fi loop so the record player does something.
// Swap for real recordings once they exist.

const CHORDS = [
  [53, 57, 60, 64], // Fmaj7
  [52, 55, 59, 62], // Em7
  [50, 53, 57, 60], // Dm7
  [48, 52, 55, 59], // Cmaj7
];
const SCALE = [60, 62, 64, 67, 69, 72, 74, 76];
const BPM = 72;

const hz = (midi: number) => 440 * Math.pow(2, (midi - 69) / 12);

export class LofiPlayer {
  private ctx: AudioContext | null = null;
  private out: GainNode | null = null;
  private noise: AudioBuffer | null = null;
  private timer: number | null = null;
  private nextTime = 0;
  private step = 0;
  playing = false;

  start() {
    if (this.playing) return;
    if (!this.ctx) this.setup();
    const ctx = this.ctx!;
    ctx.resume();
    this.out!.gain.cancelScheduledValues(ctx.currentTime);
    this.out!.gain.setTargetAtTime(0.5, ctx.currentTime, 0.4);
    this.nextTime = ctx.currentTime + 0.1;
    this.step = 0;
    this.playing = true;
    this.timer = window.setInterval(() => this.schedule(), 25);
  }

  stop() {
    if (!this.playing || !this.ctx) return;
    this.playing = false;
    if (this.timer !== null) window.clearInterval(this.timer);
    this.out!.gain.setTargetAtTime(0, this.ctx.currentTime, 0.3);
  }

  private setup() {
    const ctx = new AudioContext();
    const warm = ctx.createBiquadFilter();
    warm.type = "lowpass";
    warm.frequency.value = 3200;
    const out = ctx.createGain();
    out.gain.value = 0;
    out.connect(warm).connect(ctx.destination);

    const len = ctx.sampleRate;
    const noise = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = noise.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;

    this.ctx = ctx;
    this.out = out;
    this.noise = noise;
  }

  // Eighth-note grid, 8 steps per bar, light swing on the off-beats.
  private schedule() {
    const ctx = this.ctx!;
    const eighth = 60 / BPM / 2;
    while (this.nextTime < ctx.currentTime + 0.15) {
      const s = this.step % 8;
      const bar = Math.floor(this.step / 8);
      const chord = CHORDS[bar % CHORDS.length];
      const t = this.nextTime + (s % 2 === 1 ? eighth * 0.18 : 0);

      if (s === 0) chord.forEach((n) => this.keys(hz(n), t, eighth * 7.5));
      if (s === 0 || s === 5) this.bass(hz(chord[0] - 12), t, eighth * 2.5);
      if (s === 0 || s === 3 || s === 4) this.kick(t, s === 3 ? 0.35 : 0.7);
      if (s === 4) this.snare(t);
      this.hat(t, s % 2 === 0 ? 0.05 : 0.03);
      if (s % 2 === 1 && Math.random() < 0.35) {
        this.lead(hz(SCALE[Math.floor(Math.random() * SCALE.length)]), t, eighth * 1.6);
      }
      if (Math.random() < 0.5) this.crackle(this.nextTime + Math.random() * eighth);

      this.nextTime += eighth;
      this.step++;
    }
  }

  private env(t: number, peak: number, attack: number, dur: number) {
    const g = this.ctx!.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    g.connect(this.out!);
    return g;
  }

  private keys(f: number, t: number, dur: number) {
    const ctx = this.ctx!;
    const lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = 1400;
    lp.connect(this.env(t, 0.05, 0.03, dur));
    for (const detune of [-6, 6]) {
      const o = ctx.createOscillator();
      o.type = "triangle";
      o.frequency.value = f;
      o.detune.value = detune;
      o.connect(lp);
      o.start(t);
      o.stop(t + dur + 0.05);
    }
  }

  private bass(f: number, t: number, dur: number) {
    const o = this.ctx!.createOscillator();
    o.type = "sine";
    o.frequency.value = f;
    o.connect(this.env(t, 0.22, 0.02, dur));
    o.start(t);
    o.stop(t + dur + 0.05);
  }

  private lead(f: number, t: number, dur: number) {
    const o = this.ctx!.createOscillator();
    o.type = "sine";
    o.frequency.value = f;
    o.connect(this.env(t, 0.045, 0.02, dur));
    o.start(t);
    o.stop(t + dur + 0.05);
  }

  private kick(t: number, vel: number) {
    const o = this.ctx!.createOscillator();
    o.frequency.setValueAtTime(120, t);
    o.frequency.exponentialRampToValueAtTime(45, t + 0.12);
    o.connect(this.env(t, 0.5 * vel, 0.005, 0.3));
    o.start(t);
    o.stop(t + 0.35);
  }

  private noiseHit(t: number, type: BiquadFilterType, freq: number, peak: number, dur: number) {
    const src = this.ctx!.createBufferSource();
    src.buffer = this.noise;
    const f = this.ctx!.createBiquadFilter();
    f.type = type;
    f.frequency.value = freq;
    src.connect(f).connect(this.env(t, peak, 0.003, dur));
    src.start(t, Math.random() * 0.5);
    src.stop(t + dur + 0.02);
  }

  private snare(t: number) {
    this.noiseHit(t, "bandpass", 1800, 0.12, 0.18);
  }

  private hat(t: number, peak: number) {
    this.noiseHit(t, "highpass", 7000, peak, 0.04);
  }

  private crackle(t: number) {
    this.noiseHit(t, "highpass", 3000, 0.02 * Math.random(), 0.008);
  }
}
