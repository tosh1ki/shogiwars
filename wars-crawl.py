#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
import sys
import time
import sqlite3
import requests
import datetime as dt
import pandas as pd
from bs4 import BeautifulSoup


INTERVAL_TIME = 5
MAX_N_RETRY = 10
WCSA_PATTERN = re.compile(r'(?<=receiveMove\(\").+(?=\"\);)')
GAME_HEADER_PATTERN = re.compile(r'(?<=var\sgamedata\s=\s){.+?}', re.DOTALL)
SUB_PATTERN = re.compile(r'\n\t\t(?P<key>\w+)(?=:)')


def get_session(url, params={}):

    time.sleep(INTERVAL_TIME)

    for n in range(MAX_N_RETRY):
        res = requests.session().get(url, params=params)

        if res.status_code == 200:
            return res

        print('retry (get_session)')
        time.sleep(10 * n * INTERVAL_TIME)
    else:
        sys.exit('Exceeded MAX_N_RETRY (get_sesion())')


def connect_sqlite(filepath):
    con = sqlite3.connect(filepath)
    con.text_factory = str
    return con


def get_url_list(user, gtype, max_iter=10):
    u''' 指定したユーザーの棋譜を取得する．

    Parameters
    ----------
    user
        User name (string)
    gtype
        Kifu type (string)
    max_iter
        取得する最大数．
        10個ずつ取得するたびに判定しており厳密には守るつもりはない．
    '''

    base_url = 'http://shogiwars.heroz.jp/users/history/'
    url_list = []
    start = 1

    while True:
        url = ''.join([base_url, user,
                       '?gtype=', str(gtype),
                       '&start=', str(start)])

        text = get_session(url).text
        pattern = 'http://shogiwars.heroz.jp:3002/games/[\w\d_-]+'
        match = re.findall(pattern, text)

        # listが空のとき
        if not match:
            break

        url_list.extend(match)
        start += 10

        if start > max_iter:
            break

    return url_list


def wcsa_to_csa(wars_csa, gtype):
    u''' 将棋ウォーズ専用?のCSA形式を一般のCSA形式に変換する．

    Parameters
    ----------
    wars_csa
        将棋ウォーズ特有のCSA形式で表された棋譜の文字列
    gtype
        処理したい棋譜のgtype
    '''

    wcsa_list = re.split(r'[,\t]', wars_csa)

    # 1手も指さずに時間切れ or 接続切れ or 投了
    if (wars_csa == '\tGOTE_WIN_TIMEOUT' or
        wars_csa == '\tGOTE_WIN_DISCONNECT' or
        wars_csa == '\tGOTE_WIN_TORYO'):
        return '%TIME_UP'

    if gtype == '':
        max_time = 60 * 10
    elif gtype == 'sb':
        max_time = 60 * 3
    elif gtype == 's1':
        max_time = 3600
    else:
        print('Error: gtypeに不正な値; gtype={0}'.format(gtype))

    sente_prev_remain_time = max_time
    gote_prev_remain_time = max_time

    results = []

    for i, w in enumerate(wcsa_list):
        if i % 2 == 0:
            # 駒の動き，あるいは特殊な命令の処理
            # CAUTION: 仕様がわからないので全部網羅できているかわからない
            if w.find('TORYO') > 0 or w.find('DISCONNECT') > 0:
                w_ap = '%TORYO'
            elif w.find('TIMEOUT') > 0:
                w_ap = '%TIME_UP'
            elif w.find('DRAW_SENNICHI') > 0:
                w_ap = '%SENNICHITE'
            else:
                w_ap = w

            results.append(w_ap)

        else:
            if (i - 1) % 4 == 0:
                # 先手の残り時間を計算
                sente_remain_time = int(w[1:])
                _time = sente_prev_remain_time - sente_remain_time
                sente_prev_remain_time = sente_remain_time
            else:
                # 後手の残り時間を計算
                gote_remain_time = int(w[1:])
                _time = gote_prev_remain_time - gote_remain_time
                gote_prev_remain_time = gote_remain_time

            results.append('T' + str(_time))

    return '\n'.join(results)


def url_to_kifudata(url):
    ''' urlが指す棋譜とそれに関する情報を辞書にまとめて返す．
    '''
    html = get_session(url).text

    # 対局に関するデータの取得
    res = re.findall(GAME_HEADER_PATTERN, html)[0]
    _dict = eval(re.sub(SUB_PATTERN, '"\g<key>"', res))
    _dict['user0'], _dict['user1'], _dict['date'] = _dict['name'].split('-')

    # 棋譜の取得
    wars_csa = re.findall(WCSA_PATTERN, html)[0]
    _dict['csa'] = wcsa_to_csa(wars_csa, _dict['gtype'])

    _dict['datetime'] = dt.datetime.strptime(_dict['date'], '%Y%m%d_%H%M%S')
    _dict['_id'] = _dict.pop('name')
    _dict['wcsa'] = wars_csa

    return _dict


def append_to_sqlite(url_list, dbpath, reflesh=False):
    ''' url_list 中の url の指す棋譜を取得してCSA形式に変換，mongoDBに追加．
    '''

    id_pattern = re.compile(r'\w+-\w+-\w+')

    # connect to SQLite
    con = connect_sqlite(dbpath)

    n_list = len(url_list)
    sec = n_list * INTERVAL_TIME
    finish_time = dt.datetime.now() + dt.timedelta(seconds=sec)

    print('{0}件の棋譜'.format(n_list))
    print('棋譜収集終了予定時刻 : {0}'.format(finish_time))
    sys.stdout.flush()

    ret_list = []

    for _url in url_list:
        # _url が空の場合はcontinue
        if not _url:
            continue

        _id = re.findall(id_pattern, _url)[0]

        # DB 内にあって，かつrefleshがfalseのときはcontinueする
        # if not pd.read_csv('SELECT * FROM kifu WHERE _id=='+_id, con).empty
        # and not reflesh:
        #     continue

        ret_list.append(url_to_kifudata(_url))

    df = pd.DataFrame(ret_list)
    if not df.empty:
        df.to_sql('kifu', con, index=False, if_exists='append')


def set_kif_to_db(dbpath, username, gtype='', max_iter=10):
    ''' 指定したユーザーの最近の棋譜をSQLiteに追加する．

    Example
    ----------
    >>> username = '1_tsutsukana'
    >>> gtype = 's1'
    >>> max_iter = 10000

    >>> set_kif_to_db(username, gtype=gtype, max_iter=10)
    '''
    # 棋譜のurlのリストを取得
    url_list = get_url_list(username, gtype=gtype, max_iter=max_iter)

    append_to_sqlite(url_list, dbpath)


def get_tournament_users(title, max_page=10):
    '''大会名を指定して，その大会の上位ユーザーのidを取ってくる

    Examples
    ----------
    将棋ウォーズ第4回名人戦に参加しているユーザーのidを取得する．
    >>> get_tournament_users('meijin4', max_page=100)
    '''

    page = 0
    base_url = 'http://shogiwars.heroz.jp/events/'
    results = []

    while True:
        url = ''.join([base_url, title, '?start=', str(page)])
        html = get_session(url).text
        _users = re.findall(r'\/users\/(\w+)', html)

        # _usersが空でない場合追加．そうでなければbreak
        if _users:
            results.extend(_users)
            page += 25
        else:
            break

        if page >= max_page:
            break

    return results

if __name__ == '__main__':

    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')

    # 第4回名人戦で1〜100位になったプレーヤーの棋譜を取得する．
    t_users = get_tournament_users('meijin4', max_page=10)

    for _user in t_users:
        set_kif_to_db(dbpath, _user, gtype='s1', max_iter=10)
