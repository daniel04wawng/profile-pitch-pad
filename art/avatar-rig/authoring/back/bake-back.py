from PIL import Image,ImageDraw
import numpy as np, math,json,pathlib
p=pathlib.Path(__file__).parent
cfg={'frameSize':[256,280],'source':'standing.png','cameraDegrees':35,'facingVector':[.70710678,-.40557979],'hipSwingRadians':.30,'kneeFlexRadians':.45,'bodyHeight':78,'bodySway':1.5,'near':{'hip':[147,150],'knee':[149,196],'ankle':[151,239]},'far':{'hip':[126,149],'knee':[125,182],'ankle':[124,219]},'freeArm':{'pivot':[109,108],'swingRadians':.12},'layers':{'boundaryX':137,'legTop':143,'nearShoeTop':238,'farShoeTop':218,'armPolygon':[[104,107],[117,108],[117,131],[121,148],[111,150],[105,132]]}}
config=p/'back.rig.json'
if config.exists():cfg=json.loads(config.read_text())
else:config.write_text(json.dumps(cfg,indent=2))
im=Image.open(p/cfg['source']).convert('RGBA');a=np.array(im);yy,xx=np.mgrid[:280,:256];layers=cfg['layers']
def poly(points):
 m=Image.new('L',im.size);ImageDraw.Draw(m).polygon(points,fill=255);return np.array(m)>0
armmask=poly(layers['armPolygon'])&(a[:,:,3]>0)
# Exact shared assignment covers trousers, cuff, socks and shoes without duplication.
regions=[(yy>=layers['legTop'])&(xx>=layers['boundaryX']),(yy>=layers['legTop'])&(xx<layers['boundaryX'])]
body=a.copy();legs=[];feet=[]
gray=(np.max(a[:,:,:3],axis=2)-np.min(a[:,:,:3],axis=2)<40)&(np.max(a[:,:,:3],axis=2)<160)
from scipy.ndimage import binary_dilation
white=(np.min(a[:,:,:3],axis=2)>165)&(a[:,:,3]>0)
footmasks=[binary_dilation(white&(yy>=230)&(xx>=140),iterations=1)|((yy>=237)&(xx>=140)&(xx<=157)),binary_dilation(white&(yy>=208)&(yy<=235)&(xx<142),iterations=1)|((yy>=217)&(yy<=224)&(xx>=116)&(xx<=130))]
allfeet=footmasks[0]|footmasks[1]
for idx,reg in enumerate(regions):
 shoeY=layers['nearShoeTop'] if idx==0 else layers['farShoeTop']
 legmask=reg&gray&~armmask&~allfeet
 footmask=footmasks[idx]&~armmask
 leg=a.copy();leg[~legmask | (yy>=shoeY)]=0
 foot=a.copy();foot[~footmask]=0
 legs.append(leg);feet.append(foot);body[legmask|footmask]=0
body[yy>=155]=0
arm=a.copy();arm[~armmask]=0;body[armmask&(yy>=116)]=0
# Keep top shoulder sleeve overlap on torso.
def rigid(arr,origin,target,angle=0):
 c=math.cos(angle);s=math.sin(angle);ox,oy=origin;tx,ty=target
 return Image.fromarray(arr).transform(im.size,Image.Transform.AFFINE,(c,s,ox-c*tx-s*ty,-s,c,oy+s*tx-c*ty),Image.Resampling.NEAREST)
def segment(arr,origin,rest,target,posed):
 length=np.linalg.norm(rest);u=rest/length;n=np.array([-u[1],u[0]]);U=posed/np.linalg.norm(posed);N=np.array([-U[1],U[0]])
 inv=np.linalg.inv(np.outer(posed/length,u)+np.outer(N,n));off=origin-inv@target
 return Image.fromarray(arr).transform(im.size,Image.Transform.AFFINE,(*inv[0],off[0],*inv[1],off[1]),Image.Resampling.NEAREST)
fwd=np.array(cfg['facingVector']);vertical=math.cos(math.radians(cfg['cameraDegrees']))
for i in range(8):
 phase=i/8;bob=cfg['bodyHeight']*(1-math.cos(cfg['hipSwingRadians']*math.cos(2*math.pi*phase)));sway=cfg['bodySway']*math.sin(2*math.pi*phase);frame=Image.new('RGBA',im.size)
 for idx,name in [(1,'far'),(0,'near')]:
  H,K,A=[np.array(cfg[name][n],float) for n in ['hip','knee','ankle']];f=(phase+.5*idx)%1;angle=cfg['hipSwingRadians']*math.cos(2*math.pi*f);flex=cfg['kneeFlexRadians']*math.sin(math.pi*(f-.5)*2) if f>.5 else 0
  Hn=H+[sway,bob];up=(K-H)*math.cos(angle)+fwd*np.linalg.norm(K-H)/vertical*math.sin(angle);low=(A-K)*math.cos(angle-flex)+fwd*np.linalg.norm(A-K)/vertical*math.sin(angle-flex);Kn=Hn+up;An=Kn+low
  upper=legs[idx].copy();upper[yy>K[1]+5]=0;lower=legs[idx].copy();lower[yy<K[1]-5]=0
  frame.alpha_composite(segment(upper,H,K-H,Hn,up));frame.alpha_composite(segment(lower,K,A-K,Kn,low));frame.alpha_composite(rigid(feet[idx],A,An,-.08*math.sin(math.pi*max(0,(f-.5)*2)) if f>=.5 else 0))
 frame.alpha_composite(rigid(body,[0,0],[sway,bob]));frame.alpha_composite(rigid(arm,cfg['freeArm']['pivot'],np.array(cfg['freeArm']['pivot'])+[sway,bob],cfg['freeArm']['swingRadians']*math.cos(2*math.pi*phase)))
 frame.save(p/f'walk-back-{i+1}.png')
# Subtle upper body breath with lower body grounded.
for i,shift in enumerate([0,0,1,2,3,2,1,0]):
 out=a.copy()
 for y in range(27,160):
  delta=round(shift*max(0,min(1,(160-y)/35)))
  out[y]=a[min(y+delta,279)]
 Image.fromarray(out).save(p/f'idle-back-{i+1}.png')
review=Image.new('RGBA',(256*8,300),(238,230,215,255))
for i in range(8):review.alpha_composite(Image.open(p/f'walk-back-{i+1}.png'),(i*256,0))
review.save(p/'walk-review.png')
