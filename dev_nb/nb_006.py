
        #################################################
        ### THIS FILE WAS AUTOGENERATED! DO NOT EDIT! ###
        #################################################
        # file to edit: 006_carvana.ipynb

from nb_005 import *

class ImageMask(Image):
    def lighting(self, func, *args, **kwargs): return self

    def refresh(self):
        self.sample_kwargs['mode'] = 'nearest'
        return super().refresh()

def open_mask(fn):
    return ImageMask(pil2tensor(PIL.Image.open(fn)).float())

class MatchedFilesDataset(DatasetBase):
    def __init__(self, x:Collection[Path], y:Collection[Path]):
        assert len(x)==len(y)
        self.x,self.y = np.array(x),np.array(y)

    def __getitem__(self, i):
        return open_image(self.x[i]), open_mask(self.y[i])

def split_arrs(idxs, *a):
    mask = np.zeros(len(a[0]),dtype=bool)
    mask[np.array(idxs)] = True
    return [(o[mask],o[~mask]) for o in map(np.array, a)]

def normalize_batch(b, mean, std, do_y=False):
    x,y = b
    x = normalize(x,mean,std)
    if do_y: y = normalize(y,mean,std)
    return x,y

def normalize_funcs(mean, std, do_y=False, device=None):
    if device is None: device=default_device
    return (partial(normalize_batch, mean=mean.to(device),std=std.to(device), do_y=do_y),
            partial(denormalize,     mean=mean,           std=std))

def pred_batch(learn):
    x,y = next(iter(learn.data.valid_dl))
    return x,learn.model(x).detach()

Learner.pred_batch = pred_batch