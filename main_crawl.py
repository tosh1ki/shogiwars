#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from warscrawler import *


if __name__ == '__main__':

    gtype = gtype_dict['10s']
    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')
    wcrawler = WarsCrawler(dbpath, 10, 10)

    # 第4回名人戦で1〜100位になったプレーヤーの棋譜を取得する．
    csvpath = 'crawled.csv'
    t_users = wcrawler.get_users('meijin4', max_page=1)
    df_url = wcrawler.get_kifu_url(t_users, gtype, csvpath)
    df_kifu = wcrawler.get_all_kifu(csvpath)
