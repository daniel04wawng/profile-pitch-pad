from PIL import Image
import numpy as np,pathlib
from scipy.interpolate import RBFInterpolator
from scipy.ndimage import map_coordinates
p=pathlib.Path(__file__).parent;stand=Image.open(p/'standing.png');seat=Image.open(p/'seated.png')
A=np.array([[140,28],[121,38],[159,43],[136,68],[148,70],[109,82],[151,83],[104,106],[115,108],[110,127],[111,145],[120,151],[155,94],[165,97],[170,110],[159,128],[151,128],[121,139],[140,150],[155,141],[125,153],[148,153],[120,177],[131,180],[141,194],[155,194],[117,204],[131,205],[143,225],[159,226],[124,217],[152,238],[114,224],[130,232],[141,247],[156,254],[170,236]],float)
B=np.array([[116,79],[94,91],[137,98],[114,121],[124,124],[84,129],[128,148],[81,161],[94,165],[85,175],[94,199],[101,205],[141,132],[146,134],[154,146],[146,183],[131,181],[90,192],[112,209],[134,200],[131,207],[143,201],[129,213],[144,214],[165,187],[178,189],[130,223],[143,226],[169,228],[184,229],[139,231],[175,239],[129,236],[143,246],[169,247],[180,254],[201,237]],float)
edge=np.array([[0,0],[128,0],[255,0],[0,140],[255,140],[0,279],[128,279],[255,279]],float);A=np.vstack([A,edge]);B=np.vstack([B,edge]);y,x=np.mgrid[:280,:256];grid=np.stack([x.ravel(),y.ravel()],axis=1)
def warp(im,points,target):
 a=np.array(im,float)/255;a[:,:,:3]*=a[:,:,3:4];co=RBFInterpolator(target,points,kernel='thin_plate_spline',smoothing=.5)(grid)
 return np.stack([map_coordinates(a[:,:,ch],[co[:,1],co[:,0]],order=1,mode='constant').reshape(280,256) for ch in range(4)],axis=2)
for i in range(8):
 t=i/7;t=t*t*(3-2*t)
 if i==0:im=stand
 elif i==7:im=seat
 else:
  target=A*(1-t)+B*t;a=warp(stand,A,target)*(1-t)+warp(seat,B,target)*t;a[:,:,:3]=np.divide(a[:,:,:3],a[:,:,3:4],out=np.zeros_like(a[:,:,:3]),where=a[:,:,3:4]>1e-6);a[:,:,3]=(a[:,:,3]>.5);a[a[:,:,3]==0]=0;im=Image.fromarray(np.uint8(np.clip(a,0,1)*255))
 im.save(p/f'sit-down-back-{i+1}.png');im.save(p/f'stand-up-back-{8-i}.png')
review=Image.new('RGBA',(2048,280),(238,230,215,255))
for i in range(8):review.alpha_composite(Image.open(p/f'sit-down-back-{i+1}.png'),(256*i,0))
review.save(p/'transition-review.png')
