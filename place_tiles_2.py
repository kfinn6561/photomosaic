'''
Created on 27 Aug 2016

@author: Kieran Finn
'''
from tools import reduce_resolution_to, progress_bar,pload,pdump,blow_up_image
from imageio import imread,imwrite
from copy import copy
import numpy as np
import os
from collections import defaultdict



big='D://Mosaic'
maxie='C://Users/kiera/Mosaic'

if os.path.exists(big):
    main_dir=big
    dropbox='D://Dropbox'
else:
    main_dir=maxie
    dropbox='C://Users//kiera//Dropbox'


data_dir=main_dir+'/data'
output_dir=main_dir+'/output'
default_photos=dropbox+'/photos/USA_Edited'


import sys

try:
    options_fname=sys.argv[1]
except:
    options_fname=str(input('enter the name of the file you wish to make a mozaic of: '))
    
options={}
f=open(options_fname,'r')
r=f.readlines()
f.close()
for line in r:
    key,value=line.split(';')
    options[key.strip().rstrip()]=value.strip().rstrip()
 
 
    
input_fname=options['input']
dbase_dirname=options['directory']

if dbase_dirname=='photos':#backwards compatible
    dbase_dirname=default_photos

n_x=int(options['nx'])#each side split into this many photos
n_y=int(options['ny'])#each side split into this many photos
smoothing=int(options['smoothing'])#means we don't have to check every single pixel
blow_up=int(options['blow_up'])#blows up the picture by this amount to fit in more detail
try:
    single=bool(options['single'])
except KeyError:
    single=False


data_dir=data_dir+'/'+dbase_dirname.replace('\\','/').split('/')[-1]
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
    
output_fname=input_fname.split('.')[0]+'_place_tiles.jpg'    


 


'''Load the photo'''
print('Loading %s' %input_fname)
#logger.add('Loading %s' %input_fname)
image=imread(input_fname)

x_pix=len(image)
y_pix=len(image[0])
    


x_frame=int(x_pix/n_x)
y_frame=int(y_pix/n_y)

Nx=int(x_pix/x_frame)#real number of tiles
Ny=int(y_pix/y_frame)

comp_x=int(x_frame/smoothing)
comp_y=int(y_frame/smoothing)




single_dbase_fname=dbase_dirname.replace('\\','/').split('/')[-1]+'_single.dat'#use single colour matching  for selecting quantities

    

try:
    single_dbase=pload(data_dir+'/'+single_dbase_fname)
    print('Loaded database from %s' %single_dbase_fname)
except IOError:
    '''Make the database'''
    print('Making single colour database of %s' %dbase_dirname)
    single_dbase={}
    pnames=os.listdir(dbase_dirname)
    N_dbase=len(pnames)
    for i in range(N_dbase):
        progress_bar(i,N_dbase)
        try:
            single_dbase[pnames[i]]=np.average(imread(dbase_dirname+'/'+pnames[i]), axis=(0,1))
        except ValueError:
            pass
    print('\n')
    print('Database completed')
    #logger.add('Completed Database')
    pdump(single_dbase,data_dir+'/'+single_dbase_fname)
    print('Saved database to %s' %single_dbase_fname)
    
if single:
    print('Using single colour matching')
    dbase=single_dbase
else:
    dbase_fname=dbase_dirname.replace('\\','/').split('/')[-1]+'_'+str(comp_x)+'_'+str(comp_y)+'.dat'
    try:
        dbase=pload(data_dir+'/'+dbase_fname)
        print('Loaded database from %s' %dbase_fname)
    except IOError:
        '''Make the database'''
        print('Making the database of %s' %dbase_dirname)
        dbase={}
        pnames=os.listdir(dbase_dirname)
        N_dbase=len(pnames)
        for i in range(N_dbase):
            progress_bar(i,N_dbase)
            try:
                if single:
                    dbase[pnames[i]]=np.average(imread(dbase_dirname+'/'+pnames[i]), axis=(0,1))
                else:
                    dbase[pnames[i]]=reduce_resolution_to(imread(dbase_dirname+'/'+pnames[i]), comp_x,comp_y)
            except ValueError:
                pass
        print('\n')
        print('Database completed')
        #logger.add('Completed Database')
        pdump(dbase,data_dir+'/'+dbase_fname)
        print('Saved database to %s' %dbase_fname)

pnames=list(dbase.keys())
N_dbase=len(pnames)
   
'''Making database of frames'''
print('Making database of frames')
frame_dbase={}
single_frame_dbase={}
for i in range(Nx):
    progress_bar(i*Ny,Nx*Ny)
    for j in range(Ny):
        single_frame_dbase[(i,j)]=np.average(image[int(i*x_frame):int((i+1)*x_frame),int(j*y_frame):int((j+1)*y_frame)],axis=(0,1))
        if not single:
            frame_dbase[(i,j)]=reduce_resolution_to(image[i*x_frame:(i+1)*x_frame,j*y_frame:(j+1)*y_frame],comp_x,comp_y)
if single:
    frame_dbase=single_frame_dbase
print('\n')            


'''Get ratio of photos'''
'''For each frame choose the top 10 best fitting colours and increase their presence by 1'''
print('Calculating Ratios')

keep=3#increase ratio of this many per frame

threshold=10

cap=100

ratios={pname:1 for pname in pnames}
for i in range(Nx):
    progress_bar(i*Ny,Nx*Ny)
    for j in range(Ny):
        #photos={}
        for k in range(N_dbase):
            score=np.average(np.abs(single_frame_dbase[(i,j)]-single_dbase[pnames[k]]))
            if ratios[pnames[k]]<cap and score<threshold:
                ratios[pnames[k]]+=1
                
                
                
            '''if len(photos)<keep or score<max(photos.keys()):
                if len(photos)>=keep:
                    del photos[max(photos.keys())]
                photos[score]=pnames[k]'''
        '''if len(photos)!=keep:
            print '\nError: len(photos)=%d'%len(photos)
            print i,j'''
        '''for photo in photos.values():
            ratios[photo]+=1'''
'''
norm=float(np.sum(ratios.values()))/(Nx*Ny)        
for pname in pnames:
    ratios[pname]/=norm
'''    

'''photo_list=[]
i=0
while len(photo_list)<Nx*Ny:
    i0=i
    while ratios[pnames[i%N_dbase]]<1:
        i+=1
        if i-i0>N_dbase:#run out of photos. Very unlikely to end up here
            for pname in pnames:
                ratios[pname]+=1
    photo_list.append(pnames[i%N_dbase])
    ratios[pnames[i%N_dbase]]-=1
    i+=1'''
    
    
    
if sum(list(ratios.values()))<Nx*Ny:#not enough photos to fill mosaic
    factor=Nx*Ny/sum(list(ratios.values()))
    for pname in pnames:
        ratios[pname]*=factor

    
photo_list=[]
i=0 
while max(ratios.values())>1:
    while ratios[pnames[i%N_dbase]]<1:
        i+=1
    photo_list.append(pnames[i%N_dbase])
    ratios[pnames[i%N_dbase]]-=1
    i+=1
    
leftovers=defaultdict(list)
for pname in pnames:
    leftovers[ratios[pname]].append(pname)
    
while len(photo_list)<Nx*Ny:
    max_score=max(leftovers.keys())
    photo_list+=leftovers[max_score]
    leftovers[0]+=leftovers[max_score]
    del leftovers[max_score]



print('\n')
    
'''Pick the photos'''
out_photos=[['' for j in range(Ny)] for i in range(Nx)]
print('picking the photos')
for i in range(Nx*Ny):
    progress_bar(i,Nx*Ny)
    photo=photo_list[i]
    temp_frame=(0,0)
    best_score=np.inf
    frames=list(frame_dbase.keys())
    for frame in frames:
        score=np.average(np.abs(frame_dbase[frame]-dbase[photo])**0.1)
        if score<best_score:
            best_score=score
            temp_frame=copy(frame)
    out_photos[temp_frame[0]][temp_frame[1]]=copy(photo)
    del frame_dbase[temp_frame]
print('\n')

#logger.add('picked photos')


'''Stitch the photos together'''  
print('Stitching the photos together')      

x_frame=x_frame*blow_up
y_frame=y_frame*blow_up

original=blow_up_image(image,blow_up)[:x_frame*Nx,:y_frame*Ny]

        

rows=[]
for i in range(Nx):
    #logger.add('stitching photo %d of %d' %(i*Ny+1,Nx*Ny))
    row=[]
    for j in range(Ny):
        progress_bar(i*Ny+j,Nx*Ny)
        
        datname=out_photos[i][j].strip('.')+'_%d_%d.dat' %(x_frame,y_frame)
        try:
            current=pload(data_dir+'/'+datname)
        except IOError:
            current=reduce_resolution_to(imread(dbase_dirname+'/'+out_photos[i][j]),x_frame,y_frame)
            pdump(current,data_dir+'/'+datname)
        
        
        row.append(copy(current))
    rows.append(np.hstack(row))
output=np.vstack(rows)
        

print('\n')
print('Writing the output to %s' %output_fname)                
imwrite(output_dir+'/'+output_fname,output)

'''
for i in [25,50,75]:
    print('mixing in %d%% of the original' %(i))
    imwrite(output_dir+'/'+output_fname.split('.')[0]+'%d.jpg' %(i),np.average([original,output],weights=[i,100-i],axis=0))
'''
for i in range(1,10):
    print('mixing in %d%% of the original' %(i*10))
    imwrite(output_dir+'/'+output_fname.split('.')[0]+'%d.jpg' %(i*10),np.average([original,output],weights=[i,10-i],axis=0))


#logger.add('Finished')
print('Finished') 
        








