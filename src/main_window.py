from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QProgressBar, QSlider, QHBoxLayout, QCheckBox, QLineEdit # 添加 QLineEdit
from PyQt5.QtCore import Qt
from qfluentwidgets import FluentWindow, FluentIcon, InfoBar
from .video_splitter import is_cuda_available
from .task_worker import SplitTaskWorker
import os # 添加此行导入 os 模块

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('视频切分可视化客户端')
        self.resize(800, 600)
        self.init_ui()
        self.selected_path = None
        self.use_cuda = is_cuda_available()
        self.split_btn.clicked.connect(self.start_split)

    def init_ui(self):
        """
        初始化用户界面。

        设置窗口的布局和各种UI组件，包括文件选择按钮、路径标签、
        时间范围选择滑块、进度条和开始切分按钮。
        """
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget") # 为 central_widget 设置 objectName
        layout = QVBoxLayout()

        # 文件/文件夹选择按钮
        self.select_btn = QPushButton('选择文件或文件夹')
        self.select_btn.clicked.connect(self.select_file_or_folder)
        layout.addWidget(self.select_btn)

        # 显示选择的路径
        self.path_label = QLabel('未选择文件或文件夹')
        layout.addWidget(self.path_label)

        # 拖动条设置剪接起止时间
        slider_layout = QHBoxLayout()
        self.start_slider = QSlider(Qt.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(100)
        self.start_slider.setValue(0)
        self.end_slider = QSlider(Qt.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(100)
        self.end_slider.setValue(100)
        slider_layout.addWidget(QLabel('开始'))
        slider_layout.addWidget(self.start_slider)
        slider_layout.addWidget(QLabel('结束'))
        slider_layout.addWidget(self.end_slider)
        layout.addLayout(slider_layout)

        # 切分时长输入框
        split_duration_layout = QHBoxLayout()
        split_duration_layout.addWidget(QLabel('切分时长(秒):'))
        self.split_duration_input = QLineEdit()
        self.split_duration_input.setText("3") # 默认值为3秒
        self.split_duration_input.setFixedWidth(50) # 设置固定宽度，使其看起来更紧凑
        split_duration_layout.addWidget(self.split_duration_input)
        split_duration_layout.addStretch() # 添加伸缩因子，使输入框靠左
        layout.addLayout(split_duration_layout)

        # 静音复选框
        self.mute_checkbox = QCheckBox('静音(生成的视频将没有声音)')
        layout.addWidget(self.mute_checkbox)

        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 开始切分按钮
        self.split_btn = QPushButton('开始切分')
        layout.addWidget(self.split_btn)

        central_widget.setLayout(layout)
        self.addSubInterface(central_widget, FluentIcon.HOME, "主页")  # FluentWindow 使用 addSubInterface 来添加内容视图

    def select_file_or_folder(self):
        # 设置初始目录为桌面
        desktop = os.path.expanduser('~/Desktop')
        path, _ = QFileDialog.getOpenFileName(
            self, 
            '选择视频文件', 
            desktop,  # 添加桌面初始路径
            '视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*)'
        )
        if not path:
            path = QFileDialog.getExistingDirectory(self, '选择文件夹', desktop)  # 添加桌面初始路径
        
        if path:
            self.selected_path = path
            self.path_label.setText(path)
        else:
            self.selected_path = None
            self.path_label.setText('未选择文件或文件夹')

    def start_split(self):
        if not hasattr(self, 'selected_path') or not self.selected_path:
            InfoBar.error(
                title='操作错误',
                content='请先选择要处理的视频文件或文件夹',
                parent=self
            )
            return
        
        try:
            split_seconds_text = self.split_duration_input.text()
            split_seconds = int(split_seconds_text)
            if split_seconds <= 0:
                raise ValueError("切分时长必须为正整数")
        except ValueError:
            InfoBar.warning(
                title='输入错误',
                content='切分时长输入无效，将使用默认值3秒。',
                parent=self
            )
            split_seconds = 3 # 输入无效时使用默认值
            self.split_duration_input.setText("3") # 重置输入框为默认值

        start_time = self.start_slider.value()
        end_time = self.end_slider.value()
        is_muted = self.mute_checkbox.isChecked() # 获取静音状态
        self.progress_bar.setValue(0)
        self.split_btn.setEnabled(False)
        self.worker = SplitTaskWorker(
            self.selected_path, split_seconds, start_time, end_time, self.use_cuda, is_muted # 传递静音状态
        )
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.task_finished.connect(self.split_finished)
        self.worker.start()

    def update_progress(self, value, total):
        percent = int(value / total * 100)
        self.progress_bar.setValue(percent)

    def split_finished(self):
        self.progress_bar.setValue(100) # 确保进度条达到100%
        self.split_btn.setEnabled(True)
        InfoBar.success(
            title='操作成功',
            content='切分完成',
            parent=self
        )