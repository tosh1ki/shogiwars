shogiwars
=================

将棋ウォーズの棋譜を収集・解析したい

# 作成物

- main_crawl.py
- warscrawler.py
  - 将棋ウォーズの棋譜を収集するための各種関数
  - **明示されていない棋譜ページの仕様に依存しているので，そのうち使えなくなる可能性がある．**
- extract.py
  - 特徴量を抽出する
- ipynb/
  - **古いバージョン**
  - [データの可視化](http://nbviewer.ipython.org/github/tosh1ki/shogiwars/blob/master/ipynb/wars-visualize.ipynb)
  - [将棋ウォーズで削除されたアカウントの棋譜を検討してみる](http://nbviewer.ipython.org/github/tosh1ki/shogiwars/blob/master/ipynb/junpe_.ipynb)


# 将棋ウォーズ内部の仕様について
## 将棋ウォーズのrobots.txt
「棋譜をクローリングするわけだし一応 `robots.txt` を確認しておこう」と思って見てみたら全文コメントアウトされていて困った．そのうち編集される可能性が高そうなので，**プログラムを実行する際には注意する**．

[shogiwars.heroz.jp/robots.txt](http://shogiwars.heroz.jp/robots.txt)

## gtype
棋譜に付属している情報で，`gtype` というのがある．おそらく game type(?) の略だと思う．

- `  ` : 10分切れ負け
- `sb` : 3分切れ負け (bullet modeの'b'?)
- `s1` : 10秒指し


## 将棋ウォーズの独自棋譜フォーマットについて
将棋ウォーズではCSA形式に似た独自の棋譜フォーマットを用いている．仕様がわからないので**推測**した結果を以下にメモしておく．

将棋ウォーズでは以下のようなフォーマットを用いている．

	+7776FU,L600	-3334FU,L589  (中略) +2728UM,L200	GOTE_WIN_TORYO

上記の例は10分切れ負けの場合である．この場合，`+7776FU,L600` というのは初手７六歩を指した時点で残り時間が600秒という意味であると考えられる．以下時間が徐々に減っていく．3分切れ負けの場合は `L180` から始まり，10秒指しの場合は `L3600` から始まる．

また，最後の `GOTE_WIN_TORYO` は文字通り(先手が投了し)後手が勝った，という意味であると考えられる．普通のCSA形式であれば `%TORYO` だけで済ませるところだが，将棋ウォーズでは `GOTE_WIN_TORYO` などとしている．

### 終局時の文字列

終局時に出てくる文字列としては，（確認した限りでは）以下のものがある．先手勝ちの場合についてのみ書くが，後手勝ちの場合は `SENTE` の部分を `GOTE` に変えるだけで良い．

- `SENTE_WIN_TORYO` : 後手投了で先手勝ち
- `SENTE_WIN_DISCONNECT` : 後手接続切れで先手勝ち
- `SENTE_WIN_TIMEOUT` : 後手時間切れで先手勝ち
- `SENTE_WIN_ENTERINGKING` : 先手が入玉宣言して勝ち?
- `SENTE_WIN_OUTE_SENNICHI` : 後手連続王手の千日手による反則負けで先手勝ち
- `DRAW_SENNICHI` : 千日手で引き分け

などがある．**「相入玉で引き分け」もあるはず(?)だが確認できていない．**


# 参考文献

- [日本将棋連盟公認 将棋ウォーズ](http://shogiwars.heroz.jp/)
- [CSA標準棋譜ファイル形式 v2.2](http://www.computer-shogi.org/protocol/record_v22.html)
