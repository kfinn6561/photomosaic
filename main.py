'''
Created on 27 Aug 2016

@author: Kieran Finn
'''
from tools import reduce_resolution_to, progress_bar,pload,pdump,blow_up_image,get_region
from imageio import imread,imwrite
from copy import copy
import numpy as np
import os
import random



big='D://Mosaic'
maxie='C://Users/kiera/Mosaic'

if os.path.exists(big):
    main_dir=big
    dropbox='D://Dropbox'
else:
    main_dir=maxie
    dropbox='C:/Users/kiera/Dropbox'


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
    
try:
    region_threshold=int(options['regions'])
    modify_regions=True
except KeyError:
    modify_regions=False


data_dir=data_dir+'/'+dbase_dirname.replace('\\','/').split('/')[-1]
if not os.path.exists(data_dir):
    os.mkdir(data_dir)



try:
    output_fname=options['output']
except KeyError:
    output_fname=input_fname.split('.')[0]

if single:
    output_fname+='_mosaic_single.jpg'    
else:
    output_fname+='_mosaic.jpg'    


 


'''Load the photo'''
print(('Loading %s' %input_fname))
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


if single:
    print('Using single colour matching')
    dbase_fname=dbase_dirname.replace('\\','/').split('/')[-1]+'_single.dat'
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
   
    
'''Pick the photos'''

photo_fname=input_fname.split('.')[0]+'_picked_photos_%d_%d_%d.dat' %(smoothing,n_x,n_y)
try:
    out_photos=pload(data_dir+'/'+photo_fname)
    print('Loaded picked photos from %s' %photo_fname)
except IOError:
    out_photos=[]
    print('picking the photos')
    for i in range(Nx):
        out_photos.append([])
        for j in range(Ny):
            progress_bar(i*Ny+j,Nx*Ny)
            if single:
                frame=np.average(image[int(i*x_frame):int((i+1)*x_frame),int(j*y_frame):int((j+1)*y_frame)],axis=(0,1))
            else:
                frame=reduce_resolution_to(image[i*x_frame:(i+1)*x_frame,j*y_frame:(j+1)*y_frame],comp_x,comp_y)
            temp_name=''
            best_score=np.inf
            for k in range(N_dbase):
                #progress_bar(k,N_dbase)
                #score=np.average((frame-dbase[pnames[k]])**2)
                #score=np.average(np.abs(frame-dbase[pnames[k]]))
                score=np.average(np.abs(frame-dbase[pnames[k]])**0.1)
                if score<best_score:
                    best_score=score
                    temp_name=pnames[k]
            out_photos[i].append(copy(temp_name))
    print('\n')
    pdump(out_photos,data_dir+'/'+photo_fname)
    print('saved picked photos to %s' %photo_fname)

#logger.add('picked photos')


'''find regions bigger than threshold'''

if modify_regions:
    print('finding regions')
    regions=[]
    checked=[]
    for i in range(Nx):
        for j in range(Ny):
            if (i,j) not in checked:
                region=get_region(i,j,out_photos)
                checked+=region
                if len(region)>region_threshold:
                    regions.append(region)
    print('found %d regions larger than %d' %(len(regions),region_threshold))
    reg_no=1
    for region in regions:
        print('changing photos for region %d' %reg_no)
        reg_no+=1
        N_spread=len(region)/region_threshold*4
        a,b=region[0]
        frame=dbase[out_photos[a][b]]
        choices={}
        for k in range(N_dbase):
            score=np.average(np.abs(frame-dbase[pnames[k]])**0.1)
            if len(choices)<N_spread or score<max(choices.keys()):
                choices[score]=pnames[k]
                if len(choices)>N_spread:
                    del choices[max(choices.keys())]
        for i,j in region:
            out_photos[i][j]=random.choice(list(choices.values()))


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


for i in range(1,10):
    print('mixing in %d%% of the original' %(i*10))
    imwrite(output_dir+'/'+output_fname.split('.')[0]+'%d.jpg' %(i*10),np.average([original,output],weights=[i,10-i],axis=0))


#logger.add('Finished')
print('Finished') 
        








