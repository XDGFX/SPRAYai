#!/usr/bin/bash

./export_model.py \
--config-file ../../configs/dandelions_v3.yaml \
--output ./output \
--export-method caffe2_tracing \
--format torchscript \
MODEL.WEIGHTS ../../datasets/dandelions_v3/model_final.pth \
MODEL.DEVICE cuda