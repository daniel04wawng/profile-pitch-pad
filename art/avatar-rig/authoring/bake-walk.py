from PIL import Image,ImageDraw
import numpy as np,math,pathlib,json,argparse
ap=argparse.ArgumentParser();ap.add_argument('--rig',default=str(pathlib.Path(__file__).with_name('green.rig.json')));ap.add_argument('--out',required=True);args=ap.parse_args()
rigpath=pathlib.Path(args.rig);cfg=json.loads(rigpath.read_text());layers=cfg['layers'];p=pathlib.Path(args.out);p.mkdir(parents=True,exist_ok=True)
im=Image.open(rigpath.parent/cfg['source']).convert('RGBA');assert list(im.size)==cfg['frameSize'], 'Source image must match rig frameSize'
a=np.array(im);yy,xx=np.mgrid[:im.height,:im.width]
near=tuple(np.array(cfg['near'][n],float) for n in ['hip','knee','ankle']);far=tuple(np.array(cfg['far'][n],float) for n in ['hip','knee','ankle'])
from scipy.ndimage import binary_dilation
# Assign every lower-body pixel to a moving layer; no trouser remnants stay on torso.
boundary=np.where(yy>=layers['calfBoundaryY'],layers['calfBoundaryX'],layers['legBoundaryX'])
near_region=(yy>=layers['nearLegTop'])&(xx<boundary);far_region=(yy>=layers['farLegTop'])&(xx>=boundary)
legs=[];feet=[];body=a.copy()
footpolys=layers['footPolygons']
for idx,region in enumerate([near_region,far_region]):
 gray=(np.max(a[:,:,:3],axis=2)-np.min(a[:,:,:3],axis=2)<layers['graySaturation'])&(np.max(a[:,:,:3],axis=2)<layers['grayMax'])
 ar=a.copy();ar[~(region & gray)]=0;legs.append(ar)
 body[region & (yy>=layers['torsoOverlapY'])]=0
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(footpolys[idx],fill=255);fm=np.array(mask)>0
 # Feet are clipped by the leg assignment, preventing neighboring shoe fragments.
 fm &= (xx<134 if idx==0 else xx>=134) | (yy>237 if idx==0 else yy>219)
 fm &= yy>=(layers['nearShoeTop'] if idx==0 else layers['farShoeTop'])
 ar=a.copy();ar[~fm]=0;feet.append(Image.fromarray(ar));body[fm & (yy>218 if idx==0 else yy>207)]=0
skin=(a[:,:,0]>160)&(a[:,:,0]>a[:,:,1]*1.12)&(a[:,:,1]>70)&(a[:,:,2]<190)&(xx>=150)&(yy>=126)&(yy<=177)&(a[:,:,3]>0)
am=binary_dilation(skin,iterations=2)
sleeve=Image.new('L',im.size);ImageDraw.Draw(sleeve).polygon([(150,114),(163,114),(164,133),(151,134)],fill=255);am|=np.array(sleeve)>0
for leg in legs:leg[am]=0
arm=a.copy();arm[~am]=0
# Keep a shoulder overlap on the body; erase the full moving forearm and hand.
body[am & (yy>126)]=0;arm=Image.fromarray(arm)
def rigid(arr,origin,target,angle):
 c=math.cos(angle);sn=math.sin(angle)
 co=(c,sn,origin[0]-c*target[0]-sn*target[1],-sn,c,origin[1]+sn*target[0]-c*target[1])
 return Image.fromarray(arr).transform(im.size,Image.Transform.AFFINE,co,Image.Resampling.NEAREST)
def projected_segment(arr,origin,rest,target,posed):
 length=np.linalg.norm(rest);u=rest/length;n=np.array([-u[1],u[0]])
 U=posed/np.linalg.norm(posed);N=np.array([-U[1],U[0]])
 matrix=np.outer(posed/length,u)+np.outer(N,n)
 inv=np.linalg.inv(matrix);off=origin-inv@target
 co=(inv[0,0],inv[0,1],off[0],inv[1,0],inv[1,1],off[1])
 return Image.fromarray(arr).transform(im.size,Image.Transform.AFFINE,co,Image.Resampling.NEAREST)
fwd=np.array([math.sqrt(.5),math.sqrt(.5)*math.sin(math.radians(cfg['cameraDegrees']))]);vertical=math.cos(math.radians(cfg['cameraDegrees']))
for i in range(8):
 phase=i/8;bob=cfg['bodyHeight']*(1-math.cos(cfg['hipSwingRadians']*math.cos(2*math.pi*phase)));sway=cfg['bodySway']*math.sin(2*math.pi*phase);frame=Image.new('RGBA',im.size)
 # A rigid torso shifts over the support leg, while the cup moves with the body.
 frame.alpha_composite(rigid(body,[0,0],[sway,bob],0))
 frame.alpha_composite(rigid(np.array(arm),cfg['freeArm']['pivot'],np.array(cfg['freeArm']['pivot'])+[sway,bob],cfg['freeArm']['swingRadians']*math.cos(2*math.pi*phase)))
 for idx,(H,K,A) in [(1,far),(0,near)]:
  f=(phase+.5*idx)%1
  angle=cfg['hipSwingRadians']*math.cos(2*math.pi*f)
  flex=cfg['kneeFlexRadians']*math.sin(math.pi*(f-.5)*2) if f>.5 else 0
  shin_angle=angle-flex
  Hn=H+[sway,bob]
  upper_rest=K-H;lower_rest=A-K
  upper_pose=upper_rest*math.cos(angle)+fwd*(np.linalg.norm(upper_rest)/vertical)*math.sin(angle)
  lower_pose=lower_rest*math.cos(shin_angle)+fwd*(np.linalg.norm(lower_rest)/vertical)*math.sin(shin_angle)
  Kn=Hn+upper_pose;An=Kn+lower_pose
  upper=legs[idx].copy();upper[yy>K[1]+layers['kneeOverlap']]=0
  lower=legs[idx].copy();lower[yy<K[1]-layers['kneeOverlap']]=0;lower[yy>(layers['nearShinBottom'] if idx==0 else layers['farShinBottom'])]=0
  frame.alpha_composite(projected_segment(upper,H,K-H,Hn,upper_pose));frame.alpha_composite(projected_segment(lower,K,A-K,Kn,lower_pose))
  # Rigid shoe pivots at the ankle; it never bends with the shin texture.
  tilt=-.10*math.sin(math.pi*max(0,(f-.5)*2)) if f>=.5 else 0
  frame.alpha_composite(rigid(np.array(feet[idx]),A,An,tilt))
 frame.save(p/f'walk-front-{i+1}.png')
