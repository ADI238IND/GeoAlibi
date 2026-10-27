"""Fit a bounded similarity transform; hold the final two supplied points out."""
import hashlib
import json

import cv2
import numpy as np


def register(a,b,points):
    try:
        p=np.asarray(points,dtype=np.float64)
    except (ValueError,TypeError) as exc:
        raise ValueError('Landmarks must be numeric [after_x, after_y, before_x, before_y] rows.') from exc
    if p.ndim!=2 or p.shape[1]!=4 or not 6<=len(p)<=20 or not np.isfinite(p).all():
        raise ValueError('Supply 6–20 finite landmark rows; final two are held out.')
    h,w=a.shape[:2]
    source,target=p[:,:2],p[:,2:]
    for xy in [source,target]:
        if ((xy<0).any() or (xy[:,0]>=w).any() or (xy[:,1]>=h).any()):
            raise ValueError('Landmarks must lie inside processed image bounds.')
        distances=np.linalg.norm(xy[:,None]-xy[None,:],axis=2)
        np.fill_diagonal(distances,np.inf)
        if distances.min()<2:raise ValueError('Landmarks must be distinct in both images.')
        if cv2.contourArea(cv2.convexHull(xy[:-2].astype(np.float32)))<.1*w*h:
            raise ValueError('Fit landmarks must span at least 10% of the scene area.')
        if np.linalg.norm(xy[-1]-xy[-2])<.15*np.hypot(w,h):
            raise ValueError('The two held-out landmarks must be spatially separated.')
    # x'=s*x-r*y+tx; y'=r*x+s*y+ty. Fit only the first N-2 pairs.
    x,y=source[:-2].T
    design=np.zeros((len(x)*2,4));design[::2]=np.stack([x,-y,np.ones_like(x),np.zeros_like(x)],axis=1)
    design[1::2]=np.stack([y,x,np.zeros_like(x),np.ones_like(x)],axis=1)
    coefficients,_,rank,_=np.linalg.lstsq(design,target[:-2].ravel(),rcond=None)
    if rank!=4:raise ValueError('Landmark geometry is degenerate.')
    s,r,tx,ty=coefficients
    matrix=np.array([[s,-r,tx],[r,s,ty]],np.float32)
    scale=np.hypot(s,r);angle=abs(np.degrees(np.arctan2(r,s)))
    if not .95<=scale<=1.05 or angle>5 or np.hypot(tx,ty)>.12*min(w,h):
        raise ValueError('Landmark transform exceeds supported small-registration limits.')
    predicted=source@matrix[:,:2].T+matrix[:,2]
    errors=np.linalg.norm(predicted-target,axis=1)
    fit_rms=float(np.sqrt(np.mean(errors[:-2]**2)))
    holdout_rms=float(np.sqrt(np.mean(errors[-2:]**2)))
    if fit_rms>1.5 or holdout_rms>2 or errors[-2:].max()>3:
        raise ValueError('Landmark fit or held-out residual exceeds the pixel tolerance. Recheck the correspondences.')
    warped=cv2.warpAffine(b,matrix,(w,h))
    valid=cv2.warpAffine(np.ones((h,w),np.uint8),matrix,(w,h),flags=cv2.INTER_NEAREST)
    valid=cv2.erode(valid,np.ones((5,5),np.uint8)).astype(bool)
    if valid.mean()<.75:raise ValueError('Too little shared image area after landmark registration.')
    return warped,valid,{'method':'supplied landmarks + held-out check','matrix':matrix.tolist(),'reliable':True,'overlap':round(float(valid.mean()),4),
        'basis':'user-supplied correspondences; geometric consistency checked, not independently authenticated',
        'fit_points':len(p)-2,'held_out_points':2,'fit_rms_px':round(fit_rms,4),'held_out_rms_px':round(holdout_rms,4),
        'held_out_errors_px':errors[-2:].tolist(),'landmarks':p.tolist(),
        'landmark_hash':hashlib.sha256(json.dumps(p.tolist(),separators=(',',':')).encode()).hexdigest()}
