#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'tosh1ki'
__email__ = 'tosh1ki@yahoo.co.jp'
__date__ = '2014-11-07'

# identification.py :
# 将棋ウォーズの棋譜からユーザー同定を行う．棋譜を1つにまとめるver.

import pymongo
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
import scipy.cluster.hierarchy as sch

import pdb


def l1_normalize(v):
    return (v / v.sum().astype(float))


def extract_kifu(kifu):
    u'''データベースの一部を受け取って特徴量などを抽出してlistにして返す．
    '''
    df_csa = pd.DataFrame(kifu[u'csa'].split('\n'))

    data_marged = []
    for move in [0, 1]:
        start = move * 2
        time_str_col = df_csa.ix[np.arange(start + 1, df_csa.shape[0], 4)]
        time_list = time_str_col[0].str.replace('T', '').astype(float)
        not_normalized = np.histogram(time_list, bins=range(12))[0]

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

        first_ctime = time_list[start + 1]
        first_move = df_csa.ix[start, 0]
        data_list = [kifu['datetime'], kifu['user' + str(move)],
                     kifu['dan' + str(move)], move, first_ctime, first_move,
                     win]
        data_list.extend(list(l1_normalize(not_normalized)))
        data_marged.append(data_list)

    return data_marged

if __name__ == '__main__':

    # Connect to MongoDB
    connection = pymongo.Connection('localhost', 27017)
    db = connection.warskifu
    collection = db.kishin3

    data_list = []
    for n, kifu in enumerate(collection.find()):
        retval = extract_kifu(kifu)
        if retval:
            data_list.extend(retval)

    columns = [u'datetime', u'user', u'dan',
               u'move', u'first_ctime', u'first_move', u'win?']
    columns.extend(map(lambda time: 't' + str(time), range(11)))

    feature_value = pd.DataFrame(data_list, columns=columns)

    # first_moveから1-of-k符号化で特徴量を作る
    vec = DictVectorizer()
    df_dict = feature_value[[u'first_move', u'win?']].transpose().to_dict()
    move_dict = [d[1] for d in df_dict.iteritems()]
    fmove_array = vec.fit_transform(move_dict).toarray()[:, 0:55]
    fmove_df = pd.DataFrame(fmove_array,
                            index=feature_value.index,
                            columns=vec.get_feature_names()[0:-1])

    # その他の特徴量
    index = [4] + range(7, 18)
    some_fvalue = feature_value.ix[:, index]

    X = pd.concat([some_fvalue, fmove_df], axis=1)
    y = feature_value.ix[:, u'user']


    ## 10回以上現れるユーザーを探す
    counter = Counter(y)
    user_list = []
    for user, count in counter.most_common():
        if count > 10:
            print user, count
            user_list.append(user)

    index_10 = y.map(lambda x: x in user_list)

    train_index = index_10 & ( 
        feature_value.ix[:, u'datetime'] > dt.datetime(2014, 10, 23))
    test_index = index_10 & (
        feature_value.ix[:, u'datetime'] <=dt.datetime(2014, 10, 23))

    X_train = X.ix[train_index, :]
    y_train = y[train_index]
    X_test = X.ix[test_index, :]
    y_test = y[test_index]

    # predict by k-NN
    accuracy_rate_list = []
    k_list = range(1, 30)
    for k in k_list:
        clf = neighbors.KNeighborsClassifier(k)
        clf.fit(X_train, y_train)
        y_predict = clf.predict(X_test)

        accuracy_rate = (y_predict == np.array(y_test)).mean()
        accuracy_rate_list.append(accuracy_rate)

        print '\nCorrect rate({0}-NN): {1}'.format(k, accuracy_rate)

    plt.plot(k_list, accuracy_rate_list)


    ## 階層型クラスタリング
    index = range(3000)
    X_ = X.ix[index]
    y_ = y.ix[index]
    li = sch.linkage(np.array(X_))

    plt.figure(figsize=(6,12*len(index)/100))
    plt.subplots_adjust(left=0.1, right=0.8)
    sch.dendrogram(li, labels=list(y_), orientation='right')
    plt.savefig('dendrogram3000.pdf')
