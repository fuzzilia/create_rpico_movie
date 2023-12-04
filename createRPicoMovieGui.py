# -*- coding: utf-8 -*-
import os
import sys
import copy
import cv2
import numpy as np

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

"""
RPico Boy用の動画データファイルに変換する
"""

class EmitObject():
  """ Emitで渡すオブジェクトクラス
  """
  def __init__(self, log_str=str):
    """ コンストラクタ

    Args:
      log_str (str): ログ文字列
    """
    self.log_str = log_str


  def get_log_str(self):
    """ ログ文字列を取得する関数

    Returns:
      log_str (str): ログ文字列
    """
    return self.log_str


class CreateRPicoMovieGui(QDialog):
  """ 大本のGUIクラス
  """
  VERSION = "1.0"
  TITLE = "Create RPico Movie v{}".format(VERSION)
  WINDOW_WIDTH  = 660
  WINDOW_HEIGHT = 300
  SAVE_SETTING_FILE = "/setting.json"
  TEMPLATE_FILE = "template/template.txt"
  SAVE_FILE = "MovieData.h"
  PREVIEW_WIDTH   = 160
  PREVIEW_HEIGHT  = 90
  TEXT_BOX_WIDTH  = 260
  TEXT_BOX_HEIGHT = PREVIEW_HEIGHT
  PB_WIDTH        = WINDOW_WIDTH - 30

  video = None
  frame_count = 0
  frame_rate  = 0
  frame_digit = 0
  run_process = None


  def __init__(self, parent=None):
    """ コンストラクタ
    """
    super(CreateRPicoMovieGui, self).__init__(parent)

    # アイコン画像を設定
    if sys.platform.startswith('win'):
      self.setWindowIcon(QPixmap(self.get_temp_path('img/icon.ico')))

    # 実行ファイルパスと設定ファイルパス
    self.my_dir_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    self.json_path = self.my_dir_path + self.SAVE_SETTING_FILE
    self.template_path = self.get_temp_path(self.TEMPLATE_FILE)

    # Widgetsの設定(タイトル、固定横幅、固定縦幅)
    self.setWindowTitle(self.TITLE)
    self.setFixedWidth(self.WINDOW_WIDTH)
    self.setFixedHeight(self.WINDOW_HEIGHT)

    # --- 動画ファイル選択部分 ---
    file_layout = QHBoxLayout()
    self.movie_path_line_edit = QLineEdit("")
    self.movie_path_line_edit.setEnabled(False) # テキスト入力を禁止
    self.file_select_button = QPushButton("参照")
    self.file_select_button.clicked.connect(self.movie_dialog)
    file_layout.addWidget(self.create_label("[変換動画ファイル]", True), 1)
    file_layout.addWidget(self.movie_path_line_edit, 5)
    file_layout.addWidget(self.file_select_button, 1)

    # --- 保存フォルダ選択部分 ---
    save_layout = QHBoxLayout()
    self.save_path_line_edit = QLineEdit("")
    self.save_path_line_edit.setEnabled(False) # テキスト入力を禁止
    self.save_select_button = QPushButton("参照")
    self.save_select_button.clicked.connect(self.save_folder_dialog)
    save_layout.addWidget(self.create_label("[保存フォルダ]", True), 1)
    save_layout.addWidget(self.save_path_line_edit, 5)
    save_layout.addWidget(self.save_select_button, 1)

    # --- 設定値部分 ---
    # 縮小wサイズ
    self.bin_w_sp       = self.create_spinbox(4, 128, 114)
    self.bin_w_sp.valueChanged.connect(self.bin_w_change)
    # 縮小hサイズ
    self.bin_h_sp       = self.create_spinbox(4, 64, 64)
    self.bin_h_sp.valueChanged.connect(self.bin_h_change)
    # 開始フレーム
    self.start_frame_sp = self.create_spinbox(0, 10000, 0)
    self.start_frame_sp.valueChanged.connect(self.start_change)
    # 終了フレーム
    self.end_frame_sp   = self.create_spinbox(1, 10000, 0)
    self.end_frame_sp.valueChanged.connect(self.end_change)
    # threshold
    self.threshold_sp   = self.create_spinbox(0, 255, 150)
    self.threshold_sp.valueChanged.connect(self.threshold_change)
    # fps
    self.fps_sp         = self.create_spinbox(1, 144, 24)

    setting_layout = QHBoxLayout()
    setting_layout.addWidget(self.create_label("[変換設定値]", True), 4)
    setting_layout.addWidget(self.create_label("  w:", True), 1)
    setting_layout.addWidget(self.bin_w_sp, 3)
    setting_layout.addWidget(self.create_label("  h:", True), 1)
    setting_layout.addWidget(self.bin_h_sp, 3)
    setting_layout.addWidget(self.create_label(" start frame:", True), 3)
    setting_layout.addWidget(self.start_frame_sp, 4)
    setting_layout.addWidget(self.create_label(" end frame:", True), 3)
    setting_layout.addWidget(self.end_frame_sp, 4)
    setting_layout.addWidget(self.create_label(" threshold:", True), 3)
    setting_layout.addWidget(self.threshold_sp, 3)
    setting_layout.addWidget(self.create_label("   fps:", True), 2)
    setting_layout.addWidget(self.fps_sp, 3)

    # --- start frameプレビュー部分 ---
    self.start_img_label = QLabel()
    self.start_img_label.setFixedSize(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
    self.start_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # 画像を中央に表示
    self.start_img_label.setFrameStyle(QFrame.Box)

    # --- end frameプレビュー部分 ---
    self.end_img_label = QLabel()
    self.end_img_label.setFixedSize(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
    self.end_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # 画像を中央に表示
    self.end_img_label.setFrameStyle(QFrame.Box)

    # --- テキストボックス(ログ表示)部分 ---
    self.textbox = QListView()
    self.text_list = QStringListModel()
    self.textbox.setModel(self.text_list)
    self.textbox.setFixedSize(self.TEXT_BOX_WIDTH, self.TEXT_BOX_HEIGHT)

    # --- 画像プレビュー・テキストボックス部分 ---
    img_layout = QHBoxLayout()
    img_layout.addWidget(self.start_img_label)
    img_layout.addWidget(self.create_label("   to", True))
    img_layout.addWidget(self.end_img_label)
    img_layout.addSpacing(10)
    img_layout.addWidget(self.textbox)

    # --- プログレスバー部分 ---
    pb_layput = QHBoxLayout()
    self.pb = QProgressBar()
    self.pb.setFixedWidth(self.PB_WIDTH)
    self.pb.setTextVisible(False)
    pb_layput.addWidget(self.pb)

    # --- ボタン部分 ---
    btn_layout = QHBoxLayout()
    self.run_button = QPushButton("変換開始")
    self.run_button.clicked.connect(self.create_movie_file)
    btn_layout.addWidget(QLabel(""), 1)
    btn_layout.addWidget(self.run_button, 1)
    btn_layout.addWidget(QLabel(""), 1)

    # --- レイアウトを作成して各要素を配置 ---
    layout = QVBoxLayout()
    layout.addLayout(file_layout)
    layout.addSpacing(6)
    layout.addLayout(save_layout)
    layout.addSpacing(6)
    layout.addLayout(setting_layout)
    layout.addSpacing(6)
    layout.addLayout(img_layout)
    layout.addSpacing(6)
    layout.addLayout(pb_layput)
    layout.addSpacing(6)
    layout.addLayout(btn_layout)

    # レイアウトを画面に設定
    self.setLayout(layout)

    # 実行プロセススレッドを作成
    self.run_process = RunProcess()
    self.run_process.process_thread.connect(self.update_log)
    self.run_process.finished.connect(self.show_result)


  def get_temp_path(self, relative_path):
    """ 実行時のパスを取得する関数

    Args:
      relative_path (str): 相対ファイルパス
        
    Returns:
      実行時のパス文字列
    """
    try:
      #Retrieve Temp Path
      base_path = sys._MEIPASS
    except Exception:
      #Retrieve Current Path Then Error 
      base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


  def create_label(self, name, bold_flg, alignment=None):
    """ ラベルを作成する関数

    Args:
      bold_flg (bool): 太文字にするかのフラグ
      alignment (AlignmentFlag): 文字位置の設定

    Returns:
      作成したQLabelオブジェクト (QLabel): QLabel
    """
    label = QLabel(name)

    if not alignment is None:
      label.setAlignment(alignment)

    if bold_flg:
      label.setStyleSheet("font-weight:bold;")

    return label


  def movie_dialog(self):
    """ 動画選択ダイアログを表示する関数
    """
    file_open_flg = self.filedialog_clicked(self.movie_path_line_edit, "動画ファイル選択", "Movies(*.mp4 *.mov *.avi *.webm)")

    if (file_open_flg):
      try:
        self.load_movie(self.movie_path_line_edit.text())
      except Exception as e:
        QMessageBox.warning(self, "注意", "動画読込でエラーが発生しました。\n\n" + str(e))


  def filedialog_clicked(self, line_edit, title, filter):
    """ ファイル選択ダイアログを表示させる関数

    Args:
      line_edit (QLineEdit): 画像ファイルパスのQLineEdit
      title (str) : ダイアログタイトル
      filter (str): フィルタ文字列

    Returns:
      True/False (bool): ファイルが選択されたかどうか
    """
    # ファイルを開いていたらそのフォルダを表示させる
    path = line_edit.text()
    if path == "":
      path = self.my_dir_path
    else:
      path = os.path.split(path)[0]

    fileObj = QFileDialog.getOpenFileName(self, title, path, filter)
    filepath = fileObj[0]

    if (filepath is not None) and (filepath != ""):
      # ファイルが選択されていればそのパスを設定
      line_edit.setText("")
      line_edit.setText(filepath)
      return True
    else:
      return False


  def load_movie(self, file_path):
    """ 動画ファイルを読み込む関数

    Args:
      file_path (str): 動画ファイルパス
    """
    self.video = cv2.VideoCapture(file_path)
    self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1    # 総フレーム数
    self.frame_rate  = int(self.my_round(self.video.get(cv2.CAP_PROP_FPS))) # フレームレート(fps)
    self.frame_digit = len(str(self.frame_count))                           # 総フレーム桁数

    # 読み込んだ動画の値から初期化
    self.start_frame_sp.setMaximum(self.frame_count)
    self.start_frame_sp.setValue(0)
    self.end_frame_sp.setMaximum(self.frame_count)
    self.end_frame_sp.setValue(self.frame_count)
    self.fps_sp.setMaximum(self.frame_rate)
    self.fps_sp.setValue(self.frame_rate)

    # プレビュー画面に表示
    self.show_preview(self.start_img_label, 0)
    self.show_preview(self.end_img_label, self.frame_count)

    # ログを初期化して表示を更新
    self.text_list.removeRows(0, self.text_list.rowCount())
    log_list = self.text_list.stringList()
    log_list.append("file: " + os.path.basename(self.movie_path_line_edit.text()))
    log_list.append("max frame: " + str(self.frame_count) + ", fps(round): " + str(self.frame_rate))
    self.text_list.setStringList(log_list)
    self.textbox.scrollToBottom()


  def my_round(self, val, digit=0):
    """ 小数点以下を四捨五入する関数
    """
    p = 10 ** digit
    return (val * p * 2 + 1) // 2 / p


  def show_preview(self, img_label, frame_num):
    """ プレビューを表示させる関数
    """
    if self.video == None:
      return

    # 対象フレームの2値化画像を取得してプレビュー部分に表示
    img_label.setPixmap(self.cv2_to_qpixmap(self.get_bin_image(frame_num)))


  def get_bin_image(self, frame_num):
    """ 対象フレームの2値化した縮小画像を取得する関数
    """
    # 対象フレームを読み込む
    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    _, frame = self.video.read()

    # 縮小
    frame = cv2.resize(frame, (self.bin_w_sp.value(), self.bin_h_sp.value()))

    # グレースケール化
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2値化
    _, img_thresh = cv2.threshold(gray, self.threshold_sp.value(), 255, cv2.THRESH_BINARY)

    return img_thresh


  def cv2_to_qpixmap(self, cv2_img):
    """ 画像をプレビューに表示する形式であるQPixmapに変換する関数

    Args:
      cv2_img (img): 変換画像

    Returns:
      img (img): 変換後画像
    """
    img = copy.deepcopy(cv2_img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # QtはBGRなので順番を変更

    height, width, _ = img.shape
    bytePerLine = img.strides[0] # ⇒ 3*width相当
    qimg = QImage(img.data, width, height, bytePerLine, QImage.Format.Format_RGB888)       
    return QPixmap(QPixmap.fromImage(qimg))


  def save_folder_dialog(self):
    """ 保存先フォルダ選択ダイアログを表示する関数
    """
    # すでに設定されているフォルダがあればそれを開く
    path = self.my_dir_path

    path_movie = os.path.dirname(self.movie_path_line_edit.text())
    path_save  = self.save_path_line_edit.text()

    if not path_save == "":
      path = path_save
    elif not path_movie == "":
      path = path_movie

    dir_path = QFileDialog.getExistingDirectory(self, "保存先フォルダ選択", path)

    if dir_path:
      self.save_path_line_edit.setText(dir_path)


  def create_spinbox(self, low, high, value):
    """ スピンボックスを作成する関数

    Args:
      low (int)  : 最小値
      high (int) : 最大値
      value (int): 値

    Returns:
      作成したQSpinBoxオブジェクト (QSpinBox): QSpinBox
    """
    sp = QSpinBox()
    sp.setRange(low, high)
    sp.setValue(value)
    return sp


  def bin_w_change(self):
    """ wの値が変更された時の関数
    """
    self.start_change()
    self.end_change()


  def bin_h_change(self):
    """ hの値が変更された時の関数
    """
    self.start_change()
    self.end_change()


  def start_change(self):
    """ start_frameの値が変更された時の関数
    """
    # startプレビュー画面に表示
    self.show_preview(self.start_img_label, self.start_frame_sp.value())


  def end_change(self):
    """ end_frameの値が変更された時の関数
    """
    # endプレビュー画面に表示
    self.show_preview(self.end_img_label, self.end_frame_sp.value()-1)


  def threshold_change(self):
    """ thresholdの値が変更された時の関数
    """
    self.start_change()
    self.end_change()


  def create_movie_file(self):
    """ 動画ファイルを作成する関数
    """
    save_path   = self.save_path_line_edit.text()
    new_width   = self.bin_w_sp.value()
    new_height  = self.bin_h_sp.value()
    start_frame = self.start_frame_sp.value()
    end_frame   = self.end_frame_sp.value()
    threshold   = self.threshold_sp.value()
    new_fps     = self.fps_sp.value()

    # 動画ファイルチェック
    if self.video == None:
      QMessageBox.warning(self, "注意", "変換動画ファイルが設定されていません。")
      return

    # 保存フォルダチェック
    if save_path == "":
      QMessageBox.warning(self, "注意", "保存フォルダが設定されていません。")
      return

    # フレーム範囲チェック
    if start_frame >= end_frame:
      QMessageBox.warning(self, "注意", "end frameはstart frameよりも大きい値を設定してください。")
      return

    # fpsチェック
    if self.frame_rate % new_fps != 0:
      QMessageBox.warning(self, "注意", "変換するfpsは元のfpsを割ったときに余りが出ない値を設定してください。")
      return

    # GUI非活性化
    self.set_all_enabled(False)

    # プログレスバーの開始
    self.pb.setMinimum(0)
    self.pb.setMaximum(0)

    # データを設定して処理を実行
    self.run_process.set_data(self.video, save_path + "/" + self.SAVE_FILE, self.template_path, new_width, new_height, start_frame, end_frame, threshold, self.frame_rate, new_fps)
    self.run_process.start()


  def update_log(self, emit_obj=EmitObject):
    """ ログを更新する関数

    Args:
      emit_obj (EmitObject): Emitで受け取るオブジェクト
    """  
    # ログ表示を更新
    log_list = self.text_list.stringList()
    log_list.append(emit_obj.get_log_str())
    self.text_list.setStringList(log_list)
    self.textbox.scrollToBottom()


  def show_result(self):
    """ メイン処理の結果を表示する関数
    """
    if self.run_process.error is None:
      text = "以下のファイルにMovieデータを保存しました。\n\n" + self.save_path_line_edit.text() + "/" + self.SAVE_FILE
      QMessageBox.information(self, "正常終了", text)
    else:
      QMessageBox.warning(self, "注意", "失敗しました。\n\n" + self.run_process.error)

    # プログレスバーの停止
    self.pb.setMinimum(0)
    self.pb.setMaximum(100)

    # GUI活性化
    self.set_all_enabled(True)


  def set_all_enabled(self, flg):
    """ GUIの有効/無効を設定する関数

    Args:
      flg (bool): True/有効化、False/無効化
    """
    self.file_select_button.setEnabled(flg)
    self.save_select_button.setEnabled(flg)
    self.bin_w_sp.setEnabled(flg)
    self.bin_h_sp.setEnabled(flg)
    self.start_frame_sp.setEnabled(flg)
    self.end_frame_sp.setEnabled(flg)
    self.threshold_sp.setEnabled(flg)
    self.fps_sp.setEnabled(flg)
    self.run_button.setEnabled(flg)


class RunProcess(QThread):
  """ 動画用ファイル作成処理を実行するプロセスクラス
  """
  OLED_MAX_WIDTH = 128

  process_thread = Signal(EmitObject)
  error = None

  video = None
  save_path = None
  width = None
  height = None
  start_frame = None
  end_frame = None
  fps = None
  new_fps = None


  def __init__(self, parent=None):
    """ コンストラクタ
    """
    QThread.__init__(self, parent)


  def set_data(self, video, save_path, template_path, width, height, start_frame, end_frame, threshold, fps, new_fps):
    self.error = None
    self.video = video
    self.save_path = save_path
    self.template_path = template_path
    self.width = width
    self.height = height
    self.start_frame = start_frame
    self.end_frame = end_frame
    self.threshold = threshold
    self.fps = fps
    self.new_fps = new_fps


  def run(self):
    # 開始フレームまで移動
    mode = "MODE_64BIT"
    file_str = ""
    step_frame = int(self.fps / self.new_fps)
    count_frame = 0

    for i in range(self.start_frame, self.end_frame + 1, step_frame):
      self.video.set(cv2.CAP_PROP_POS_FRAMES, i)
      _, frame = self.video.read()
      # 縮小
      frame = cv2.resize(frame, (self.width, self.height))
      # グレースケール化
      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      # 2値化
      _, img_thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)
      # 配列に変換して1ファイル分追加
      if self.width > 64:
        file_str = file_str + self.get_64bit_hex_array_90rot(img_thresh)
        mode = "MODE_64BIT_ROT"
      else:
        file_str = file_str + self.get_64bit_hex_array(img_thresh)
        mode = "MODE_64BIT"

      # 画面表示用のログを出力
      self.process_thread.emit(EmitObject("frame: " + str(i) + " done!"))
      count_frame += 1

    # 各種設定値
    w_val = str(self.width) if mode == "MODE_64BIT_ROT" else str(64)
    array_col = "MOVIE_WIDTH" if mode == "MODE_64BIT_ROT" else "MOVIE_HEIGHT"
    movie_x_pos = int((self.OLED_MAX_WIDTH - self.width) / 2) + 1

    # テンプレートを読み込んで書き込み文字列作成
    template_str = self.load_template()
    file_str = template_str.format(mode, w_val, str(self.height), str(self.new_fps), count_frame, str(movie_x_pos), array_col, file_str[:-2])

    # ファイルに書き込み
    if not self.save_movie_data_file(file_str, self.save_path):
      # 画面表示用のログを出力
      self.process_thread.emit(EmitObject("saved: " + self.save_path))


  # 64bitの16進数配列を取得する関数
  def get_64bit_hex_array_90rot(self, img_thresh):
    img_np_array = np.array(img_thresh)
    hex_str = ""

    for w in range(0, img_np_array.shape[1]):
      line_str = "0b"
      for h in range(0, img_np_array.shape[0]):
        dot = 1 if img_np_array[h,w] == 255 else 0
        line_str = line_str + str(dot)

      # 一行分終わったら2進数を16進数に変換
      line_str = format(int(line_str, 0), '#0x') + ","
      hex_str = hex_str + line_str

    # 1枚分の処理が終わった場合
    hex_str = "  {" + hex_str[:-1] + "},\n"
    return hex_str


  # 64bitの16進数配列を取得する関数
  def get_64bit_hex_array(self, img_thresh):
    img_np_array = np.array(img_thresh)
    hex_str = ""

    for h in range(0, img_np_array.shape[0]):
      line_str = "0b"
      for w in range(0, img_np_array.shape[1]):
        dot = 1 if img_np_array[h,w] == 255 else 0
        line_str = line_str + str(dot)

      # 一行分終わったら2進数を16進数に変換
      line_str = format(int(line_str, 0), '#0x') + ","
      hex_str = hex_str + line_str

    # 1枚分の処理が終わった場合
    hex_str = "  {" + hex_str[:-1] + "},\n"
    return hex_str


  def load_template(self):
    """ テンプレートファイルを読み込む関数
    """
    result = None
    try:
      f = open(self.template_path, 'r', encoding='UTF-8')
      result = f.read()
    except Exception as e:
      self.error = str(e)
    finally:
      f.close()
      return result


  def save_movie_data_file(self, data_str, save_path):
    """ Movieファイルに書き込む関数
    """
    is_error = False
    try:
      f = open(save_path, 'w', encoding='UTF-8')
      f.write(data_str)
    except Exception as e:
      self.error = str(e)
      is_error = True
    finally:
      f.close()
      return is_error


if __name__ == '__main__':
  # Qtアプリケーションの作成
  app = QApplication(sys.argv)

  # フォームを作成して表示
  form = CreateRPicoMovieGui()
  form.show()

  # 画面表示のためのループ
  sys.exit(app.exec())
