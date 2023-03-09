# -*- coding: utf-8 -*-
"""yolov5.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oQRKFof3-XbtGLxO7uL8hLXJo8laDI_o
"""

!pip install --upgrade seaborn

import numpy as np, pandas as pd
from glob import glob
import shutil, os
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold
from tqdm.notebook import tqdm
import seaborn as sns

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

import zipfile

with zipfile.ZipFile('/content/drive/MyDrive/Chest X-ray(512).zip', 'r') as zip_ref:
  zip_ref.extractall('./input')

len(os.listdir('/content/input/512_B'))

train_df = pd.read_csv('/content/input/train.csv')
train_df = train_df[train_df.class_id!=14].reset_index(drop = True)
train_df

pd.read_csv('/content/drive/MyDrive/vinbig_train.csv')

train_df = pd.read_csv('/content/drive/MyDrive/vinbig_train.csv')
train_df['image_path'] = f'/content/input/train/'+ train_df.image_id+'.png' 

train_df['x_min'] = train_df.apply(lambda row: (row.x_min)/row.width, axis =1)
train_df['x_max'] = train_df.apply(lambda row: (row.x_max)/row.width, axis =1)
train_df['x_mid'] = train_df.apply(lambda row: (row.x_max+row.x_min)/2, axis =1)

train_df['y_min'] = train_df.apply(lambda row: (row.y_min)/row.height, axis =1)
train_df['y_max'] = train_df.apply(lambda row: (row.y_max)/row.height, axis =1)
train_df['y_mid'] = train_df.apply(lambda row: (row.y_max+row.y_min)/2, axis =1)

train_df['h'] = train_df.apply(lambda row: (row.y_max-row.y_min), axis =1) #height
train_df['w'] = train_df.apply(lambda row: (row.x_max-row.x_min), axis =1) #width

train_df['area'] = train_df['w']*train_df['h']

train_df = train_df[train_df.class_id!=14].reset_index(drop = True)
train_df.head()

features = ['x_min', 'y_min', 'x_max', 'y_max', 'x_mid', 'y_mid', 'w', 'h', 'area']
y = train_df['class_id']
X = train_df[features]
X.shape, y.shape

class_ids, class_names = list(zip(*set(zip(train_df.class_id, train_df.class_name))))
class_list = list(np.array(class_names)[np.argsort(class_ids)])
class_list = list(map(lambda x: str(x), class_list))
class_list

fold = 4
gkf  = GroupKFold(n_splits = 5)
train_df['fold'] = -1
for fold, (train_idx, val_idx) in enumerate(gkf.split(train_df, groups = train_df.image_id.tolist())):
    train_df.loc[val_idx, 'fold'] = fold
train_df.head()

val_files   = []
train_files = []
val_files += list(train_df[train_df.fold==fold].image_path.unique())
train_files += list(train_df[train_df.fold!=fold].image_path.unique())
print(len(train_files)) #size of train dataset
print(len(val_files)) # size of validation set

os.makedirs('/content/kaggle/working/vinbigdata/labels/train')
os.makedirs('/content/kaggle/working/vinbigdata/labels/val')
os.makedirs('/content/kaggle/working/vinbigdata/images/train')
os.makedirs('/content/kaggle/working/vinbigdata/images/val')

!gdown --id 18vKptjbi-OMgHssPw68JmhVPo9bwZeMv

with zipfile.ZipFile('/content/drive/MyDrive/vinbig_label.zip', 'r') as zip_ref:
  zip_ref.extractall('/content/kaggle/working/vinbigdata')

label_dir = '/content/kaggle/working/vinbigdata/labels'

for file in tqdm(train_files): # we use tqdm to see the progress of the copying of files
    shutil.copy(file, '/content/kaggle/working/vinbigdata/images/train')
    filename = file.split('/')[-1].split('.')[0]
    shutil.copy(os.path.join(label_dir, filename+'.txt'), '/content/kaggle/working/vinbigdata/labels/train')
    
for file in tqdm(val_files):
    shutil.copy(file, '/content/kaggle/working/vinbigdata/images/val')
    filename = file.split('/')[-1].split('.')[0]
    shutil.copy(os.path.join(label_dir, filename+'.txt'), '/content/kaggle/working/vinbigdata/labels/val')

from os import listdir
from os.path import isfile, join
import yaml

cwd = '/content/kaggle/working'

with open(join( cwd , 'train.txt'), 'w') as f:
    for path in glob('/content/kaggle/working/vinbigdata/images/train/*.png'):
        f.write(path+'\n')
            
with open(join( cwd , 'val.txt'), 'w') as f:
    for path in glob('/content/kaggle/working/vinbigdata/images/val/*.png'):
        f.write(path+'\n')

data = dict(
    train =  join( cwd , 'train.txt') ,
    val   =  join( cwd , 'val.txt' ),
    nc    = 14,
    names = class_list
    )

with open(join( cwd , 'vinbigdata.yaml'), 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)

f = open(join( cwd , 'vinbigdata.yaml'), 'r')
print('\nyaml contents:')
print(f.read())

import torch
from IPython.display import Image, clear_output  # to display images and clear outputs



# shutil.copytree('/content/input/yolov5', '/content/kaggle/working/yolov5')
# os.chdir('/content/kaggle/working/yolov5')

# clear_output()
print('Setup complete. Using torch %s %s' % (torch.__version__, torch.cuda.get_device_properties(0) if torch.cuda.is_available() else 'CPU'))

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/kaggle/working
# %pwd

!git clone https://github.com/ultralytics/yolov5

!WANDB_MODE="dryrun" python ./yolov5/train.py --img 640 --batch 16 --epochs 30 --data /content/kaggle/working/vinbigdata.yaml --weights yolov5x.pt --cache

import numpy as np, pandas as pd
from glob import glob
import shutil, os
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold
from tqdm.notebook import tqdm
import seaborn as sns

dim = 512 #1024, 256, 'original'
test_dir = '/content/input/test'
weights_dir = '/content/kaggle/working/yolov5/runs/train/exp/weights/best.pt'

test_df = pd.read_csv('/content/drive/MyDrive/test.csv')
test_df.head()

# Commented out IPython magic to ensure Python compatibility.
# %pwd

!python /content/kaggle/working/yolov5/detect.py --weights $weights_dir\
--img 640\
--conf 0.01\
--iou 0.4\
--source $test_dir\
--save-txt --save-conf --exist-ok

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
import numpy as np
import random
import cv2
from glob import glob
from tqdm import tqdm

files = glob('runs/detect/exp/*png')
for _ in range(3):
    row = 4
    col = 4
    grid_files = random.sample(files, row*col)
    images     = []
    for image_path in tqdm(grid_files):
        img          = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
        images.append(img)

    fig = plt.figure(figsize=(col*5, row*5))
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(col, row),  # creates 2x2 grid of axes
                     axes_pad=0.05,  # pad between axes in inch.
                     )

    for ax, im in zip(grid, images):
        # Iterating over the grid returns the Axes.
        ax.imshow(im)
        ax.set_xticks([])
        ax.set_yticks([])
    plt.show()

def yolo2voc(image_height, image_width, bboxes):
    """
    yolo => [xmid, ymid, w, h] (normalized)
    voc  => [x1, y1, x2, y1]
    
    """ 
    bboxes = bboxes.copy().astype(float) # otherwise all value will be 0 as voc_pascal dtype is np.int
    
    bboxes[..., [0, 2]] = bboxes[..., [0, 2]]* image_width
    bboxes[..., [1, 3]] = bboxes[..., [1, 3]]* image_height
    
    bboxes[..., [0, 1]] = bboxes[..., [0, 1]] - bboxes[..., [2, 3]]/2
    bboxes[..., [2, 3]] = bboxes[..., [0, 1]] + bboxes[..., [2, 3]]
    
    return bboxes



image_ids = []
PredictionStrings = []

for file_path in tqdm(glob('/content/kaggle/working/yolov5/runs/detect/exp/labels/*txt')):
    image_id = file_path.split('/')[-1].split('.')[0]
    w, h = test_df.loc[test_df.image_id==image_id,['width', 'height']].values[0]
    f = open(file_path, 'r')
    data = np.array(f.read().replace('\n', ' ').strip().split(' ')).astype(np.float32).reshape(-1, 6)
    data = data[:, [0, 5, 1, 2, 3, 4]]
    bboxes = list(np.round(np.concatenate((data[:, :2], np.round(yolo2voc(h, w, data[:, 2:]))), axis =1).reshape(-1), 1).astype(str))
    for idx in range(len(bboxes)):
        bboxes[idx] = str(int(float(bboxes[idx]))) if idx%6!=1 else bboxes[idx]
    image_ids.append(image_id)
    PredictionStrings.append(' '.join(bboxes))

pred_df = pd.DataFrame({'image_id':image_ids,
                        'PredictionString':PredictionStrings})
sub_df = pd.merge(test_df, pred_df, on = 'image_id', how = 'left').fillna("14 1 0 0 1 1")
sub_df = sub_df[['image_id', 'PredictionString']]
sub_df
# sub_df.to_csv('/kaggle/working/submission.csv',index = False)
# sub_df.tail()

sub_df.to_csv('yolov5.csv',index = False )

