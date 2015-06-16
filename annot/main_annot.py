# -*- coding: utf-8 -*-
"""
Main module of thumbnailer.

function scan_directory() does all the work and calls everything else. It is
the only thing a normal user should have to use.
"""

import dicom, os, dicom_coords, metasql, sys
import matplotlib.pylab as plt
import numpy as np
from numpy import array
from matplotlib.patches import Ellipse

#copied from prog.util.load_cube
def get_annot(h):
    """Retrieve annotation from header and convert points to
    DICOM, if they exist."""
    val = h.get((0x029, 0x1300),None)
    if val:
        print val
        x,y = val.value.split('\\')[2:4]
        out = dicom_coords.data_dicom([0,int(y),int(x)],h)
        val = val.value + "\\%s"%repr(out)
        x,y = val.split('\\')[4:6]
        out = dicom_coords.data_dicom([0,int(y),int(x)],h)
        val = val + "\\%s"%repr(out)
        annot = []
        for e in val.split('\\'):
            try:
                annot.append(eval(e))
            except:
                annot.append(e)
        if len( annot ) > 20:
            raise ValueError

        return [annot]
    return []


def scan_directory(pars):
    """
Main root function.

Produces images, puts metadata in a database table and provides URLs
for all annotations in a given data-set.

Parameters
----------
A single dictionary with the following keys, all optional:

directory : string
    Full path to search. Should contain DICOM images, of which some
    may have annotations.
    
im_path : string
    Root of the location in which to store the output images.
    
URLroot : string
    Front part of every image URL.
    
logfile : string
    Location to output progress to - set to None for no logging.
    
sql : string
    connection string for the SQL interaction
    
clobber : bool
    whether to overwrite existing, clashing database entried and image files
    
logmode : 'w'|'a'
    whether to write a new logfile from scratch, or append.
    
dry_run : bool
    
    
Returns
-------

No direct return expected, but images will be created under im_path, 
metadata will be edited, and logfile will be updated.
    """
    plt.ioff()
    if pars['logfile']: 
        pars['log'] = open(pars['logfile'], pars['logmode'])
    allfiles = os.listdir(pars['directory'])
    metasql.connect(pars['sql'])
    for myfile in allfiles:
        if os.path.isdir(myfile):
            continue
        try:
            f = dicom.read_file(os.sep.join([pars['directory'],myfile]))
            annots = get_annot(f)
            if(annots):
                print "------------------------------------"
                print myfile
            for i,ann in enumerate(annots):
                print ann
                ending = "annot%s_%s_%s_%s.jpeg"%(f.AccessionNumber,f.SeriesNumber,f.InstanceNumber,i)
                acc = "".join([a for a in f.AccessionNumber if a.isdigit()])
                pars['im_file'] = os.sep.join([pars['im_path'], acc, ending])
                pars['URL'] = '/'.join([pars['im_path'], acc, ending])
                
                make_image(f, pars, ann)
                put_SQL(f, pars, ann)
        except dicom.filereader.InvalidDicomError:
            pass
    
def make_image(myfile, pars, ann):
    """
Produce image and save to disc
    """    
    fig = plt.figure(-1,figsize=(10,8))
    ax = fig.add_subplot(111)
    im = myfile.pixel_array
    nx,ny = myfile.Columns,myfile.Rows
    start = dicom_coords.data_dicom([0,0,0], myfile)
    end = dicom_coords.data_dicom([0,0,nx], myfile)
    indx = np.argmax((start-end)**2)
    minx,maxx = start[indx],end[indx]
    end = dicom_coords.data_dicom([0,ny,0], myfile)
    indy = np.argmax((start-end)**2)
    miny,maxy = start[indy],end[indy]
    
    img =ax.imshow( im, vmax = np.percentile(im,99), vmin = np.percentile(im, 10),
              cmap = 'gray', aspect='equal', origin='upper', interpolation='nearest',
              extent = [minx,maxx,maxy,miny])
    fig.colorbar(mappable=img, ax = ax)
    ax.set_title(os.path.split(pars['im_file'])[1][5:-5])
    
    x1,y1 = ann[-2][[indx,indy]]
    x2,y2 = ann[-1][[indx,indy]]
    if ann[0]=='CALIPER':
        ax.plot([x1, x2], [y1,y2], marker='s', mfc='g', ms=5, ls=':', lw=0.8, c='g')
        d = np.sqrt((ann[2] - ann[4])**2*ann[12]**2 + ( ann[3] - ann[5] )**2*ann[13]**2)
        fig.text(0.6,0.05,"Length: %5.2f mm"%d, ha='center', va='center')
    elif ann[0]=='LINEARROW':
        ax.arrow(x1, y1, x2-x1, y2-y1, length_includes_head=True,
                 color='g', width=0.2)
    elif ann[0]=="ELLIPSE":
        x3,y3 = dicom_coords.data_dicom([0,ann[7],ann[6]], myfile)[[indx,indy]]
        ang = ann[8]
        e = Ellipse((x1,y1),(x2-x1)*2,(y3-y1)*2, angle=ang, ec='g', fc='none', fill=False)
        e.set_clip_box(ax.bbox)
        ax.add_artist(e)
    else:
        ValueError("New type!")
        
    ax.set_xbound(minx,maxx)
    ax.set_ybound(miny,maxy)
    cosines = np.array(myfile.ImageOrientationPatient, dtype=float)

    if np.alltrue(cosines==[-0.,  1.,  0., -0., -0., -1.]):
        ax.set_xlabel('A -- P')
        ax.set_ylabel('I -- S')
    if np.alltrue(cosines==[-1., -0.,  0., -0., -1.,  0.]):
        ax.set_xlabel('L -- R')
        ax.set_ylabel('A -- P')
    if np.alltrue(cosines==[ 1.,  0.,  0.,  0.,  0., -1.]):
        raise ValueError("Coronal!")
    if pars['dry_run']:
        return 
    try:
        os.makedirs(os.path.split(pars['im_file'])[0])         
    except OSError:
        pass
    if os.path.exists(pars['im_file']):
        if pars['clobber']:
            print "Overwriting image %s"%pars['im_file']
            fig.savefig(pars['im_file'])
        else:
            print "%s exists, not overwriting"%pars['im_file']
    else:
        fig.savefig(pars['im_file'])
    plt.close(fig)
    if pars['log']:
        pars['log'].write("Image processed %s\n"%pars['im_file'])    
    
def put_SQL(myfile, pars, ann):
    """
Produce database entry and save.
    """
    record = metasql.Meta()
    record.from_dicom(myfile, ann, pars)
    if pars['dry_run']:
        return
    rec1 = metasql.is_duplicate(record)
    if rec1:
        if pars['clobber']:
            rec1.from_dicom(myfile, ann, pars)
            metasql.s.add(rec1)
            metasql.s.commit()
            record=rec1
            print "Duplicate database entry: overwriting"
        else:
            print "Duplicate database entry: not overwriting"
    else:
        metasql.s.add(record)
        metasql.s.commit()
    if pars['log']:
       pars['log'].write(record.string_all()+'\n')
       
if __name__=='__main__':
    if len(sys.argv)!=2:
        print """Annotation thumbnailer - query database.

Usage:
> python main.py acc

where acc is the accession number you wish to query for. 
Will return all records in the thumbnail database for the
given accession."""
    metasql.connect(pars['sql'])
    metasql.all_acc(sys.argv[1])