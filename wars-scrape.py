#!/usr/bin/env python
# -*- coding: utf-8 -*-

##--------------------------------------------------------------##
## Filename: wars-an.py
## Author  : tosh1ki
## E-mail  : tosh1ki@yahoo.co.jp
## Outline : 将棋ウォーズの棋譜取得,DB登録プログラム
## Since   : 2014-10-24
##--------------------------------------------------------------##

import sys
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import time
import datetime as dt
import pymongo


INTERVAL_TIME = 5
WCSA_PATTERN = re.compile(r'(?<=receiveMove\(\").+(?=\"\);)')
GAME_HEADER_PATTERN = re.compile(r'(?<=var\sgamedata\s=\s){.+?}', re.DOTALL)


def get_html(url):
    time.sleep(INTERVAL_TIME)

    response = urllib2.urlopen(url)
    html = response.read()
    response.close()

    return html

def get_url_list(user, gtype='', max_iter=10):
    u''' 指定したユーザーの棋譜を取得する．

    Parameters
    ----------
    user
        User name (string)
    gtype
        Kifu type (string)
        example
            ''   : 10 min. (default)
            'sb' :  3 min. (bullet mode)
            's1' : 10 sec.
    max_iter
        取得する最大数．10個ずつ取得するたびに判定しているので10個弱はずれる．

    Example
    ----------
    >>> username = '1_tsutsukana'
    >>> url_list = get_url_list(username)
    >>> len(url_list)>0
    True
    '''

    base_url = 'http://shogiwars.heroz.jp/users/history/'
    url_list = []
    start = 1

    while True:
        url = ''.join([base_url,user, 
                       '?gtype=', str(gtype), 
                       '&start=', str(start)])

        html = get_html(url)
        soup = BeautifulSoup(html)
        url_list_tmp = [div.a['href'] 
                        for div in soup('div', {'class':'short_btn1'})]

        ## listが空のとき
        if not url_list_tmp :
            break

        url_list.extend(url_list_tmp)
        start += 10
        
        if start > max_iter:
            break 

    return url_list


def wcsa_to_csa(wars_csa, gtype):
    u''' 将棋ウォーズ専用?のCSA形式を一般のCSA形式に変換する．

    Parameters
    ----------
    wars_csa : 
        将棋ウォーズ特有のCSA形式で表された棋譜の文字列
    gtype : 
        処理したい棋譜のgtype
    '''

    wcsa_list = re.split(r'[,\t]', wars_csa)

    if gtype == '': 
        max_time = 60*10
    elif gtype == 'sb': 
        max_time = 60*3
    elif gtype == 's1': 
        max_time = 3600
    else: 
        print 'Error: gtypeに不正な値; gtype={0}'.format(gtype)

    sente_prev_remain_time = max_time
    gote_prev_remain_time = max_time

    results = []

    for i,w in enumerate(wcsa_list):
        if i%2==0:
            ## 駒の動き，あるいは特殊な命令の処理
            ## CAUTION: 仕様がわからないので全部網羅できているかわからない
            if w.find('TORYO') > 0:
                w_ap = '%TORYO'
            elif w.find('TIMEOUT') > 0:
                w_ap = '%TIME_UP'
            else:
                w_ap = w

            results.append(w_ap)

        else:
            if (i-1)%4==0:
                ## 先手の残り時間を計算
                sente_remain_time = int(w[1:])
                _time = sente_prev_remain_time - sente_remain_time
                sente_prev_remain_time = sente_remain_time
            else: 
                ## 後手の残り時間を計算
                gote_remain_time = int(w[1:])
                _time = gote_prev_remain_time - gote_remain_time
                gote_prev_remain_time = gote_remain_time

            results.append('T' + str(_time))

    return '\n'.join(results)


def url_to_kifudata(url):
    u''' urlが指す棋譜とそれに関する情報を辞書にまとめて返す．

    CAUTION : 明示されていない棋譜ページの仕様に依存しているので，
    そのうち使えなくなる可能性がある．
    '''
    html = get_html(url)
    
    ## 対局に関するデータの取得
    res = re.findall(GAME_HEADER_PATTERN, html)[0]
    _dict = eval(re.sub(r'\n\t\t(?P<key>\w+)(?=:)','"\g<key>"', res))
    _dict['user0'], _dict['user1'], _dict['date'] = _dict['name'].split('-')

    ## 棋譜の取得
    wars_csa = re.findall(WCSA_PATTERN, html)[0]
    _dict['csa'] = wcsa_to_csa(wars_csa, _dict['gtype'])

    ## 時刻オブジェクトの生成
    _dict['datetime'] = dt.datetime.strptime(_dict['date'], '%Y%m%d_%H%M%S')

    _dict['_id'] = _dict.pop('name')

    return _dict


def connect_mongodb():
    u''' MongoDBに接続
    '''
    connection = pymongo.Connection('localhost',27017)
    db = connection.warskifu
    return db.kifu


def append_mongodb(url_list, reflesh=False):
    u''' url_list 中の url の指す棋譜を取得してCSA形式に変換，mongoDBに追加．
    '''

    id_pattern = re.compile(r'\w+-\w+-\w+')

    ## connect to mongoDB
    col = connect_mongodb()

    n_list = len(url_list)
    sec = n_list * INTERVAL_TIME
    finish_time = dt.datetime.now() + dt.timedelta(seconds=sec)

    print '{0}件の棋譜'.format(n_list)
    print '棋譜収集終了予定時刻 : {0}'.format(finish_time)
    sys.stdout.flush()

    for _url in url_list:
        _id = re.findall(id_pattern, _url)[0]

        ## DB 内にあって，かつrefleshがfalseのときはcontinueする
        if col.find({u'_id':_id}).count() > 0 and not reflesh:
            continue

        kifu_dict = url_to_kifudata(_url)
        col.insert(kifu_dict)


def set_kif_to_db(username, gtype='', max_iter=10):
    ## 棋譜のurlのリストを取得
    url_list = get_url_list(username, gtype=gtype, max_iter=max_iter)

    ## mongoDB に追加
    append_mongodb(url_list)
    

if __name__ == '__main__':

    ## Example
    username = '1_tsutsukana'
    gtype = 's1'
    max_iter = 10000

    set_kif_to_db(username, gtype=gtype, max_iter=10000)

