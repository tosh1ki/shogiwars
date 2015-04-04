#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import pandas as pd
from warscrawler import *


if __name__ == '__main__':

    gtype = gtype_dict['10s']
    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')
    wcrawler = WarsCrawler(dbpath, 10, 10)

    # 第4回名人戦で1〜100位になったプレーヤーの棋譜を取得する．
    t_users = wcrawler.get_tournament_users('meijin4', max_page=1)

    csvpath = 'urllist.csv'
    df = wcrawler.get_kifu_url_list(t_users, gtype, csvpath)

    for d in df.values:
#    wcrawler.append_to_sqlite(url_list)
