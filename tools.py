'''
Created on 27 Aug 2016

@author: Kieran Finn
'''
import numpy as np
import sys
import pickle
import os
from imageio import imread

def overprint(s):
    sys.stdout.write('\r')
    sys.stdout.flush()
    sys.stdout.write(s)

def pload(fname):
    f=open(fname,'rb')
    try:
        out=pickle.load(f)
    except:
        f.close()
        f=open(fname,'r')
        out=pickle.load(f)
    f.close()
    return out

def pdump(obj,fname):
    f=open(fname,'wb')
    pickle.dump(obj,f)
    f.close()
    
def add_comma(number): #makes a large number more readable by adding a comma every three digits
    out=''
    i=1
    number=str(number)
    while i<=len(number):
        out=number[-i]+out
        if i%3==0 and i!=len(number):
            out=','+out
        i+=1
    return out
    

def progress_bar(current,total):
    screen_length=80.0
    middle=int(screen_length/2)
    timestr=' %s/%s ' %(add_comma(current+1),add_comma(total))
    timelen=len(timestr)
    start=int(middle-timelen/2)
    end=int(start+timelen)
    n=int(screen_length*float(current)/total)
    if n<=start:
        out='#'*n+' '*(start-n)+timestr
    elif n<=end:
        out='#'*start+timestr
    else:
        out='#'*start+timestr+'#'*(n-end)
    overprint(out)

def rgb2hex(rgb):
    return '#%02x%02x%02x' %tuple(rgb)

def rgb2int(rgb):
    return int(rgb2hex(rgb)[1:],16)

def get_average_colour(fname):
    image=imread(fname)
    avg=np.sum(np.sum(image,axis=0),axis=0)/(image.shape[0]*image.shape[1])
    return rgb2int(avg)

def binsearch(x,dbase):
    l=-1
    r=len(dbase)
    while r-l>1:
        i=(r+l)/2
        if dbase[i][1]>x:
            r=i
        else:
            l=i
    return r

def make_dbase(dirname):
    print('making database for %s' %dirname)
    pnames=os.listdir(dirname)
    N=len(pnames)
    out=[]
    for i in range(N):
        progress_bar(i,N)
        fname=dirname+'/'+pnames[i]
        avg=get_average_colour(fname)
        r=binsearch(avg,out)
        out.insert(r,(fname,avg))
    print('\n')
    return out


def compare_photos(im_1,im_2,smoothing=20):#smoothing provides additional smoothing so we don't need to compare pixel by pixel
    out=0
    ims=[im_1,im_2]
    x_pix=[len(ims[i]) for i in range(2)]
    y_pix=[len(ims[i][0]) for i in range(2)]
    if x_pix[0]>x_pix[1]:#allows either image to be the larger one
        large=0
        small=1
    else:
        large=1
        small=0
    x_smooth=float(x_pix[large])/float(x_pix[small])
    y_smooth=float(y_pix[large])/float(y_pix[small])
    Nx=x_pix[small]/smoothing
    Ny=y_pix[small]/smoothing
    for i in range(Nx):
        for j in range(Ny):
            p1=ims[small][int(i*smoothing):int((i+1)*smoothing),int(j*smoothing):int((j+1)*smoothing)]
            p2=ims[large][int(i*x_smooth*smoothing):int((i+1)*x_smooth*smoothing),int(j*y_smooth*smoothing):int((j+1)*y_smooth*smoothing)]
            out+=np.sum((np.average(p1,axis=(0,1))-np.average(p2,axis=(0,1)))**2)
    return out/(Nx*Ny)


def find_match(frame,dbase):
    pnames=os.listdir(dbase)
    best_match=''
    winning_score=np.inf
    N=len(pnames)
    for i in range(N):
        progress_bar(i,N)
        score=compare_photos(frame,imread(dbase+'/'+pnames[i]))
        if score<winning_score:
            winning_score=score
            best_match=pnames[i]
    return best_match
    
    
    
def reduce_resolution_by(image,n):
    Nx=len(image)/n
    Ny=len(image[0])/n
    out=[]
    for i in range(Nx):
        out.append([])
        for j in range(Ny):
            out[i].append(np.average(image[i*n:(i+1)*n,j*n:(j+1)*n],axis=(0,1)))
    return np.array(out)
     
      
def cheating(image,Nx,Ny):
    nx=len(image)/Nx
    ny=len(image[0])/Ny
    n=min([nx,ny])
    return image[::n,::n][:Nx,:Ny]
    
def reduce_resolution_to(image,Nx,Ny):
    nx=len(image)/Nx
    ny=len(image[0])/Ny
    n=min([nx,ny])
    if n**2>Nx*Ny:
        return rrt_pixel(image,Nx,Ny)
    else:
        return rrt_ave(image,Nx,Ny)
      
  
def rrt_pixel(image,Nx,Ny):
    nx=int(len(image)/Nx)
    ny=int(len(image[0])/Ny)
    n=min([nx,ny])
    x_offset=int((len(image)-Nx*n)/2)
    y_offset=int((len(image[0])-Ny*n)/2)
    out=[]
    for i in range(Nx):
        out.append([])
        for j in range(Ny):
            out[i].append(np.average(image[x_offset+i*n:x_offset+(i+1)*n,y_offset+j*n:y_offset+(j+1)*n],axis=(0,1)))
    return np.array(out)
  
    
def rrt_ave(image,Nx,Ny):
    nx=int(len(image)/Nx)
    ny=int(len(image[0])/Ny)
    n=min([nx,ny])
    x_offset=int((len(image)-Nx*n)/2)
    y_offset=int((len(image[0])-Ny*n)/2)
    out=np.zeros([Nx,Ny,3])
    for i in range(n):
        for j in range(n):
            out+=image[i+x_offset::n,j+y_offset::n][:Nx,:Ny]
    return out/(n**2)
        
def blow_up_image(image,factor):
    Nx=len(image)*factor
    Ny=len(image[0])*factor
    out=np.zeros([Nx,Ny,3])
    for i in range(factor):
        for j in range(factor):
            out[i::factor,j::factor]=image
    return out
    
    
def get_region(i0,j0,images):
    images=np.array(images)
    test=images[i0,j0]
    X=len(images)
    Y=len(images[0])
    out=[]
    to_check=[(i0,j0)]
    n=0
    while n<len(to_check):
        if images[to_check[n]]==test:
            i,j=to_check[n]
            out.append((i,j))
            for a,b in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
                if a>=0 and a<X and b>=0 and b<Y and (a,b) not in to_check:
                    to_check.append((a,b))
        n+=1
    return out
    
    
    
    
    