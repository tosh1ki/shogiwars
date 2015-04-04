#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
from warscrawler import *


if __name__ == '__main__':

    gtype = gtype_dict['10s']
    dbpath = os.path.expanduser('~/data/sqlite3/shogiwars.sqlite3')
    wcrawler = WarsCrawler(dbpath, 10, 10)

    # 第4回名人戦で1〜100位になったプレーヤーの棋譜を取得する．
    t_users = wcrawler.get_tournament_users('meijin4', max_page=1)

    for _user in t_users:

        url_list = wcrawler.get_url_list(_user, gtype=gtype, max_iter=10)
        wcrawler.append_to_sqlite(url_list)

        break
