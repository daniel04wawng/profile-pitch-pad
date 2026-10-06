export type Action = 'walk-front'|'idle-front'|'sit-down'|'stand-up'|'coffee-sip'|'seated-idle'|'walk-back'|'idle-back'|'sit-down-back'|'stand-up-back'|'coffee-sip-back'|'seated-idle-back';
export type Direction = 'SE'|'SW'|'NE'|'NW';
export type Motion = 'walk'|'idle'|'sit-down'|'stand-up'|'coffee-sip'|'seated-idle';
export class CafeAvatar {
  direction: Direction;
  setDirection(direction: Direction): void;
  play(name: Motion, options?: {restart?: boolean}): boolean;
  action: Action; elapsedMs: number; completed: boolean;
  setAction(name: Action, options?: {restart?: boolean}): boolean;
  update(dtMs: number): {dx:number;dy:number;justCompleted:boolean};
  draw(ctx: CanvasRenderingContext2D, options:{x:number;y:number;scale?:number;flipX?:boolean;alpha?:number}):void;
  readonly frameIndex:number; readonly durationMs:number;
  readonly attachmentPoints:Record<string, [number,number]>;
}
export function loadCafeAvatar(url:string, options?: {fetchImpl?:typeof fetch;imageFactory?:()=>HTMLImageElement}):Promise<CafeAvatar>;
