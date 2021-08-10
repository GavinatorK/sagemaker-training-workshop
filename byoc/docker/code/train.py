from __future__ import absolute_import
from fastai.vision.all import *
from fastai.metrics import error_rate, accuracy
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
# Set path to root directory
import argparse
import os
import sys
import time
from utils import print_files_in_path, save_model_artifacts


def train(lr, train_channel):
    
    path = Path(os.environ["SM_CHANNEL_TRAIN"])
    dblock = DataBlock(blocks = (ImageBlock, CategoryBlock),
               get_items = get_image_files,
               splitter = GrandparentSplitter(),
               get_y = parent_label)
    
    
    dls=dblock.dataloaders(path)
    
    print(dls.vocab)
    # Dummy net.
    net=cnn_learner(dls,resnet50,metrics=error_rate)
    

    # Run training loop.
    net.fit_one_cycle(5, 1e-03)

    # At the end of the training loop, we have to save model artifacts.
    model_dir = os.environ["SM_MODEL_DIR"]
    net.export(model_dir + "/export.pkl")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # sagemaker-containers passes hyperparameters as arguments
    parser.add_argument("--lr", type=float, default=9e-03)

    # This is a way to pass additional arguments when running as a script
    # and use sagemaker-containers defaults to set their values when not specified.
    parser.add_argument("--train", type=str, default=os.environ["SM_CHANNEL_TRAIN"])

    args = parser.parse_args()

    train(args.lr, args.train)