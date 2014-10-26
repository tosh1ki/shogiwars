## wars-an: 将棋ウォーズの棋譜を解析したい

### 作成物

- wars-scrape.py
  - 将棋ウォーズの棋譜を収集するための各種関数
  - 実行する前に `mongod --config mongodb.config`, `mongo`でMongoDBを起動して，`use warskifu` などとしておく．
- wars-visualize.ipynb
  - スクレイピングしたデータの解析，可視化
  - [nbviewer.ipython.org/github/tosh1ki/wars-an/blob/master/wars-visualize.ipynb](http://nbviewer.ipython.org/github/tosh1ki/wars-an/blob/master/wars-visualize.ipynb)


### 将棋ウォーズのrobots.txt
「棋譜をクローリングするわけだし一応 `robots.txt` を確認しておこう」と思って見てみたら全文コメントアウトされていて困った．そのうち編集される可能性が高そうなので，**プログラムを実行する際には注意する**．

[shogiwars.heroz.jp/robots.txt](http://shogiwars.heroz.jp/robots.txt)


### gtype
棋譜に付属している情報で，`gtype` というのがある．おそらく game type(?) の略だと思う．

- '' : 10分切れ負け
- 'sb' : 3分切れ負け (bullet modeの'b'?)
- 's1' : 10秒指し

### 将棋ウォーズの独自棋譜フォーマットについて
将棋ウォーズではCSA形式に似た独自の棋譜フォーマットを用いている．仕様がわからないので推測した結果を以下にメモしておく．

将棋ウォーズでは以下のようなフォーマットを用いている．

	+7776FU,L600	-3334FU,L589  (中略) +2728UM,L200	GOTE_WIN_TORYO

上記の例は10分切れ負けの場合である．この場合，`+7776FU,L600` というのは初手７六歩を指した時点で残り時間が600秒という意味であると考えられる．以下時間が徐々に減っていく．3分切れ負けの場合は `L180` から始まり，10秒指しの場合は `L3600` から始まる．

また，最後の `GOTE_WIN_TORYO` は文字通り(先手が投了し)後手が勝った，という意味であると考えられる．普通のCSA形式であれば `%TORYO` だけで済ませるところだが，将棋ウォーズでは `GOTE_WIN_TORYO` などとしている．終局時の特殊な文字列としては他に，`SENTE_WIN_DISCONNECT`, `SENTE_WIN_TIMEOUT`，`DRAW_SENNICHI` などがある．**おそらく持将棋用の文字列もあるが確認できていない．**


### 参考文献

- [日本将棋連盟公認 将棋ウォーズ](http://shogiwars.heroz.jp/)
- [CSA標準棋譜ファイル形式 v2.2](http://www.computer-shogi.org/protocol/record_v22.html)
