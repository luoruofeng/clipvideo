from PyQt5.QtCore import QThread, pyqtSignal
from .video_splitter import split_video_ffmpeg
from .utils import get_all_video_files
from .video_splitter import crop_square_video
import os

class SplitTaskWorker(QThread):
    progress_changed = pyqtSignal(int, int)
    task_finished = pyqtSignal()

    def __init__(self, path, split_seconds, start_time, end_time, use_cuda, is_muted=False,is_square=False): # 添加 is_muted 参数，并提供默认值
        super().__init__()
        self.path = path
        self.split_seconds = split_seconds
        self.start_time = start_time
        self.end_time = end_time
        self.use_cuda = use_cuda
        self.is_muted = is_muted # 保存 is_muted 状态
        self.is_square = is_square # 保存 is_square 状态

    def run(self):
        if os.path.isdir(self.path):
            files = get_all_video_files(self.path)
        else:
            files = [self.path]
        total_files = len(files)
        squere_files = []
        if self.is_square:
            for file in files:
                # 在这里添加将视频转换为正方形的代码
                r = crop_square_video(file)
                squere_files.append(r)
        if len(squere_files) > 0:
            files = squere_files    
        for idx, file in enumerate(files):
            out_dir = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0])
            split_video_ffmpeg(
                file, out_dir, self.split_seconds,
                start_time=self.start_time, end_time=self.end_time,
                use_cuda=self.use_cuda,
                progress_callback=lambda seg, seg_total: self.progress_changed.emit(idx * 100 + int(seg / seg_total * 100), total_files * 100),
                is_muted=self.is_muted # 传递 is_muted 参数
            )
        if len(squere_files) > 0:
            for file in files:
                os.remove(file)
                print(f"删除文件: {file}")
        self.task_finished.emit()