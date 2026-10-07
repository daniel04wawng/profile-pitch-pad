import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import fs from "fs";

// Every sprite a café can use (companion layers like window sky masks and sun patches, and
// the editor's blank new-asset canvas, aren't assets of their own).
function listSprites() {
  return fs
    .readdirSync(path.resolve(__dirname, "public/cafe/sprites"))
    .filter((f) => f.endsWith(".png") && !/\.(sky|light)\.png$/.test(f) && f !== "new-asset.png")
    .sort()
    .map((f) => `sprites/${f}`);
}

// Lets the café editor (/cafe?edit) save its layout and pixel edits straight to disk.
// Dev server only, and only from this machine: the server listens on the whole network.
function cafeEditorSaver(): Plugin {
  const root = path.resolve(__dirname, "public/cafe");
  const local = ["127.0.0.1", "::1", "::ffff:127.0.0.1"];

  const handle =
    (write: (body: string) => void) =>
    (req: import("http").IncomingMessage, res: import("http").ServerResponse) => {
      if (req.method !== "POST" || !local.includes(req.socket.remoteAddress ?? "")) {
        res.statusCode = 403;
        res.end();
        return;
      }
      let body = "";
      req.on("data", (chunk) => {
        body += chunk;
        if (body.length > 8_000_000) req.destroy();
      });
      req.on("end", () => {
        try {
          write(body);
          res.statusCode = 204;
        } catch (e) {
          res.statusCode = 400;
          res.write(String(e));
        }
        res.end();
      });
    };

  return {
    name: "cafe-editor-saver",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use(
        "/__cafe/layout",
        handle((body) => {
          const layout = JSON.parse(body);
          if (!Array.isArray(layout.assets)) throw new Error("layout.assets missing");
          fs.writeFileSync(path.join(root, "layout.json"), JSON.stringify(layout, null, 2) + "\n");
        }),
      );
      server.middlewares.use(
        "/__cafe/screens",
        handle((body) => {
          const data = JSON.parse(body);
          if (typeof data.screens !== "object" || Array.isArray(data.screens)) throw new Error("screens missing");
          fs.writeFileSync(path.join(root, "screens.json"), JSON.stringify(data, null, 2) + "\n");
        }),
      );
      // An asset's collision (set in the editor), kept with the asset in _companions.json under
      // its own key, so re-running the art scripts (which write foot/size) never undoes it.
      server.middlewares.use(
        "/__cafe/collision",
        handle((body) => {
          const { name, collision } = JSON.parse(body);
          if (typeof name !== "string" || !/^[a-z0-9_-]+$/i.test(name)) throw new Error("bad name");
          const n = (v: unknown) => typeof v === "number" && Number.isFinite(v) && Math.abs(v) < 4096;
          if (collision !== null) {
            const c = collision;
            if (!c || !n(c.foot?.x) || !n(c.foot?.y) || !n(c.size?.a) || !n(c.size?.b) || !["front", "back", "centre"].includes(c.size?.from)) throw new Error("bad collision");
          }
          const file = path.join(root, "sprites", "_companions.json");
          const all = JSON.parse(fs.readFileSync(file, "utf8"));
          all[name] = { ...all[name] };
          if (collision === null) delete all[name].collision;
          else
            all[name].collision = {
              foot: { x: collision.foot.x, y: collision.foot.y },
              size: { a: collision.size.a, b: collision.size.b, from: collision.size.from },
              ...(collision.walkable ? { walkable: true } : {}),
            };
          fs.writeFileSync(file, JSON.stringify(all, null, 1)); // as the art scripts write it
        }),
      );
      // Photos and videos for the screens (bakes, project demos): the raw file as the body,
      // saved to public/cafe/media/<name>. Loopback only, like the rest.
      server.middlewares.use("/__cafe/media", (req, res) => {
        const fail = (code: number, msg: string) => {
          res.statusCode = code;
          res.end(msg);
        };
        if (req.method !== "POST" || !local.includes(req.socket.remoteAddress ?? "")) return fail(403, "");
        const file = new URL(req.url ?? "", "http://x").searchParams.get("file") ?? "";
        if (!/^media\/[a-z0-9-]+\.(jpg|jpeg|png|webp|gif|mp4|webm)$/i.test(file)) return fail(400, "bad file name");
        const chunks: Buffer[] = [];
        let size = 0;
        req.on("data", (c: Buffer) => {
          size += c.length;
          if (size > 80_000_000) {
            fail(413, "too big (80 MB max)");
            req.destroy();
          } else chunks.push(c);
        });
        req.on("end", () => {
          if (res.writableEnded) return;
          fs.mkdirSync(path.join(root, "media"), { recursive: true });
          fs.writeFileSync(path.join(root, file), Buffer.concat(chunks));
          res.statusCode = 204;
          res.end();
        });
      });
      // Asset library: every PNG in public/cafe/sprites.
      server.middlewares.use("/__cafe/assets", (req, res) => {
        if (req.method !== "GET" || !local.includes(req.socket.remoteAddress ?? "")) {
          res.statusCode = 403;
          res.end();
          return;
        }
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(listSprites()));
      });
      // what a build writes as cafe/assets.json (the library for visitors building their own café)
      server.middlewares.use("/cafe/assets.json", (req, res) => {
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify(listSprites()));
      });
      server.middlewares.use(
        "/__cafe/image",
        handle((body) => {
          const { file, data } = JSON.parse(body);
          const prefix = "data:image/png;base64,";
          // PNGs inside public/cafe only; no way to climb out of it.
          if (typeof file !== "string" || !/^[a-z0-9_\-/]+\.png$/i.test(file) || file.includes("..")) throw new Error("bad file");
          if (typeof data !== "string" || !data.startsWith(prefix)) throw new Error("bad data");
          const target = path.resolve(root, file);
          if (!target.startsWith(root + path.sep)) throw new Error("outside public/cafe");
          fs.writeFileSync(target, Buffer.from(data.slice(prefix.length), "base64"));
        }),
      );
    },
  };
}

// Production builds list every sprite in cafe/assets.json: the library for visitors building
// their own café (the dev server answers /__cafe/assets instead).
function cafeAssetIndex(): Plugin {
  return {
    name: "cafe-asset-index",
    apply: "build",
    generateBundle() {
      this.emitFile({ type: "asset", fileName: "cafe/assets.json", source: JSON.stringify(listSprites()) });
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [react(), cafeEditorSaver(), cafeAssetIndex()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
