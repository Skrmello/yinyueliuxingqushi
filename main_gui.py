import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QDateEdit, QFileDialog, QLineEdit
)
from PyQt5.QtCore import QDate, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import subprocess
import datetime
import keshihua  # 使用你原来的 keshihua.py

class SpiderThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, start_date, end_date):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.running = True

    def run(self):
        self.signal.emit("开始爬取数据...")
        try:
            subprocess.run(['python', 'pachong.py'], check=True)
            self.signal.emit("爬取完成，开始导入数据库...")
            subprocess.run(['python', 'dada.py'], check=True)
            self.signal.emit("数据库导入完成！")
        except Exception as e:
            self.signal.emit(f"发生错误: {str(e)}")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音乐流行趋势分析系统")
        self.resize(1000, 700)

        # 日期选择
        self.start_date = QDateEdit(calendarPopup=True)
        self.end_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.end_date.setDate(QDate.currentDate())
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期："))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("结束日期："))
        date_layout.addWidget(self.end_date)

        # 控制按钮
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.clicked.connect(self.start_spider)

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)

        # 可视化按钮区
        vis_buttons = QVBoxLayout()
        vis_map = {
            "每年歌曲数量": keshihua.plot_yearly_songs_count,
            "上榜最多艺术家": keshihua.plot_top_artists,
            "最长在榜歌曲": keshihua.plot_songs_longevity,
            "排名分布": keshihua.plot_peak_positions_distribution,
            "季节性趋势": keshihua.plot_seasonal_trends,
            "波动性": keshihua.plot_rank_volatility,
            "歌手影响力": keshihua.plot_song_artist_heatmap,
            "歌曲关键词": keshihua.plot_song_name_wordcloud,
        }

        for name, func in vis_map.items():
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, f=func, n=name: self.run_vis(f, n))
            vis_buttons.addWidget(btn)
 
        # 精确查询
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入歌手或歌名")
        self.search_btn = QPushButton("生成趋势图")
        self.search_btn.clicked.connect(self.run_search)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)

        # 图像展示区
        self.image_label = QLabel("图表将在此显示")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(300)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.addLayout(date_layout)
        main_layout.addWidget(self.start_btn)
        main_layout.addWidget(QLabel("运行状态："))
        main_layout.addWidget(self.status_box)
        main_layout.addLayout(vis_buttons)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.image_label)
        self.setLayout(main_layout)

    def start_spider(self):
        self.status_box.append("任务开始...")
        self.thread = SpiderThread(
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )
        self.thread.signal.connect(self.status_box.append)
        self.thread.start()

    def run_vis(self, func, name):
        self.status_box.append(f"生成{name}图...")
        func()
        img_path = os.path.join('charts', f'{func.__name__[5:]}.png')
        if os.path.exists(img_path):
            self.show_image(img_path)
            self.status_box.append("图表生成成功")
        else:
            self.status_box.append("图表生成失败")

    def run_search(self):
        name = self.search_input.text().strip()
        if not name:
            self.status_box.append("请输入查询内容")
            return
        self.status_box.append(f"正在查询: {name}")
        keshihua.plot_search_trend(name)
        img_path = os.path.join('charts', f'{name}_search_trend.png'.replace(' ', '_'))
        if os.path.exists(img_path):
            self.show_image(img_path)
            self.status_box.append("查询图表生成成功")
        else:
            self.status_box.append("未找到相关结果")

    def show_image(self, path):
        pixmap = QPixmap(path)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
