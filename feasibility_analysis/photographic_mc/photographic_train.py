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
    Embedding
)
from tensorflow.keras.optimizers import Adam


util_dir = Path.cwd().parent.joinpath('util')
sys.path.insert(1, str(util_dir))
from extractor_config import Config
from mu2e_output import *
from loss import *
from metric import *
### import ends

def photographic_train(C):
    pstage("Start Training")

    ### load inputs
    pinfo('Loading processed arrays')
    X = np.load(C.X_npy)
    Y = np.load(C.Y_npy)

    pinfo('Standarlizing the input array')
    X = (X-X.mean())/X.std()

    pinfo('Flattening the output array')

    
    ### outputs
    pinfo('Configuring output paths')
    cwd = Path.cwd()
    data_dir = cwd.parent.parent.joinpath('data')
    weights_dir = cwd.parent.parent.joinpath('weights')

    model_weights = weights_dir.joinpath(C.model_name+'.h5')
    record_file = data_dir.joinpath(C.record_name+'.csv')

    ### build the model
    input_layer = Input(shape=(X.shape[1], X.shape[2], 1))
    x = Conv2D(128, (3, 3), padding='same', activation='relu', kernel_initializer=initializers.RandomNormal(stddev=0.01), kernel_regularizer=regularizers.l2(1e-8))(input_layer)
    x = MaxPool2D(pool_size=(2, 2), padding='same')(x)
    x = Dropout(0.3)(x)


    x = Conv2D(256, (3, 3), padding='same', activation='relu', kernel_initializer=initializers.RandomNormal(stddev=0.01), kernel_regularizer=regularizers.l2(1e-8))(x)
    x = MaxPool2D(pool_size=(2, 2), padding='same')(x)
    x = Dropout(0.3)(x)


    x = Conv2D(512, (3, 3), padding='same', activation='relu', kernel_initializer=initializers.RandomNormal(stddev=0.01), kernel_regularizer=regularizers.l2(1e-8))(x)
    x = MaxPool2D(pool_size=(2, 2), padding='same')(x)
    x = Dropout(0.3)(x)

    x = Conv2D(512, (3, 3), padding='same', activation='relu', kernel_initializer=initializers.RandomNormal(stddev=0.01), kernel_regularizer=regularizers.l2(1e-8))(x)
    x = BatchNormalization()(x)
    x = MaxPool2D(pool_size=(2, 2), padding='same')(x)
    x = Dropout(0.3)(x)

    x = Flatten()(x)

    output_layer = Dense(Y.shape[1], activation='sigmoid')(x)
    model = Model(inputs=input_layer, outputs=output_layer)

    # setup loss
    unmasked_bce = define_rpn_class_loss(1)

    # setup optimizer
    adam = Adam(1e-3)

    # setup callback
    CsvCallback = tf.keras.callbacks.CSVLogger(str(record_file), separator=",", append=False)
    LRCallback = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='loss', factor=0.1, patience=10, verbose=0, mode='auto',
        min_delta=1e-6, cooldown=0, min_lr=1e-7
    )
    # print(cnn.summary())
    model.compile(optimizer=adam,\
                loss=unmasked_bce,\
                metrics=[unmasked_accuracy, positive_number])

    model.fit(x=X, y=Y,\
            validation_split=0.2,\
            shuffle=True,\
            batch_size=32, epochs=1000,\
            callbacks = [CsvCallback, LRCallback])

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
    model_name = "photographic_00"
    record_name = "photographic_record_00"

    # setup parameters
    C.set_outputs(model_name, record_name)
    photographic_train(C)
