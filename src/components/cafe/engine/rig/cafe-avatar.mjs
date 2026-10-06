const finite = (value, name) => { if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite`); };
export async function loadCafeAvatar(manifestUrl, { fetchImpl = globalThis.fetch, imageFactory = () => new Image() } = {}) {
  const response = await fetchImpl(manifestUrl);
  if (!response.ok) throw new Error(`Avatar manifest request failed: ${response.status}`);
  const manifest = await response.json();
  if (manifest.version !== 1) throw new Error('Unsupported avatar format');
  const base = new URL(manifestUrl, globalThis.location?.href || 'http://localhost/');
  const sheets = {};
  for (const [name, clip] of Object.entries(manifest.animations)) {
    if (!clip.durationMs.length || clip.durationMs.some(d => !Number.isFinite(d) || d <= 0)) throw new Error(`Invalid timing: ${name}`);
    const image = imageFactory();
    await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = () => reject(new Error(`Failed to load ${name} sprite sheet`)); image.src = new URL(clip.sheet, base).href; });
    if (image.naturalWidth !== manifest.frameSize[0] * clip.durationMs.length || image.naturalHeight !== manifest.frameSize[1]) throw new Error(`Wrong sheet dimensions: ${name}`);
    sheets[name] = image;
  }
  return new CafeAvatar(manifest, sheets);
}
export class CafeAvatar {
  constructor(manifest, sheets) {
    this.manifest = manifest; this.sheets = sheets; this.action = manifest.defaultAction;
    this.elapsedMs = 0; this.completed = false; this.direction = "SE";
    if (!manifest.animations[this.action]) throw new Error('Missing default action');
  }
  setAction(name, { restart = false } = {}) {
    if (!this.manifest.animations[name]) throw new Error(`Unknown action: ${name}`);
    if (name === this.action && !restart) return false;
    const views = this.manifest.directions;
    if (views && !Object.values(views[this.direction].actions).includes(name)) {
      const mirrored = views[this.direction].flipX;
      const match = Object.entries(views).find(([,view]) => view.flipX === mirrored && Object.values(view.actions).includes(name));
      if (match) this.direction = match[0];
    }
    this.action = name; this.elapsedMs = 0; this.completed = false; return true;
  }
  setDirection(direction) {
    const views = this.manifest.directions;
    if (!views?.[direction]) throw new Error(`Unsupported direction: ${direction}`);
    const before = views[this.direction];
    const next = views[direction];
    const entry = Object.entries(before.actions).find(([, name]) => name === this.action);
    if (!entry) throw new Error(`Action has no direction mapping: ${this.action}`);
    const elapsed = this.elapsedMs, completed = this.completed;
    this.setAction(next.actions[entry[0]]);
    this.elapsedMs = elapsed; this.completed = completed; this.direction = direction;
  }
  play(name, { restart = false } = {}) {
    const action = this.manifest.directions?.[this.direction]?.actions[name];
    if (!action) throw new Error(`Unknown directional action: ${name}`);
    return this.setAction(action, { restart });
  }
  get clip() { return this.manifest.animations[this.action]; }
  get durationMs() { return this.clip.durationMs.reduce((sum, n) => sum + n, 0); }
  get frameIndex() {
    const total = this.durationMs; let time = this.clip.loop ? this.elapsedMs % total : Math.min(this.elapsedMs, total - 1e-6);
    for (let i = 0; i < this.clip.durationMs.length; i++) { if (time < this.clip.durationMs[i]) return i; time -= this.clip.durationMs[i]; }
    return this.clip.durationMs.length - 1;
  }
  motionAt(time) {
    const curve = this.clip.rootMotion;
    if (!curve) return { x: 0, y: 0 };
    const duration = this.durationMs;
    const cycles = this.clip.loop ? Math.floor(time / duration) : 0;
    const phase = this.clip.loop ? (time % duration) / duration : Math.min(time / duration, 1);
    const last = curve[curve.length - 1], sample = phase * (curve.length - 1);
    const i = Math.min(Math.floor(sample), curve.length - 2), f = sample - i;
    return { x: cycles * last[0] + curve[i][0] * (1 - f) + curve[i + 1][0] * f,
      y: cycles * last[1] + curve[i][1] * (1 - f) + curve[i + 1][1] * f };
  }
  update(dtMs) {
    finite(dtMs, 'dtMs'); if (dtMs < 0) throw new RangeError('dtMs must be nonnegative');
    const before = this.motionAt(this.elapsedMs);
    const wasCompleted = this.completed;
    this.elapsedMs = this.clip.loop ? this.elapsedMs + dtMs : Math.min(this.elapsedMs + dtMs, this.durationMs);
    this.completed = !this.clip.loop && this.elapsedMs >= this.durationMs;
    const after = this.motionAt(this.elapsedMs);
    return { dx: (after.x - before.x) * (this.manifest.directions?.[this.direction]?.flipX ? -1 : 1), dy: after.y - before.y, justCompleted: this.completed && !wasCompleted };
  }
  draw(ctx, { x, y, scale = 1, flipX = this.manifest.directions?.[this.direction]?.flipX || false, alpha = 1 } = {}) {
    finite(x, 'x'); finite(y, 'y'); finite(scale, 'scale'); if (scale <= 0) throw new RangeError('scale must be positive');
    const [w, h] = this.manifest.frameSize, [ax, ay] = this.manifest.anchor;
    ctx.save(); ctx.imageSmoothingEnabled = false; ctx.globalAlpha *= alpha;
    ctx.translate(x, y); ctx.scale(flipX ? -scale : scale, scale);
    ctx.drawImage(this.sheets[this.action], this.frameIndex * w, 0, w, h, -ax, -ay, w, h);
    ctx.restore();
  }
  get attachmentPoints() {
    const points = this.manifest.attachments[this.action] || {};
    if (!this.manifest.directions?.[this.direction]?.flipX) return points;
    return Object.fromEntries(Object.entries(points).map(([key, [x,y]]) => [key, [2*this.manifest.anchor[0]-x,y]]));
  }
}
