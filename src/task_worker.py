from PyQt5.QtCore import QThread, pyqtSignal
from .video_splitter import split_video_ffmpeg
from .utils import get_all_video_files
import os

class SplitTaskWorker(QThread):
    progress_changed = pyqtSignal(int, int)
    task_finished = pyqtSignal()

    def __init__(self, path, split_seconds, start_time, end_time, use_cuda, is_muted=False): # 添加 is_muted 参数，并提供默认值
        super().__init__()
        self.path = path
        self.split_seconds = split_seconds
        self.start_time = start_time
        self.end_time = end_time
        self.use_cuda = use_cuda
        self.is_muted = is_muted # 保存 is_muted 状态

    def run(self):
        if os.path.isdir(self.path):
            files = get_all_video_files(self.path)
        else:
            files = [self.path]
        total_files = len(files)
        for idx, file in enumerate(files):
            out_dir = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0])
            split_video_ffmpeg(
                file, out_dir, self.split_seconds,
                start_time=self.start_time, end_time=self.end_time,
                use_cuda=self.use_cuda,
                progress_callback=lambda seg, seg_total: self.progress_changed.emit(idx * 100 + int(seg / seg_total * 100), total_files * 100),
                is_muted=self.is_muted # 传递 is_muted 参数
            )
        self.task_finished.emit()