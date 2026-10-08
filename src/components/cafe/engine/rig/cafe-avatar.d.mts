// Types for cafe-avatar.mjs (the avatar package's runtime, unchanged). The package ships
// cafe-avatar.d.ts; this adds the members the café uses to share one loaded avatar between
// visitors (manifest, sheets, the constructor) and to read the current clip.
export type Action = 'walk-front'|'idle-front'|'sit-down'|'stand-up'|'coffee-sip'|'seated-idle'|'walk-back'|'idle-back'|'sit-down-back'|'stand-up-back'|'coffee-sip-back'|'seated-idle-back';
export type Direction = 'SE'|'SW'|'NE'|'NW';
export type Motion = 'walk'|'idle'|'sit-down'|'stand-up'|'coffee-sip'|'seated-idle';
export type Clip = { sheet: string; durationMs: number[]; loop: boolean; rootMotion?: [number, number][] };
export type Manifest = {
  version: 1;
  character?: string;
  frameSize: [number, number];
  anchor: [number, number];
  defaultAction: Action;
  attachments: Partial<Record<Action, Record<string, [number, number]>>>;
  directions: Record<Direction, { flipX: boolean; actions: Record<Motion, Action> }>;
  animations: Record<Action, Clip>;
};
export class CafeAvatar {
  constructor(manifest: Manifest, sheets: Record<string, HTMLImageElement | HTMLCanvasElement>);
  manifest: Manifest;
  sheets: Record<string, HTMLImageElement | HTMLCanvasElement>;
  direction: Direction;
  action: Action; elapsedMs: number; completed: boolean;
  setDirection(direction: Direction): void;
  play(name: Motion, options?: {restart?: boolean}): boolean;
  setAction(name: Action, options?: {restart?: boolean}): boolean;
  update(dtMs: number): {dx:number;dy:number;justCompleted:boolean};
  draw(ctx: CanvasRenderingContext2D, options:{x:number;y:number;scale?:number;flipX?:boolean;alpha?:number}):void;
  readonly clip: Clip;
  readonly frameIndex:number; readonly durationMs:number;
  readonly attachmentPoints:Record<string, [number,number]>;
}
export function loadCafeAvatar(url:string, options?: {fetchImpl?:typeof fetch;imageFactory?:()=>HTMLImageElement}):Promise<CafeAvatar>;
