import numpy as np
import random
import logging

from tensorflow import keras
from keras import backend as K
from tensorflow.keras.optimizers import SGD
import tensorflow as tf

from Utils import HSphereSMOTE

from sklearn.utils import shuffle

def train(x_train, y_train, x_test, y_test, batch_size, train_batch_size, epochs):
    K.clear_session()

    result = np.where(y_train == 1)
    attack_idx = result[0]
    result = np.where(y_train == 0)
    normal_idx = result[0]

    selected_attack = random.choices(attack_idx, k=round(train_batch_size * 0.3))
    selected_normal = random.choices(normal_idx, k=round(train_batch_size * 0.9))

    input_attack = [x_train[i] for i in selected_attack]
    labels_attack = [y_train[i] for i in selected_attack]

    input_normal = [x_train[i] for i in selected_normal]
    labels_normal = [y_train[i] for i in selected_normal]
    
    x_train_client = [*input_attack, *input_normal]
    y_train_client = [*labels_attack, *labels_normal]

    x_train_client = np.asarray(x_train_client)
    y_train_client = np.asarray(y_train_client)

    xsyn, ysyn, nls, n0, n1 = HSphereSMOTE.Sampling(x_train_client, y_train_client, ratio=0.9, k=20)
    xsyn = xsyn.numpy()
    ysyn = ysyn.numpy()

    logging.info("Data Shape Before HSphere: X_Train: " + str(x_train_client.shape) + " Y_Train: " + str(y_train_client.shape))
    x_train_client = np.concatenate([x_train_client, xsyn])
    y_train_client = np.concatenate([y_train_client, ysyn])
    logging.info("Data Shape After HSphere: X_Train: " + str(x_train_client.shape) + " Y_Train: " + str(y_train_client.shape))

    input_dim = x_train.shape[1]

    x_train = np.asarray(x_train)
    y_train = np.asarray(y_train)

    x_test = np.asarray(x_test)
    y_test = np.asarray(y_test)
    
    optimizer = SGD(learning_rate=0.01, decay=0.01 / 100, momentum=0.9) 

    model = keras.Sequential([
            keras.layers.Dense(150, input_shape = (input_dim,), activation = 'relu'), 
            keras.layers.Dense(50, activation = 'relu'),
            keras.layers.Dense(1, activation = 'sigmoid')
            ])

    model.compile(optimizer=optimizer,
                    loss='binary_crossentropy',
                    metrics=['accuracy'])

    model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=False, validation_data=(x_test, y_test))
    train_loss, train_accuracy = model.evaluate(x_test, y_test, verbose=False)

    logging.info('Local Model Training Done | Accuracy: {:.3%} | Loss: {:.4f}'.format(train_accuracy, train_loss))        

    weights = model.get_weights()

    return weights

def test(global_weights, x_test, y_test):
    K.clear_session()

    x_test = np.asarray(x_test)
    y_test = np.asarray(y_test)

    input_dim = x_test.shape[1]

    optimizer = SGD(learning_rate=0.01, decay=0.01 / 100, momentum=0.9) 

    model = keras.Sequential([
            keras.layers.Dense(150, input_shape = (input_dim,), activation = 'relu'), 
            keras.layers.Dense(50, activation = 'relu'),
            keras.layers.Dense(1, activation = 'sigmoid')
            ])

    model.compile(optimizer=optimizer,
                    loss='binary_crossentropy',
                    metrics=['accuracy'])

    model.set_weights(global_weights)

    test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=False)

    logging.info('Global Model Testing Done | Accuracy: {:.3%} | Loss: {:.4f}'.format(test_accuracy, test_loss))        