"""Research-only masked SIFT matching; never promotes a production verdict."""
import hashlib
import cv2
import numpy as np
from .correspondence_checks import check_correspondences


def stable_registration(before, after, before_excluded, after_excluded):
    """Exclusions use each original image's coordinates; nonzero means do not match.

    Masks must be obtained without evaluation labels. This method does not infer
    stable ground truth from a proposal or certify an acquisition's geometry.
    """
    a, b = np.asarray(before), np.asarray(after)
    if (a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3 or a.dtype != np.uint8
            or b.dtype != np.uint8 or min(a.shape[:2]) < 64 or max(a.shape[:2]) > 2048):
        raise ValueError('Require equal uint8 RGB images, dimensions 64 through 2048.')
    h, w = a.shape[:2]
    masks=[]
    for excluded in (before_excluded, after_excluded):
        excluded=np.asarray(excluded)
        if excluded.shape != (h,w) or excluded.dtype != np.uint8 or not np.isin(excluded,[0,255]).all():
            raise ValueError('Exclusions must be same-frame uint8 binary 0/255 masks.')
        # Conservative guard around excluded objects; descriptor support is also checked.
        masks.append(255-cv2.dilate(excluded, np.ones((65,65),np.uint8)))
    detector=cv2.SIFT_create(nfeatures=4000)
    features=[]
    for image, mask in zip((a,b),masks):
        points, descriptors=detector.detectAndCompute(cv2.cvtColor(image,cv2.COLOR_RGB2GRAY),mask)
        distance=cv2.distanceTransform(cv2.copyMakeBorder(mask,1,1,1,1,cv2.BORDER_CONSTANT,value=0),cv2.DIST_L2,5)[1:-1,1:-1]
        selected=[i for i,p in enumerate(points) if distance[int(p.pt[1]),int(p.pt[0])] > 3*p.size]
        features.append(([points[i] for i in selected], None if descriptors is None or not selected else descriptors[selected]))
    (ka,da),(kb,db)=features
    src=[];dst=[]
    if da is not None and db is not None and min(len(da),len(db))>=2:
        matcher=cv2.BFMatcher(cv2.NORM_L2)
        def ratio(query, train):
            return {p[0].queryIdx:p[0].trainIdx for p in matcher.knnMatch(query,train,k=2)
                    if len(p)==2 and p[0].distance < .72*p[1].distance}
        backward,forward=ratio(db,da),ratio(da,db)
        used_source=set();used_target=set()
        for ib,ia in sorted(backward.items()):
            sp,tp=kb[ib].pt,ka[ia].pt
            if forward.get(ia)!=ib or sp in used_source or tp in used_target: continue
            src.append(sp);dst.append(tp);used_source.add(sp);used_target.add(tp)
    source=np.asarray(src,dtype=float).reshape(-1,2);target=np.asarray(dst,dtype=float).reshape(-1,2)
    return {'schema':'geoalibi-stable-registration-research-v1',
            'method':'masked mutual-ratio SIFT; separate same-frame exclusions',
            'width':w,'height':h,'exclusion_guard_px':32,'descriptor_clearance_keypoint_sizes':3,
            'input_sha256':{name:hashlib.sha256(np.asarray(value).tobytes()).hexdigest()
                            for name,value in zip(('before_rgb','after_rgb','before_excluded','after_excluded'),
                                                  (a,b,before_excluded,after_excluded))},
            'keypoints_before':len(ka),'keypoints_after':len(kb),
            'source_after_xy':source.tolist(),'target_before_xy':target.tolist(),
            'geometry':check_correspondences(source,target,width=w,height=h),
            'scope':'Research correspondence consistency only. Fixed holdout uses the same matcher, not independent human truth. '
                    'Exclusion masks must not use evaluation labels. No production gate, benchmark score or provider call changed.'}
