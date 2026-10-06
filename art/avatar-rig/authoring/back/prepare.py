from PIL import Image
import numpy as np
from scipy.ndimage import label
from pathlib import Path
p=Path(__file__).parent
def prepare(name,out,height,bottom=254,cx=140):
 im=Image.open(p/name).convert('RGBA');a=np.array(im)
 a[(a[:,:,0]>200)&(a[:,:,1]<95)&(a[:,:,2]<95)]=0
 labels,n=label(a[:,:,3]>100);counts=np.bincount(labels.ravel());counts[0]=0;mask=labels==counts.argmax()
 ys,xs=np.where(mask);box=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
 a[~mask & (a[:,:,3]<200)]=0
 im=Image.fromarray(a).crop(box);scale=height/im.height;im=im.resize((round(im.width*scale),height),Image.Resampling.NEAREST)
 result=Image.new('RGBA',(256,280));result.alpha_composite(im,(round(cx-im.width/2),bottom-height));result.save(p/out)
 print(out,box,result.getbbox(),scale)
prepare('standing-source.png','standing.png',227)

prepare("seated-source.png","seated.png",176)
