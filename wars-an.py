#!/usr/bin/env python
# -*- coding: utf-8 -*-

##--------------------------------------------------------------##
## Author  : tosh1ki
## E-mail  : tosh1ki@yahoo.co.jp
## Outline : 将棋ウォーズの棋譜取得プログラム いずれは解析プログラムへ
## Since   : 2014-10-24
##--------------------------------------------------------------##


import urllib2
from BeautifulSoup import BeautifulSoup
import time
import pdb
import re
from datetime import datetime as dt

INTERVAL_TIME = 5
SWARS_URL_PATTERN = re.compile(r'(?:http\:\/\/shogiwars\.heroz\.jp\:3002\/games\/)(?P<sente>\w+)-(?P<gote>\w+)-(?P<date>[0-9_]+)')


def get_html(url):
    time.sleep(INTERVAL_TIME)

    response = urllib2.urlopen(url)
    html = response.read()
    response.close()

    return html

def get_url_list(user, gtype='', start=1):
    u''' 指定したユーザーの棋譜を取得する．

    Parameters
    ----------
    user : User name (string)
    gtype : Kifu type (string) 
        ''   : 10 min. (default)
        'sb' :  3 min. (bullet mode)
        's1' : 10 sec.
    start : Number of start point (Numeric)

    Example
    ----------
    >>> username = '1_tsutsukana'
    >>> url_list = get_url_list(username)
    11
    21
    31
    41
    >>> len(url_list)>0
    True
    '''

    base_url = 'http://shogiwars.heroz.jp/users/history/'
    url_list = []

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
        print start
        break ## とりあえず1ループで止めておく
        
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
        ## TODO: 10秒切れ負けの場合を実装
        return 0
    else :
        print 'Error: gtypeに不正な値; gtype={0}'.format(gtype)

    sente_prev_remain_time = max_time
    gote_prev_remain_time = max_time

    results = []

    for i,w in enumerate(wcsa_list):
        if i%2==0:
            ## 駒の動き，あるいは特殊な命令の処理
            ## TODO: GOTE_TORYO_hoge みたいな文字列を
            ##       きちんとCSA形式のものに置換する．
            results.append(w)
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

    明示されていない棋譜ページの仕様に依存しているので，そのうち使えなくなる可能性がある．
    '''
    html = get_html(url)

    ## 対局に関するデータの取得
    res = re.findall(r'(?<=var\sgamedata\s=\s){.+?}', html, re.DOTALL)[0]
    _dict = eval(re.sub(r'\n\t\t(?P<key>\w+)(?=:)','"\g<key>"', res))
    _dict['user0'], _dict['user1'], _dict['date'] = _dict['name'].split('-')

    ## 棋譜の取得
    wars_csa = re.findall(r'(?<=receiveMove\(\").+(?=\"\);)', html)[0]
    _dict['csa'] = wcsa_to_csa(wars_csa, '')

    ## 時刻オブジェクトの生成
    _dict['datetime'] = dt.strptime(date, '%Y%m%d_%H%M%S')

    return _dict



if __name__ == '__main__':

    ## 棋譜のurlのリストを取得
    url_list = get_url_list('1_tsutsukana', gtype='')

    ## test code
    ui = 0
    url_to_kifudata(url_list[ui])

