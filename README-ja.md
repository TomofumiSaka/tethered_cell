# Tethered_cell
このリポジトリは ImageJ Fiji 上で動作する, べん毛を持つバクテリアのテザードセルアッセイを解析するためのスクリプトです.
以下の論文でこのスクリプトを使用しました。
"Novel Insights into Conformational Rearrangements of the Bacterial Flagellar Switch Complex", DOI: 10.1128/mBio.00079-19

# 使い方
* 次のURLから mageJ Fiji をダウンロードしてインストールしてください。 https://imagej.net/Fiji/Downloads
* 「tethered_cell.py」をダウンロードして, Fijiのインストール先の, 'Fiji.app\plugins\' ディレクトリにおいてください.
* ImageJ Fiji を立ち上げるとメニューの 'Plugins' に 'tethered_cell' が下の方に追加されているのでクリックします.
* ファイルを選ぶためのウィンドウが表示されるので, 解析したいtiffファイルを選びます（もしくはImageJがサポートしている他のスタック画像ファイルや動画ファイル）.
* ダイアログに解析したいフレーム数, フレームレート, 画面上での細胞の回転方向を入力します.
* 動画ファイルと同じ場所に, 「_tethered_cell_result」という接尾辞のついたフォルダが作成されそこに結果が保存されます.  
RoiN.csvという名前で細胞の重心, 角度, 回転速度が出力されます. RoiN.tiff にクロップした画像が保存され、PlotM.bmpに簡単なプロットが出力されます.
* また, このスクリプトの動作確認のために 'test_movies/1103_pH6.5_2016.04.15_17.17.19S.ihvideo-2.tif' を用意しています.

# ライセンス
[MIT License](LICENSE)  
日本語訳: https://ja.osdn.net/projects/opensource/wiki/licenses%2FMIT_license  
端的に言えば「このコードの使用についての保証はない」, 「適切な著作権表示の下に自由に複製・配布・改変を行ってよい」です。

# How To Cite
Please cite "Novel Insights into Conformational Rearrangements of the Bacterial Flagellar Switch Complex", DOI: [10.1128/mBio.00079-19](https://doi.org/10.1128/MBIO.00079-19)  
or 
this repository https://github.com/TomofumiSaka/tethered_cell

# その他
あるディレクトリを指定したらそのディレクトリ以下のスタックファイルをすべて解析するようなスクリプトを, 将来的にここに追加するかもしれない。
