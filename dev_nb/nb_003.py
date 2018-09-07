
        #################################################
        ### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
        #################################################

import nb_002
from nb_002c import *

import operator

class FilesDataset(DatasetBase):
    def __init__(self, fns, labels, classes=None):
        if classes is None: classes = list(set(labels))
        self.classes = classes
        self.class2idx = {v:k for k,v in enumerate(classes)}
        self.x = np.array(fns)
        self.y = np.array([self.class2idx[o] for o in labels])

    def __getitem__(self,i): return open_image(self.x[i]),self.y[i]

    @classmethod
    def from_folder(cls, folder, classes=None, test_pct=0.):
        if classes is None: classes = [cls.name for cls in find_classes(folder)]

        fns,labels = [],[]
        for cl in classes:
            fnames = get_image_files(folder/cl)
            fns += fnames
            labels += [cl] * len(fnames)

        if test_pct==0.: return cls(fns, labels, classes=classes)

        fns,labels = np.array(fns),np.array(labels)
        is_test = np.random.uniform(size=(len(fns),)) < test_pct
        return (cls(fns[~is_test], labels[~is_test], classes=classes),
                cls(fns[is_test], labels[is_test], classes=classes))

def affine_mult(c,m):
    if m is None: return c
    size = c.size()
    _,h,w,_ = size
    m[0,1] *= h/w
    m[1,0] *= w/h
    c = c.view(-1,2)
    c = torch.addmm(m[:2,2], c,  m[:2,:2].t())
    return c.view(size)

nb_002.affine_mult = affine_mult

class TfmCrop(TfmPixel): order=99

@TfmCrop
def crop_pad(x, size, padding_mode='reflect',
             row_pct:uniform = 0.5, col_pct:uniform = 0.5):
    if padding_mode=='zeros': padding_mode='constant'
    size = listify(size,2)
    if x.shape[1:] == size: return x
    rows,cols = size
    if x.size(1)<rows or x.size(2)<cols:
        row_pad = max((rows-x.size(1)+1)//2, 0)
        col_pad = max((cols-x.size(2)+1)//2, 0)
        x = F.pad(x[None], (col_pad,col_pad,row_pad,row_pad), mode=padding_mode)[0]
    row = int((x.size(1)-rows+1)*row_pct)
    col = int((x.size(2)-cols+1)*col_pct)

    x = x[:, row:row+rows, col:col+cols]
    return x.contiguous() # without this, get NaN later - don't know why

def round_multiple(x, mult): return (int(x/mult+0.5)*mult)

def get_crop_target(target_px, mult=32):
    target_r,target_c = listify(target_px, 2)
    return round_multiple(target_r,mult),round_multiple(target_c,mult)

def get_resize_target(img, crop_target, do_crop=False):
    if crop_target is None: return None
    ch,r,c = img.shape
    target_r,target_c = crop_target
    ratio = (min if do_crop else max)(r/target_r, c/target_c)
    return ch,round(r/ratio),round(c/ratio)

def is_listy(x)->bool: return isinstance(x, (tuple,list))

def apply_tfms(tfms, x, do_resolve=True, xtra=None, size=None,
               mult=32, do_crop=True, padding_mode='reflect', **kwargs):
    if not tfms: return x
    if not xtra: xtra={}
    tfms = sorted(listify(tfms), key=lambda o: o.tfm.order)
    if do_resolve: resolve_tfms(tfms)
    x = Image(x.clone())
    x.set_sample(padding_mode=padding_mode, **kwargs)
    if size:
        crop_target = get_crop_target(size, mult=mult)
        target = get_resize_target(x, crop_target, do_crop=do_crop)
        x.resize(target)

    size_tfms = [o for o in tfms if isinstance(o.tfm,TfmCrop)]
    for tfm in tfms:
        if tfm.tfm in xtra: x = tfm(x, **xtra[tfm.tfm])
        elif tfm in size_tfms: x = tfm(x, size=size, padding_mode=padding_mode)
        else: x = tfm(x)
    return x.px

import nb_002b
nb_002b.apply_tfms = apply_tfms

def rand_zoom(*args, **kwargs): return zoom(*args, row_pct=(0,1), col_pct=(0,1), **kwargs)
def rand_crop(*args, **kwargs): return crop_pad(*args, row_pct=(0,1), col_pct=(0,1), **kwargs)
def zoom_crop(scale, do_rand=False, p=1.0):
    zoom_fn = rand_zoom if do_rand else zoom
    crop_fn = rand_crop if do_rand else crop_pad
    return [zoom_fn(scale=scale, p=p), crop_fn()]