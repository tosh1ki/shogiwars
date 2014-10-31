
### DBの準備


    import pymongo
    from collections import Counter
    import re


    connection = pymongo.Connection('localhost',27017)
    db = connection.warskifu
    col = db.kifu

### データの概要

MongoDBには事前に「第1回将棋ウォーズ聖帝戦」で**100位以内に入ったプレーヤー**の棋譜を(だいたい3週間分)取り込んである．情報の取得はイベントが終
わってから数時間後である．

[将棋ウォーズ - 第1回将棋ウォーズ聖帝戦ランキング](http://shogiwars.heroz.jp/events/seitei)

#### 取得した棋譜の総数


    col.find().count()




    1891



#### 対局数のランキング


    results = []
    for data in col.find():
        results.append(data['user0'])
        results.append(data['user1'])
    
    counter = Counter(results)
    id_list = []
    for _id, count in counter.most_common():
        if count > 80:
            print _id, count

    1_tsutsukana 261
    miya_with_r 113
    kumanbou 108
    kuropete 107
    zomzom082 103
    Aokijikuzan 103
    pagagm 102
    aoba81 100
    persona42 97


`1_tsutsukana` が1位だった．

`1_tsutsukana` は運営が放流している将棋ソフトなので大会のランキングには入っていない．しかし2位の2倍以上の対局数をこなしている．

#### 対局が行われている時間のヒストグラム


    %matplotlib inline
    import matplotlib.pyplot as plt
    
    dates = [d['datetime'] for d in col.find()]
    hist = plt.hist([t.hour for t in dates], bins=range(25))
    plt.xlim(0,24)
    plt.show()


![png](wars-visualize_files/wars-visualize_11_0.png)


まず19時から23時までが特に盛り上がっている点からして，プレーヤーには普通の社会人/学生が多いのかなという印象を受ける．

11時の人数が12時より多いのは不思議だ．大抵の場合昼休みは12~13時なので対局は12時に集中しそうな気がするのだが…

#### 時間切れになった対局の数


    pattern = re.compile(r'%TIME_UP')
    print col.find({'csa':pattern}).count()

    289

