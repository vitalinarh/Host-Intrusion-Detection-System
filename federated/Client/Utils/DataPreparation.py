import numpy as np
import os, random, glob

from sklearn.utils import shuffle
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

# Paths
rootpath = "Datasets/ADFA-LD"
attack_data_master = rootpath + "/Attack_Data_Master"
training_data_master = rootpath + "/Training_Data_Master"
validation_data_master = rootpath + "/Validation_Data_Master"
test_data_master = rootpath + "/Validation_Data_Master"
processed_root = rootpath + "/Processed"

def get_data():
    ''' function for reading data from local database
    return:
        x_train, y_train, x_test, y_test dataframes'''

    sentence_length = 30
    main_corpus_x = []
    main_corpus_y = []

    malCOUNT = 0
    benCOUNT = 0

    nGRAM1 = 2
    nGRAM2 = 2
    weight = 10

    for folder in os.listdir(attack_data_master): # iterate through all label folders in the directory
        for filename in glob.glob(os.path.join(attack_data_master + '/' + folder, '*.txt')):
            fMAL = open(filename, "r")
            fMAL = fMAL.readlines()
            fMAL = fMAL[0].split()
            for i in range(len(fMAL) - sentence_length):
                line = ' '.join(fMAL[i:i+sentence_length])
                main_corpus_x.append(line)
                main_corpus_y.append(1)
                malCOUNT += 1

    for filename in glob.glob(os.path.join(training_data_master, '*.txt')):
        fBEN = open(filename, "r")
        fBEN = fBEN.readlines()
        fBEN = fBEN[0].split()
        for i in range(len(fBEN)):
            line = ' '.join(fBEN[i:i+sentence_length])
            main_corpus_x.append(line)
            main_corpus_y.append(0)
            benCOUNT += 1

    # shuffling the dataset
    main_corpus_y, main_corpus_x = shuffle(main_corpus_y, main_corpus_x, random_state=0)

    # weight as determined in the top of the code
    train_corpus = main_corpus_x[:(weight * len(main_corpus_x)//(weight + 1))]
    y_train = main_corpus_y[:(weight * len(main_corpus_x)//(weight + 1))]
    test_corpus = main_corpus_x[(len(main_corpus_x) - (len(main_corpus_x)//(weight + 1))):]
    y_test = main_corpus_y[(len(main_corpus_x) - len(main_corpus_x)//(weight + 1)):]

    vectorizer = TfidfVectorizer(ngram_range=(nGRAM1, nGRAM2), min_df=1, use_idf=True, smooth_idf=True) 

    X_train = vectorizer.fit_transform(train_corpus)
    X_test = vectorizer.transform(test_corpus)

    clf = TruncatedSVD(150)
    clf.fit(X_train)
    x_train = clf.transform(X_train)
    x_test = clf.transform(X_test)

    y_train = np.array(y_train)
    x_train = np.array(x_train)

    selected_normal = np.where(y_train == 0)
    selected_normal = selected_normal[0]
    size = round(len(selected_normal))

    attack_idx = np.where(y_train == 1)
    selected_attack = random.choices(attack_idx[0], k=size)

    input_attack = [x_train[i] for i in selected_attack]
    labels_attack = [y_train[i] for i in selected_attack]

    input_normal = [x_train[i] for i in selected_normal]
    labels_normal = [y_train[i] for i in selected_normal]

    train_input = [*input_attack, *input_normal]
    train_labels = [*labels_attack, *labels_normal]

    x_train = np.array(train_input)
    y_train = np.array(train_labels)
    x_test = np.array(x_test)
    y_test = np.array(y_test)

    return x_train, y_train, x_test, y_test
