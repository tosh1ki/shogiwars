#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from warscrawler import *


if __name__ == '__main__':

    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')
    wcrawler = WarsCrawler(dbpath, interval=10, n_retry=10)
    csvpath = 'crawled.csv'

#    gtype = gtype_dict['10s']

    if not os.path.exists(csvpath):
        # csvpathのファイルが存在しない場合

        for mode, gtype in gtype_dict.items():
            # 将棋ウォーズ第4回名人戦の棋譜を取得する．
            t_users = wcrawler.get_users('meijin4', max_page=1)
            df_url = wcrawler.get_kifu_url(t_users, gtype, csvpath)

#    df_kifu = wcrawler.get_all_kifu(csvpath)
