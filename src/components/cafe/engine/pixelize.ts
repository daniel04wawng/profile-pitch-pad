// Make a generated picture into a café asset: real pixel art, not a blurry image.
//   1. the plain background goes: everything joined to the picture's edge that's close to the
//      edge's own colour is cleared (a flood fill, so light parts inside the object stay)
//   2. cropped to the object, scaled down to `width` pixels across (averaging, then crisp alpha)
//   3. a small palette (k-means over the object's colours), so it has the flat look of the rest
//   4. a 1px dark warm outline round it, like every sprite in the café

const INK: [number, number, number] = [61, 36, 24]; // #3d2418, the café's outline colour

export async function pixelize(src: string, width = 64, colours = 20): Promise<string> {
  const img = await new Promise<HTMLImageElement>((res, rej) => {
    const im = new Image();
    im.onload = () => res(im);
    im.onerror = () => rej(new Error("couldn't read the picture"));
    im.src = src;
  });
  const W = img.naturalWidth;
  const H = img.naturalHeight;
  const big = document.createElement("canvas");
  big.width = W;
  big.height = H;
  const g = big.getContext("2d", { willReadFrequently: true })!;
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, W, H);
  const P = d.data;

  // 1. background: flood from the edges through pixels close to the edge colour
  let br = 0;
  let bg = 0;
  let bb = 0;
  let n = 0;
  const edge = (x: number, y: number) => {
    const i = (y * W + x) * 4;
    br += P[i];
    bg += P[i + 1];
    bb += P[i + 2];
    n++;
  };
  for (let x = 0; x < W; x++) {
    edge(x, 0);
    edge(x, H - 1);
  }
  for (let y = 0; y < H; y++) {
    edge(0, y);
    edge(W - 1, y);
  }
  br /= n;
  bg /= n;
  bb /= n;
  const near = (i: number) => Math.abs(P[i] - br) + Math.abs(P[i + 1] - bg) + Math.abs(P[i + 2] - bb) < 60;
  const seen = new Uint8Array(W * H);
  const stack: number[] = [];
  for (let x = 0; x < W; x++) stack.push(x, (H - 1) * W + x);
  for (let y = 0; y < H; y++) stack.push(y * W, y * W + W - 1);
  while (stack.length) {
    const p = stack.pop()!;
    if (seen[p] || !near(p * 4)) continue;
    seen[p] = 1;
    P[p * 4 + 3] = 0;
    const x = p % W;
    const y = (p / W) | 0;
    if (x > 0) stack.push(p - 1);
    if (x < W - 1) stack.push(p + 1);
    if (y > 0) stack.push(p - W);
    if (y < H - 1) stack.push(p + W);
  }
  g.putImageData(d, 0, 0);

  // 2. crop and scale down
  let x0 = W;
  let y0 = H;
  let x1 = -1;
  let y1 = -1;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++)
      if (P[(y * W + x) * 4 + 3] > 0) {
        x0 = Math.min(x0, x);
        x1 = Math.max(x1, x);
        y0 = Math.min(y0, y);
        y1 = Math.max(y1, y);
      }
  if (x1 < 0) throw new Error("nothing left after taking the background off");
  const cw = x1 - x0 + 1;
  const ch = y1 - y0 + 1;
  const w = Math.max(8, Math.min(width, cw));
  const h = Math.max(8, Math.round((ch * w) / cw));
  const small = document.createElement("canvas");
  small.width = w + 2; // room for the outline
  small.height = h + 2;
  const s = small.getContext("2d", { willReadFrequently: true })!;
  s.imageSmoothingEnabled = true;
  s.imageSmoothingQuality = "high";
  s.drawImage(big, x0, y0, cw, ch, 1, 1, w, h);
  const out = s.getImageData(0, 0, w + 2, h + 2);
  const Q = out.data;
  for (let i = 0; i < Q.length; i += 4) Q[i + 3] = Q[i + 3] >= 128 ? 255 : 0;

  // 3. a small palette
  const px: [number, number, number][] = [];
  for (let i = 0; i < Q.length; i += 4) if (Q[i + 3]) px.push([Q[i], Q[i + 1], Q[i + 2]]);
  const k = Math.min(colours, px.length);
  const centres = Array.from({ length: k }, (_, j) => [...px[Math.floor((j * px.length) / k)]] as [number, number, number]);
  const nearest = (c: [number, number, number]) => {
    let best = 0;
    let bd = Infinity;
    centres.forEach((m, j) => {
      const dd = (c[0] - m[0]) ** 2 + (c[1] - m[1]) ** 2 + (c[2] - m[2]) ** 2;
      if (dd < bd) {
        bd = dd;
        best = j;
      }
    });
    return best;
  };
  for (let iter = 0; iter < 8; iter++) {
    const sum = centres.map(() => [0, 0, 0, 0]);
    for (const c of px) {
      const j = nearest(c);
      sum[j][0] += c[0];
      sum[j][1] += c[1];
      sum[j][2] += c[2];
      sum[j][3]++;
    }
    sum.forEach((t, j) => {
      if (t[3]) centres[j] = [t[0] / t[3], t[1] / t[3], t[2] / t[3]];
    });
  }
  for (let i = 0; i < Q.length; i += 4) {
    if (!Q[i + 3]) continue;
    const m = centres[nearest([Q[i], Q[i + 1], Q[i + 2]])];
    Q[i] = Math.round(m[0]);
    Q[i + 1] = Math.round(m[1]);
    Q[i + 2] = Math.round(m[2]);
  }

  // 4. the outline
  const OW = w + 2;
  const solid = (x: number, y: number) => x >= 0 && y >= 0 && x < OW && y < h + 2 && Q[(y * OW + x) * 4 + 3] === 255;
  const ring: number[] = [];
  for (let y = 0; y < h + 2; y++)
    for (let x = 0; x < OW; x++) if (!solid(x, y) && (solid(x - 1, y) || solid(x + 1, y) || solid(x, y - 1) || solid(x, y + 1))) ring.push((y * OW + x) * 4);
  for (const i of ring) {
    Q[i] = INK[0];
    Q[i + 1] = INK[1];
    Q[i + 2] = INK[2];
    Q[i + 3] = 255;
  }
  s.putImageData(out, 0, 0);
  return small.toDataURL("image/png");
}
