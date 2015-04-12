#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sqlite3
import os
from collections import Counter
import re
import numpy as np
import scipy.stats as sp
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
from sklearn import svm
from sklearn import neighbors
from sklearn.feature_extraction import DictVectorizer
from sklearn.cross_validation import train_test_split
import scipy.cluster.hierarchy as sch

import pdb


max_time = {'': 600, 'sb': 180, 's1': 10}


def l1_normalize(v):
    return (v / v.sum().astype(float))


def extract_kifu(kifu):
    u'''データベースの一部を受け取って特徴量などを抽出してlistにして返す．
    '''
    df_csa = pd.DataFrame(kifu[u'csa'].split('\n'))

    data_marged = []
    for move in [0, 1]:
        start = move * 2
        time_str_col = df_csa.ix[np.arange(start + 21, df_csa.shape[0], 4)]
        time_list = time_str_col[0].str.replace('T', '').astype(float).values
        n_bins = max_time[gtype] + 2  # 0秒目とbin用で +2
        not_normalized = np.histogram(time_list, bins=range(n_bins))[0]

        if len(time_list) == 0:
            return []

        sente_win = kifu['wcsa'].find('SENTE') > 0
        gote_win = kifu['wcsa'].find('GOTE') > 0

        if (not sente_win) and (not gote_win):
            win = -1
        else:
            if move == 0:
                win = int(sente_win)
            else:
                win = int(gote_win)

        if len(time_list) <= 1:
            return None

        first_ctime = time_list[start + 1]
        first_move = df_csa.ix[start+20, 0]
        data_list = [kifu['datetime'], kifu['user' + str(move)],
                     kifu['dan' + str(move)], move, first_ctime, first_move,
                     win]
        data_list.extend(list(l1_normalize(not_normalized)))
        data_marged.append(data_list)

    return data_marged

if __name__ == '__main__':

    # Connect to SQLite
    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')
    con = sqlite3.connect(dbpath)

    gtype = ''
    query = 'SELECT * FROM kifu WHERE gtype="{0}";'.format(gtype)
    df_kifu = pd.read_sql(query, con)

    data_list = []
    for n, kifu in df_kifu.T.to_dict().items():
        retval = extract_kifu(kifu)
        if retval:
            data_list.extend(retval)

    columns = [u'datetime', u'user', u'dan',
               u'move', u'first_ctime', u'first_move', u'win?']
    t_length = max_time[gtype] + 1
    columns.extend(map(lambda time: 't' + str(time), range(t_length)))

    feature_value = pd.DataFrame(data_list, columns=columns)
    feature_value.ix[:, 7:].T.plot(legend=False)

    X = feature_value.ix[:, 7:]
    y = feature_value.ix[:, 'user']

    # train, testに分割する
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # predict by k-NN
    accuracy_rate_list = []
    k_list = range(1, 30)
    for k in k_list:
        clf = neighbors.KNeighborsClassifier(k)
        clf.fit(X_train, y_train)
        y_predict = clf.predict(X_test)

        accuracy_rate = (y_predict == np.array(y_test)).mean()
        accuracy_rate_list.append(accuracy_rate)

        print('\nCorrect rate({0}-NN): {1}'.format(k, accuracy_rate))

    plt.plot(k_list, accuracy_rate_list)


    ## 階層型クラスタリング
    res_linkage = sch.linkage(np.array(X), method='average')

    plt.figure(figsize=(6,12*X.shape[0]/100))
    plt.subplots_adjust(left=0.1, right=0.8)
    sch.dendrogram(res_linkage, labels=list(y), orientation='right')
    plt.savefig('dendrogram.pdf')
