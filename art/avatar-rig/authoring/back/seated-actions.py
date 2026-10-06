from PIL import Image,ImageDraw
import numpy as np,math,pathlib
p=pathlib.Path(__file__).parent
# The clean plate shares the original image framing, so use the same crop and scale.
raw=Image.open(p/'seated-plate-source.png').convert('RGBA');a=np.array(raw);a[(a[:,:,0]>200)&(a[:,:,1]<95)&(a[:,:,2]<95)]=0
plate=Image.fromarray(a).crop((331,114,1046,1115));plate=plate.resize((126,176),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(256,280));canvas.alpha_composite(plate,(77,78));plate=canvas
source=Image.open(p/'seated.png');a=np.array(source)
def maskpoly(points):
 m=Image.new('L',source.size);ImageDraw.Draw(m).polygon(points,fill=255);return np.array(m)>0
uppermask=maskpoly([(125,146),(135,145),(148,161),(153,179),(148,189),(132,191),(122,175)])
foremask=maskpoly([(137,131),(148,131),(156,137),(157,148),(152,159),(149,174),(141,183),(137,170),(141,150),(137,146)])
upper=a.copy();upper[~uppermask]=0;fore=a.copy();fore[~foremask]=0
# Replace only the region underneath moving arm; retain every other original pixel.
body=a.copy();bm=uppermask|foremask;body[bm]=np.array(plate)[bm]
S=np.array([127.,151.]);E=np.array([145.,180.])
def rot(v,angle):
 c=math.cos(angle);s=math.sin(angle);return np.array([[c,-s],[s,c]])@v
def rigid(arr,origin,target,angle):
 c=math.cos(angle);s=math.sin(angle);ox,oy=origin;tx,ty=target
 return Image.fromarray(arr).transform(source.size,Image.Transform.AFFINE,(c,s,ox-c*tx-s*ty,-s,c,oy+s*tx-c*ty),Image.Resampling.NEAREST)
for i,amount in enumerate([0,.25,.65,1,1,.65,.25,0]):
 if amount==0:frame=source.copy()
 else:
  ua=-.45*amount;fa=-.6*amount;En=S+rot(E-S,ua);frame=Image.fromarray(body);frame.alpha_composite(rigid(upper,S,S,ua));frame.alpha_composite(rigid(fore,E,En,fa))
 frame.save(p/f'coffee-sip-back-{i+1}.png')
for i,shift in enumerate([0,0,1,2,3,2,1,0]):
 out=a.copy()
 for y in range(78,209):
  delta=round(shift*max(0,min(1,(209-y)/35)));out[y]=a[y+delta]
 Image.fromarray(out).save(p/f'seated-idle-back-{i+1}.png')
review=Image.new('RGBA',(2048,280),(238,230,215,255))
for i in range(8):review.alpha_composite(Image.open(p/f'coffee-sip-back-{i+1}.png'),(256*i,0))
review.save(p/'sip-review.png')
