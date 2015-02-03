# -*- coding: utf-8 -*-
"""
Cooredinate tranformations to/from DICOM patient system.
"""

import numpy as np

def transformation(head):
    """Simplest transform matrix, specific to Sagittal orientation."""
    pos = np.array(head.ImagePositionPatient,dtype=float)
    M = np.array([[0, 0, head.SpacingBetweenSlices, pos[0]],
                   [0, head.PixelSpacing[1], 0, pos[1]],
                    [-head.PixelSpacing[0], 0, 0, pos[2]],
                    [0, 0, 0, 1]],dtype=float)
    return M

def rotation_between(head1,head2):
    c = np.array(head1.ImageOrientationPatient,dtype=float)
    n = np.cross([c[3],c[4],c[5]],[c[0],c[1],c[2]])
    R1 = [[ c[3], c[0], n[0], 0],
         [ c[4], c[1], n[1], 0],
         [ c[5], c[2], n[2], 0],
         [  0  ,  0  ,  0 ,  1]]
    c = np.array(head2.ImageOrientationPatient,dtype=float)
    n = np.abs(np.cross([c[3],c[4],c[5]],[c[0],c[1],c[2]]))
    R2 = [[ c[3], c[0], n[0], 0,],
         [ c[4], c[1], n[1], 0,],
         [ c[5], c[2], n[2], 0],
         [  0  ,  0  ,  0 ,  1]]
    return np.dot(R1,np.linalg.inv(R2))

def A(head):
    """Affine for data->DICOM coord, from
    http://nipy.sourceforge.net/nibabel/dicom/dicom_orientation.html#d-affine-formulae
    """
    if hasattr(head,'cosines'):
        c = head.cosines
    else:
        c = np.array(head.ImageOrientationPatient,dtype=float)
    if hasattr(head,'vox'):
        ds,dc,dr = head.vox
    else:
        dr = float(head.PixelSpacing[1])
        dc = float(head.PixelSpacing[0])
        ds = float(getattr(head,'SpacingBetweenSlices',1))
    if hasattr(head,'origin'):
        s = head.origin
    else:
        s = np.array(head.ImagePositionPatient,dtype=float)
    n = np.abs(np.cross([c[3],c[4],c[5]],[c[0],c[1],c[2]]))
    A = [[ dr*c[0], dc*c[3], ds*n[0], s[0]],
         [ dr*c[1], dc*c[4], ds*n[1], s[1]],
         [ dr*c[2], dc*c[5], ds*n[2], s[2]],
         [     0  ,     0  ,      0 ,    1]]
    return np.array(A,dtype=float)

def norm_axis(c):
    """For the input cosines array (aka ImageOrientationPatient),
    return which of the three axes increases in the through-plane
    direction
    Returns None for obleque orientation."""
    c = np.array(c,dtype='float')
    n = np.cross([c[3],c[4],c[5]],[c[0],c[1],c[2]])
    if len(np.where(abs(n)==1)[0])>0:
        return np.where(abs(n)==1)[0][0]
    return None

def invA(head):
    return np.linalg.inv(A(head))

def dicom_data(coo,head):
    """Dicom coords (xyz) to data (array) coords (zyx) for header head. """
    M = invA(head)
    inarr = np.array([coo[0],coo[1],coo[2],1])
    out = np.dot(M,inarr)
    return out[-2::-1]

def data_dicom(coo,head):
    """Data (array) coords (zyx) to dicom coords (xyz) for header head)."""
    M = A(head)
    inarr = np.array([coo[2],coo[1],coo[0],1])
    out = np.dot(M,inarr)
    return out[:-1]

def affine(vol1,vol2):
    """Finds the affine transform (in the form to be used by nipi for a
    resampling) between two volumes based on the dicom coordinates referenced
    in the headers."""
    from nipy.algorithms.registration import affine
    T1 = A(vol1)
    T2 = invA(vol2)
    return affine.Affine(np.dot(T2,T1))