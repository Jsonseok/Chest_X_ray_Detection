# -*- coding: utf-8 -*-
"""mmdetection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZHxOu4vb-6e_SEdBVA6cORyQzZsL_z9W
"""



"""## MMD

### MMD_pip&import
"""

import torch
print(torch.__version__)

!pip uninstall mmdet
!pip install openmim
!mim install mmdet

# Commented out IPython magic to ensure Python compatibility.

# %cd /content
!git clone https://github.com/open-mmlab/mmdetection.git
# %cd ./mmdetection
!pip install openmim
!mim install mmdet==2.22.0

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import cv2
import time
import datetime
import os
import shutil
import random
from tqdm.notebook import tqdm
from glob import glob
from collections import defaultdict

seed = 41

"""### MMD_Data Setting"""

# Commented out IPython magic to ensure Python compatibility.
# https://drive.google.com/file/d/1SrbdUq86pOQuDhKbWS_DdaOyAk6JUjGW/view?usp=share_link
# %cd /content
image_size = 1024

os.makedirs('./data', exist_ok=True)
!unzip -q '/content/drive/MyDrive/1024x1024.zip' -d ./data

# %cd /content/mmdetection
df_train = pd.read_csv('/content/drive/MyDrive/vinbig_train.csv')
df_train_meta = pd.read_csv('./data/train_meta.csv')

# NAN값 치환
df_train = pd.merge(df_train, df_train_meta, on='image_id').fillna(0)

# No finding 데이터 제외
df_train = df_train[df_train['class_id'] != 14]
df_train['class_id'] = df_train['class_id'] + 1

# 이미지 크기에 따른 절대좌표 변환
df_train[['x_min', 'x_max']] = df_train[['x_min', 'x_max']].apply(lambda x : (x / df_train['dim1']) * image_size)
df_train[['y_min', 'y_max']] = df_train[['y_min', 'y_max']].apply(lambda x : (x / df_train['dim0']) * image_size)
df_train

categories = {}
for i, j in zip(sorted(df_train['class_name'].unique()), sorted(df_train['class_id'].unique())):
  categories[i] = int(j)
categories

df_train = df_train.drop(columns = ['class_name', 'rad_id', 'dim0', 'dim1'])
df_train

def convert_to_coco(name_list, df, save_path):

  res = defaultdict(list)
    
  df = df[df['image_id'].isin(name_list)]
  names = df['image_id'].unique()
  n_id = 0

  for pic_name in tqdm(names):

    df_temp = df[df['image_id'] == pic_name]

    res['images'].append({
        'id': pic_name,
        'width': image_size,
        'height': image_size,
        'file_name': pic_name+".png"
    })
      
    for temp in df_temp.values:
        x1, y1, x2, y2 = temp[2], temp[3], temp[4], temp[5]
        
        w, h = x2 - x1, y2 - y1
        
        res['annotations'].append({
            'id': n_id,
            'image_id': pic_name,
            'category_id': temp[1],
            'area': w * h,
            'bbox': [x1, y1, w, h],
            'iscrowd': 0,
        })
        n_id += 1
    
  for name, id in categories.items():
      res['categories'].append({
          'id': id,
          'name': name,
      })
  # return res
  with open(save_path, 'w') as f:
      json.dump(res, f)

random.seed(seed)

# train_files = glob(os.path.join(base_dir, 'train/*.png'))
# train_files = os.listdir('./input/train')
# train_files = list(map(del_extension, train_files))
train_files = df_train['image_id'].unique()

random.shuffle(train_files)

# 8:2로 학습/검증 데이터 분리
split_num = int(len(train_files)*0.2)
print("split_num :", split_num)

train_file = train_files[split_num:]
valid_file = train_files[:split_num]

len(train_file), len(valid_file),len(train_files)

# train
convert_to_coco(train_file, df_train, './data/train_annotations.json')
# validation
convert_to_coco(valid_file, df_train, './data/valid_annotations.json')

"""### MMD_Model Setting"""

# condition = 'cascade_rcnn'

# !mkdir checkpoints
# !wget -c https://download.openmmlab.com/mmdetection/v2.0/cascade_rcnn/cascade_rcnn_r50_fpn_1x_coco/cascade_rcnn_r50_fpn_1x_coco_20200316-3dc56deb.pth \
#       -O checkpoints/cascade_rcnn_r50_fpn_1x_coco_20200316-3dc56deb.pth

# config = "configs/cascade_rcnn/cascade_rcnn_r50_fpn_1x_coco.py"
# checkpoint = './checkpoints/cascade_rcnn_r50_fpn_1x_coco_20200316-3dc56deb.pth'

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/mmdetection

condition = 'faster_rcnn'

!mkdir checkpoints
!wget -c https://download.openmmlab.com/mmdetection/v2.0/faster_rcnn/faster_rcnn_r50_fpn_1x_coco/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth \
      -O checkpoints/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth

config = "configs/faster_rcnn/faster_rcnn_r50_fpn_1x_coco.py"
checkpoint = './checkpoints/faster_rcnn_r50_fpn_1x_coco_20200130-047c8118.pth'

#@title MMD_Config faster rcnn
import mmdet
import mmcv
from mmcv import Config
from mmdet.apis import set_random_seed
import os.path as osp

cfg = Config.fromfile(config)

cfg.runner.max_epochs = 30 #@param {type:"integer"}


# 라벨 목록
classes = (
    'Aortic enlargement',
    'Atelectasis',
    'Calcification',
    'Cardiomegaly',
    'Consolidation',
    'ILD',
    'Infiltration',
    'Lung Opacity',
    'Nodule/Mass',
    'Other lesion',
    'Pleural effusion',
    'Pleural thickening',
    'Pneumothorax',
    'Pulmonary fibrosis'
    )

# 데이터셋 경로
base_path = 'content/data'

# cocoformat.json 파일 경로
train_anno = 'train_annotations.json'
test_anno = 'valid_annotations.json'

# 이미지파일 경로
test_img =  'train'
train_img = 'train'

# 저장경로(?)
# save_dir = '/content/drive/MyDrive/Inference'
save_dir = 'work_dir'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
cfg.work_dir = save_dir

# 모델별 cfg 수정
# ==================================================
cfg.dataset_type = 'CocoDataset'
cfg.data_root = base_path


if condition == 'faster_rcnn':
  cfg.model.roi_head.bbox_head.num_classes = 14
elif condition == 'cascade_rcnn':
  for i in range(3):
    cfg.model.roi_head.bbox_head[i].num_classes = 14
  
cfg.data.train.type = 'CocoDataset'
cfg.data.train.data_root = base_path
cfg.data.train.ann_file = train_anno
cfg.data.train.img_prefix = train_img
cfg.data.train.classes = classes

img_norm_cfg = dict(type='Normalize', mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)
albu_train_transforms = [dict(type='RandomRotate90', p=0.5)] #dict(type='InvertImg', p=0.5)

cfg.data.train.pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(image_size, image_size), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    img_norm_cfg,
    dict(
        type='Albu',
        transforms=albu_train_transforms,
        bbox_params=dict(
        type='BboxParams',
        format='pascal_voc',
        # format='coco',
        label_fields=['gt_labels'],
        min_visibility=0.0,
        filter_lost_elements=True),
        keymap=dict(img='image', gt_bboxes='bboxes'),
        update_pad_shape=False,
        skip_img_without_anno=True),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels'])
]

cfg.data.val.pipeline[1].img_scale = (image_size, image_size)
cfg.data.test.pipeline = cfg.data.val.pipeline

cfg.data.test.type = 'CocoDataset'
cfg.data.test.data_root = base_path
cfg.data.test.ann_file = test_anno
cfg.data.test.img_prefix = test_img

cfg.data.val.type = 'CocoDataset'
cfg.data.val.data_root = base_path
cfg.data.val.ann_file = test_anno
cfg.data.val.img_prefix = test_img

cfg.data.samples_per_gpu = 16 #@param {type:"integer"}
cfg.data.workers_per_gpu = 2

cfg.data.val.classes = classes
cfg.data.test.classes = classes

# 옵티마이저 설정
cfg.lr_config.warmup = None
cfg.lr_config = dict(policy='step', warmup='linear', warmup_iters=500, warmup_ratio=0.001, step=[8, 11])
cfg.optimizer = dict(type='Adam', lr=0.0003, weight_decay=0.0001)

cfg.runner.type = 'EpochBasedRunner'

cfg.load_from = checkpoint
cfg.log_config.interval = 30
cfg.evaluation.metric = 'bbox'
cfg.evaluation.interval = 1
cfg.checkpoint_config.interval = 5
cfg.seed = seed
set_random_seed(seed, deterministic=False)
cfg.gpu_ids = range(1)

cfg.evaluation.classwise = True # 클래스별 mAp 출력 여부
cfg.device='cuda'
# print(f'Config:\n{cfg.pretty_text}')

with open(f'./MMD({condition}_{image_size}).py', 'w') as f:
  f.write(cfg.pretty_text)

condition = 'yolox'

!mkdir checkpoints

!wget -c https://download.openmmlab.com/mmdetection/v2.0/yolox/yolox_s_8x8_300e_coco/yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth \
      -O checkpoints/yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth


config = 'configs/yolox/yolox_s_8x8_300e_coco.py'
checkpoint = './checkpoints/yolox_s_8x8_300e_coco_20211121_095711-4592a793.pth'

!sed -i 's/img_scale = (640, 640)/img_scale = (512, 512)/' configs/yolox/yolox_s_8x8_300e_coco.py

#@title MMD_Config yolo
import mmdet
import mmcv
from mmcv import Config
from mmdet.apis import set_random_seed
import os.path as osp

cfg = Config.fromfile(config)

cfg.runner.max_epochs = 30 #@param {type:"integer"}

# 라벨 목록
classes = (
    'Aortic enlargement',
    'Atelectasis',
    'Calcification',
    'Cardiomegaly',
    'Consolidation',
    'ILD',
    'Infiltration',
    'Lung Opacity',
    'Nodule/Mass',
    'Other lesion',
    'Pleural effusion',
    'Pleural thickening',
    'Pneumothorax',
    'Pulmonary fibrosis'
    )

# 데이터셋 경로
base_path = '/content/data'

# cocoformat.json 파일 경로
train_anno = 'train_annotations.json'
test_anno = 'valid_annotations.json'

# 이미지파일 경로
test_img =  'train'
train_img = 'train'

# 저장경로(?)
# save_dir = '/content/drive/MyDrive/Inference'
save_dir = 'work_dir'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
cfg.work_dir = save_dir

# 모델별 cfg 수정
# ==================================================
cfg.dataset_type = 'CocoDataset'
cfg.data_root = base_path

if condition.startswith('yolo'):
  cfg.data.train.dataset.data_root = base_path
  cfg.data.train.dataset.ann_file = train_anno
  cfg.data.train.dataset.img_prefix = train_img
  cfg.data.train.dataset.classes = classes
  cfg.model.bbox_head.num_classes = 14


cfg.data.test.type = 'CocoDataset'
cfg.data.test.data_root = base_path
cfg.data.test.ann_file = test_anno
cfg.data.test.img_prefix = test_img

cfg.data.val.type = 'CocoDataset'
cfg.data.val.data_root = base_path
cfg.data.val.ann_file = test_anno
cfg.data.val.img_prefix = test_img

cfg.data.samples_per_gpu = 16 #@param {type:"integer"}
cfg.data.workers_per_gpu = 2

cfg.data.val.classes = classes
cfg.data.test.classes = classes

# 옵티마이저 설정
cfg.lr_config.warmup = None
cfg.lr_config = dict(policy='step', warmup='linear', warmup_iters=500, warmup_ratio=0.001, step=[8, 11])
cfg.optimizer = dict(type='Adam', lr=0.0003, weight_decay=0.0001)

cfg.runner.type = 'EpochBasedRunner'

cfg.load_from = checkpoint
cfg.log_config.interval = 30
cfg.evaluation.metric = 'bbox'
cfg.evaluation.interval = 1
cfg.checkpoint_config.interval = 5
cfg.seed = seed
set_random_seed(seed, deterministic=False)
cfg.gpu_ids = range(1)

cfg.evaluation.classwise = True # 클래스별 mAp 출력 여부
cfg.device='cuda'
# print(f'Config:\n{cfg.pretty_text}')

with open(f'./MMD({condition}_{image_size}).py', 'w') as f:
  f.write(cfg.pretty_text)



#@title MMD_Train

from mmdet.datasets import build_dataset
from mmdet.models import build_detector
from mmdet.apis import train_detector

# Build dataset
datasets = [build_dataset(cfg.data.train)]

# Build the detector
model = build_detector(
    cfg.model, train_cfg=cfg.get('train_cfg'), test_cfg=cfg.get('test_cfg'))
# Add an attribute for visualization convenience
model.CLASSES = datasets[0].CLASSES

# Create work_dir
mmcv.mkdir_or_exist(osp.abspath(cfg.work_dir))
train_detector(model, datasets, cfg, distributed=False, validate=True)

"""### MMD_Inference & Save"""

model.cfg = cfg

df_test_meta = pd.read_csv('/content/drive/MyDrive/test_meta.csv')

from mmdet.apis import inference_detector

test_file = glob('/content/data/test/*.png')

score_threshold = 0.5
results = []

def format_prediction_string(labels, boxes, scores, x, y):
    pred_strings = []
    px = x/image_size
    py = y/image_size
    for j in zip(labels, scores, boxes):
        pred_strings.append("{0} {1:.4f} {2} {3} {4} {5}".format(
            j[0], j[1], j[2][0]*px, j[2][1]*py, j[2][2]*px, j[2][3]*py))
    return " ".join(pred_strings)

for index, img_path in tqdm(enumerate(test_file), total = len(test_file)):
    image_id = img_path.split("/")[-1].split(".")[0]
    # image_id = image_id.split('_')[0]
    # file_name = img_path.split("/")[-1].split(".")[0]+".png"
    
    result = {
        'image_id': image_id,
        'PredictionString': '14 1 0 0 1 1'
    }
    img = mmcv.imread(img_path)

    predictions = inference_detector(model, img)
    boxes, scores, labels = (list(), list(), list())

    for k, cls_result in enumerate(predictions):
        if cls_result.size != 0:
            if len(labels)==0:
                boxes = np.array(cls_result[:, :4])
                scores = np.array(cls_result[:, 4])
                labels = np.array([k + 1]*len(cls_result[:, 4]))
            else:
                boxes = np.concatenate((boxes, np.array(cls_result[:, :4])))
                scores = np.concatenate((scores, np.array(cls_result[:, 4])))
                labels = np.concatenate((labels, [k + 1]*len(cls_result[:, 4])))

    if len(labels) != 0:
        # 라벨 -1 씩 SHIFT
        labels = labels - 1
        # no finding 이 -1에서 14로 이동!
        labels[labels == -1] = 14

        indexes = np.where(scores > score_threshold)
        boxes = boxes[indexes]
        scores = scores[indexes]
        labels = labels[indexes]
        
        if len(boxes) > 0:

          temp = df_test_meta[df_test_meta['image_id'] == image_id].values
          xx = temp[0][1]
          yy = temp[0][2]
          result = {
              'image_id': image_id,
              'PredictionString': format_prediction_string(labels, boxes, scores, xx, yy)
          }
    results.append(result)

submission = pd.DataFrame(results)
submission

# Commented out IPython magic to ensure Python compatibility.
# %pwd

submission.to_csv('sub.csv')

#@title MMD_File Save

submission.to_csv(f'/content/drive/MyDrive/Inference/MMD({condition}_{image_size}).csv', index=False)
shutil.copy(f'MMD({condition}_{image_size}).py', '/content/drive/MyDrive/Data/')

for i in os.listdir('./work_dir'):
  if i.startswith('best'):
    shutil.copy(f'./work_dir/{i}', '/content/drive/MyDrive/Data/')
    break

