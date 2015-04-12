#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import re
import yaml
import sys
import time
import sqlite3
import requests
import datetime as dt
import pandas as pd
from bs4 import BeautifulSoup

import pdb


gtype_dict = {'10m': '', '3m': 'sb', '10s': 's1'}

WCSA_PATTERN = re.compile(r'(?<=receiveMove\(\").+?(?=\"\);)')
GAME_HEADER_PATTERN = re.compile(r'(?<=var\sgamedata\s=\s){[^}]+}', re.DOTALL)


class WarsCrawler:
    '''将棋ウォーズ用のクローラー

    Args
    ----------
    dbpath : string
        SQLiteのパス
    interval : int, optional (default = 10)
        取得時の時間間隔
    n_retry : int, optional (default = 10)
        取得時の再試行の回数のmax
    '''

    def __init__(self, dbpath, interval=10, n_retry=10):
        self.dbpath = dbpath
        self.INTERVAL_TIME = interval
        self.MAX_N_RETRY = n_retry

        # SQLiteに接続する
        self.con = sqlite3.connect(self.dbpath)
        self.con.text_factory = str

    def get_html(self, url):
        '''指定したurlのhtmlを取得する
        '''
        time.sleep(self.INTERVAL_TIME)

        for n in range(self.MAX_N_RETRY):
            time.sleep(10 * n * self.INTERVAL_TIME)

            try:
                res = requests.session().get(url)
            except requests.ConnectionError:
                print('\nConnection aborted.\n')
                res = None

            if res and res.status_code == 200:
                return res.text
            else:
                print('\nretry (WarsCrawler.get_html())\n')
                sys.stdout.flush()
        else:
            sys.exit('Exceeded MAX_N_RETRY (WarsCrawler.get_html())')

    def get_url(self, user, gtype, max_iter=10):
        ''' 指定したユーザーの棋譜を取得する．

        Args
        ----------
        user: string
            User name
        gtype: string
            Kifu type
        max_iter: int, optional (default=10)
            取得する最大数．
            10個ずつ取得するたびに判定しており厳密には守るつもりはない．
        '''
        url_list = []
        start = 1
        url = ('http://shogiwars.heroz.jp/users/history/'
               '{user}?gtype={gtype}&start={start}')
        pattern = 'http://shogiwars.heroz.jp:3002/games/[\w\d_-]+'

        while start <= max_iter:
            url = url.format(user=user, gtype=gtype, start=start)
            text = self.get_html(url)
            match = re.findall(pattern, text)

            if match:
                url_list.extend(match)
                start += len(match)
            else:
                break

        return url_list

    def get_kifu(self, url):
        ''' urlが指す棋譜とそれに関する情報を辞書にまとめて返す．
        '''
        html = self.get_html(url)
        res = re.findall(GAME_HEADER_PATTERN, html)[0]

        # keyがquoteされていないので対処する
        d = yaml.load(re.sub('[{}\t,]', ' ', res))

        d['user0'], d['user1'], d['date'] = d['name'].split('-')
        wars_csa = re.findall(WCSA_PATTERN, html)[0]
        d['wcsa'] = wars_csa
        d['datetime'] = dt.datetime.strptime(d['date'], '%Y%m%d_%H%M%S')
        d['csa'] = self.wcsa_to_csa(d)

        return d

    def get_all_kifu(self, csvpath):
        ''' url_list 中の url の指す棋譜を取得，SQLiteに追加．

        Args
        ----------
        csvpath: string
            クロールするurlの入っているcsvのパス
        '''
        df_crawled = pd.read_csv(csvpath)

        not_crawled = df_crawled.query('crawled==0')

        if not_crawled.empty:
            print('{0}のファイルは全て取得済み'.format(csvpath))
            return None

        url_list = list(not_crawled.url)
        sec = len(url_list) * self.INTERVAL_TIME
        finish_time = dt.datetime.now() + dt.timedelta(seconds=sec)

        # 途中経過の表示
        print('{0}件の棋譜'.format(len(url_list)))
        print('棋譜収集終了予定時刻 : {0}'.format(finish_time))
        sys.stdout.flush()

        df = pd.DataFrame()

        for _url in url_list:
            kifu = self.get_kifu(_url)
            df = df.append(kifu, ignore_index=True)

            df_crawled.loc[df_crawled.url == _url, 'crawled'] = 1
            df_crawled.to_csv(csvpath, index=False)

        if not df.empty:
            df.to_sql('kifu', self.con, index=False, if_exists='append')
            return df
        else:
            return None

    def get_users(self, title, max_page=10):
        '''大会名を指定して，その大会の上位ユーザーのidを取ってくる

        Examples
        ----------
        将棋ウォーズ第4回名人戦に参加しているユーザーのidを取得する．
        >>> wcrawler.get_users('meijin4', max_page=100)
        '''
        page = 0
        url = 'http://shogiwars.heroz.jp/events/{title}?start={page}'
        results = []

        while page < max_page:
            _url = url.format(title=title, page=page)
            print(_url)
            sys.stdout.flush()
            
            html = self.get_html(_url)
            _users = re.findall(r'\/users\/(\w+)', html)

            # _usersが空でない場合追加．そうでなければbreak
            if _users:
                results.extend(_users)
                page += 25
            else:
                break

        return results

    def get_kifu_url(self, users, gtype, csvpath,
                     max_iter=10, if_exists='append'):
        '''ユーザー名とgtypeを指定して棋譜のurlを取得する．

        Args
        ----------
        users: string
            ユーザー名
        gtype: string
            gtype
        csvpath: string
            棋譜のurlを保存するCSVファイルのパス
        max_iter: string, optional (default=10)
            最大試行回数
        '''
        url_list = []

        print('\ngtype:{0}, max_iter:{1}\n'.format(gtype, max_iter))

        for _user in users:
            print(_user)

            _url_list = self.get_url(_user, gtype=gtype, max_iter=max_iter)
            url_list.extend(_url_list)

        df = pd.DataFrame(url_list)
        df.ix[:, 1] = 0
        df.columns = ['url', 'crawled']
        
        if os.path.exists(csvpath) and if_exists == 'append':
            df_before = pd.read_csv(csvpath, index_col=0)
            df = pd.concat([df_before, df], axis=0, ignore_index=True)

        df.to_csv(csvpath)

        return df

    def wcsa_to_csa(self, d):
        '''将棋ウォーズ専用?のCSA形式を一般のCSA形式に変換する．

        Args
        ----------
        wars_csa
            将棋ウォーズ特有のCSA形式で表された棋譜の文字列
        gtype
            処理したい棋譜のgtype
        '''
        wcsa_list = re.split(r'[,\t]', d['wcsa'])

        time_up = ['\tGOTE_WIN_TIMEOUT',
                   '\tGOTE_WIN_DISCONNECT',
                   '\tGOTE_WIN_TORYO']

        if d['wcsa'] in time_up:
            # 1手も指さずに時間切れ or 接続切れ or 投了
            return '%TIME_UP'

        if d['gtype'] == gtype_dict['10m']:
            max_time = 60 * 10
            rule = '\'持ち時間:10分、切れ負け'
            time_limit = '$TIME_LIMIT:00:10+00'
        elif d['gtype'] == gtype_dict['3m']:
            max_time = 60 * 3
            rule = '\'持ち時間:3分、切れ負け'
            time_limit = '$TIME_LIMIT:00:03+00'
        elif d['gtype'] == gtype_dict['10s']:
            max_time = 3600
            rule = '\'初手から10秒'
            time_limit = '$TIME_LIMIT:00:00+10'
        else:
            print('Error: gtypeに不正な値; gtype={0}'.format(d['gtype']))

        sente_prev_remain_time = max_time
        gote_prev_remain_time = max_time

        results = [
            '\'バージョン', 'V2.2',
            '\'対局者名', 'N+', d['user0'], 'N-', d['user1'],
            '\'棋譜情報', '\'棋戦名', '$EVENT:', '将棋ウォーズ',
            '\'対局場所', '$SITE:shogiwars.heroz.jp',
            '\'開始日時', 
            '$START_TIME:' + d['datetime'].strftime('%Y/%m/%d %H:%M:%S'),
            rule, time_limit,
            '\'先手番', '+',
            '\'指し手と消費時間'
        ]

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
                # 時間の行の処理
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
