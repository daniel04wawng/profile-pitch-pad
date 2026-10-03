// A piece's footprint read from its own pixels, for pieces that don't come with a size (cut
// art, things you draw or import). An isometric piece's outline gives it away: the lowest
// pixel is its front floor corner, and its leftmost and rightmost columns show how far it runs
// along each floor axis.

export type Measure = { fx: number; fy: number; lx: number; rx: number; w: number; h: number };

const cache = new Map<string, Promise<Measure | null>>();

export function measureSprite(src: string): Promise<Measure | null> {
  let p = cache.get(src);
  if (!p) {
    p = new Promise((res) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.width;
        c.height = img.height;
        const ctx = c.getContext("2d")!;
        ctx.drawImage(img, 0, 0);
        const d = ctx.getImageData(0, 0, img.width, img.height).data;
        const low = new Int32Array(img.width).fill(-1); // lowest solid pixel in each column
        for (let x = 0; x < img.width; x++)
          for (let y = img.height - 1; y >= 0; y--)
            if (d[(y * img.width + x) * 4 + 3] > 8) {
              low[x] = y;
              break;
            }
        const cols = [...low.keys()].filter((x) => low[x] >= 0);
        if (!cols.length) return res(null);
        const fy = Math.max(...cols.map((x) => low[x]));
        const front = cols.filter((x) => low[x] === fy);
        res({ fx: front.reduce((a, b) => a + b, 0) / front.length, fy, lx: cols[0], rx: cols[cols.length - 1], w: img.width, h: img.height });
      };
      img.onerror = () => res(null);
      img.src = src;
    });
    cache.set(src, p);
  }
  return p;
}
