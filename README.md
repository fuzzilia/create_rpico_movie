# Create RPico Movie

## 概要

RPicoBoyで動画ファイルを再生するためのデータファイルを作成するツールです。

動画ファイルを読み込んで2値化し、指定フレーム分のドットを64bitの16進数配列のデータとして出力します。

## 使い方

１：「変換動画ファイル」の参照ボタンをクリックして変換したい動画を読み込みます(mp4, mov, avi, webmに対応)。

２：「保存フォルダ」の参照ボタンをクリックして変換後ファイルの保存フォルダを指定します。

３：「変換設定値」の各値を入力します。各設定値の説明は以下の通りです。

|名称|内容|デフォルト値|備考|
|---|---|---|---|
|w|変換後の幅|114|デフォルト値は元動画が16:9の場合に合わせている。|
|h|変換後の高さ|64|デフォルト値は元動画が16:9の場合に合わせている。|
|start_frame|変換開始フレーム|0|動画の最初のフレーム番号が0。この値を変更するとプレビュー画像も更新される。|
|end_frame|変換終了フレーム|動画の最終フレーム番号|この値を変更するとプレビュー画像も更新される。|
|threshold|2値化する閾値|150|この値を変更するとプレビュー画像も更新される。|
|fps|変換後fps|元動画のfps(整数値)|元動画のfpsが小数の場合は整数値に変換(23.98の場合は24で計算)。設定値は「元fps / 設定fps」の結果が割り切れるものしか設定できない。例として元動画が24fpsの場合は24, 12, 8, 6, 4, 3, 2, 1のいずれかのみ設定可能でそれ以外の場合はエラーとなる。|

４：変換開始ボタンをクリックして変換処理を開始します。変換フレーム数が多い場合は時間がかかるので注意してください。

５：変換終了後、ダイアログが表示され正常終了すると保存フォルダに「MovieData.h」ファイルが作成されます。

６：RPicoBoyの動画再生サンプルスケッチに「MovieData.h」ファイルがあるので作成したファイルで上書きします。

７：サンプルスケッチをRPico Boyに書き込むことで変換したファイルをドット絵の動画として再生できます。

## 注意

1フレーム毎の画像をドットの配列として保存するため、fpsが高い、または長尺の動画についてはRPicoBoyへの書き込み時に容量不足によってエラーとなる場合があります。

おおよその目安としてwが114、hが64で24fpsで90秒程度が容量の限界値となります。

16:9の動画はwが114、hが64で最適化しているため、その他のサイズではRPicoBoyでの再生時に意図しない形で再生される場合があります。

## 開発環境

|名称|バージョン|
|---|---|
|Python|3.10.8|
|NumPy|1.24.3|
|OpenCV|4.7.0|
|PySide6|6.5.1|
|pyinstaller|5.11.0|

## ビルドコマンド

create_rpico_movieディレクトリの階層に移動し、以下のコマンドを実行します。

### ・Windows

```shell
pyinstaller createRPicoMovie.spec
```

## ソース実行コマンド

create_rpico_movieディレクトリの階層に移動し、以下のコマンドを実行します。

```shell
python createRPicoMovieGui.py
```

## LICENSE

本ライセンスはLICENSEファイルを参照してください。
- https://github.com/fuzzilia/create_rpico_movie/blob/master/LICENSE

使用している各ライブラリのライセンスは以下を参照してください。

- NumPy
  - https://github.com/numpy/numpy/blob/main/LICENSE.txt
- OpenCV
  - https://github.com/opencv/opencv/blob/master/LICENSE
- PySide6
  - https://wiki.qt.io/Qt_for_Python
  - https://github.com/pyside/pyside-setup/tree/dev/LICENSES
- pyinstaller
  - https://github.com/pyinstaller/pyinstaller/wiki/FAQ
  - https://github.com/pyinstaller/pyinstaller?tab=License-1-ov-file#readme

