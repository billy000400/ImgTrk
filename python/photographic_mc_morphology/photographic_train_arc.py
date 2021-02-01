# This script's purpose is to train a preliminary CNN for tracking by Keras
# Author: Billy Li
# Email: li000400@umn.edu

# import starts
import sys
from pathlib import Path
import csv
import random
import pickle

import numpy as np

import tensorflow as tf
from tensorflow.keras import Model, initializers, regularizers
from tensorflow.keras.layers import(
    Input,
    Dense,
    Conv2D,
    BatchNormalization,
    MaxPool2D,Dropout,
    Flatten,
    TimeDistributed,
    Embedding,
    Reshape,
    Softmax
)
from tensorflow.keras.optimizers import Adam


util_dir = Path.cwd().parent.joinpath('util')
sys.path.insert(1, str(util_dir))
from Config import extractor_config as Config
from DataGenerator import DataGenerator as Generator
from Architecture import U_Net_Like
from mu2e_output import *
from Loss import *
from Metric import *
### import ends

def photographic_train(C):
    pstage("Start Training")

    ### outputs
    pinfo('Configuring output paths')
    cwd = Path.cwd()
    data_dir = cwd.parent.parent.joinpath('data')
    weights_dir = cwd.parent.parent.joinpath('weights')

    model_weights = weights_dir.joinpath(C.model_name+'.h5')
    record_file = data_dir.joinpath(C.record_name+'.csv')

    input_shape = (160, 240, 1)
    architecture = U_Net_Like(input_shape, 3)
    model = architecture.get_model()
    model.summary()

    # setup loss
    weights = [1, 1.62058132, 1.13653004e-03]
    cce = categorical_focal_loss(alpha=weights, gamma=2)

    # setup metric
    ca = top2_categorical_accuracy

    # setup optimizer
    adam = Adam(1e-4)

    # setup callback
    CsvCallback = tf.keras.callbacks.CSVLogger(str(record_file), separator=",", append=False)
    LRCallback = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='loss', factor=0.1, patience=3, verbose=0, mode='auto',
        min_delta=1e-6, cooldown=0, min_lr=1e-7
    )
    # print(cnn.summary())
    model.compile(optimizer=adam,\
                metrics = ca,\
                loss=cce)

    cwd = Path.cwd()
    data_dir = cwd.parent.parent.joinpath('data')
    morph_dir = data_dir.joinpath('photographic_morphology')
    train_dir = morph_dir.joinpath('Arc_train')
    val_dir = morph_dir.joinpath('Arc_val')
    X_train_dir = train_dir.joinpath('X')
    Y_train_dir = train_dir.joinpath('Y')
    X_val_dir = val_dir.joinpath('X')
    Y_val_dir = val_dir.joinpath('Y')


    train_generator = Generator(X_train_dir, Y_train_dir, batch_size=1)
    val_generator = Generator(X_val_dir, Y_val_dir, batch_size=1)

    model.fit(x=train_generator,\
            shuffle=True,\
            validation_data=val_generator,\
            callbacks = [CsvCallback, LRCallback],\
            use_multiprocessing=True,\
            workers=4,\
            epochs=40)
    model.save(model_weights)

    pcheck_point('Finished Training')
    return C


if __name__ == "__main__":
    pbanner()
    psystem('Photographic track extractor')
    pmode('Testing Feasibility')
    pinfo('Input DType for testing: StrawDigiMC')

    # load pickle
    cwd = Path.cwd()
    pickle_path = cwd.joinpath('photographic.train.config.pickle')
    C = pickle.load(open(pickle_path,'rb'))

    # initialize parameters
    model_name = "photographic_mc_arc_00"
    record_name = "photographic_record_mc_arc_00"

    # setup parameters
    C.set_outputs(model_name, record_name)
    photographic_train(C)
