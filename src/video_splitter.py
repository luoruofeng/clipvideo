import os
import subprocess
import ffmpeg
from moviepy import ColorClip, CompositeVideoClip, ImageClip, VideoFileClip,AudioFileClip,CompositeAudioClip,vfx

def is_cuda_available():
    """检测本机是否支持ffmpeg的cuda加速"""
    # 检查CUDA可用性
    result = subprocess.Popen(['ffmpeg', '-hide_banner', '-hwaccels'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    result.wait()
    output = result.stdout.read().decode('utf-8')
    return 'cuda' in output.lower()

def split_video_ffmpeg(input_path, output_dir, split_seconds, start_time=0, end_time=None, use_cuda=False, progress_callback=None, is_muted=False):
    """
    使用ffmpeg切分视频
    input_path: 输入视频路径
    output_dir: 输出目录
    split_seconds: 每段时长（秒）
    start_time: 剪接起始时间（秒）
    end_time: 剪接结束时间（秒），None表示到视频结尾
    use_cuda: 是否使用cuda加速 (此参数在此版本中未使用，因为采用copy方式)
    progress_callback: 进度回调
    is_muted: 是否静音
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # 获取视频总时长
    probe = ffmpeg.probe(input_path)
    duration = float(probe['format']['duration'])
    if end_time is None or end_time > duration:
        end_time = duration
    total = int((end_time - start_time) // split_seconds) + 1
    for i in range(total):
        seg_start = start_time + i * split_seconds
        seg_end = min(seg_start + split_seconds, end_time)
        if seg_start >= end_time:
            break
        output_file = os.path.join(output_dir, f"{i+1:03d}.mp4")
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(seg_start),      # -ss 参数提前
            '-i', input_path,
            '-t', str(seg_end - seg_start),
            '-c', 'copy',              # 直接复制视频和音频流
        ]
        if is_muted:
            cmd.append('-an') # 添加无音频流参数
        cmd.append(output_file)

        # 注意：移除了 use_cuda 的判断，因为 -c copy 不涉及编码，所以CUDA加速不适用
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW).wait()
        if progress_callback:
            progress_callback(i+1, total)


def split_video(input_path, output_path, start_time, end_time, is_muted=False):
    """
    切分单个视频片段
    input_path: 输入视频路径
    output_path: 输出视频路径
    start_time: 剪接起始时间（秒）
    end_time: 剪接结束时间（秒）
    is_muted: 是否静音
    """
    duration = end_time - start_time
    command = [
        'ffmpeg', '-y',
        '-ss', str(start_time),    # -ss 参数提前
        '-i', input_path,
        '-t', str(duration),
        '-c', 'copy',             # 直接复制视频和音频流
    ]
    if is_muted:
        command.append('-an') # 添加无音频流参数
    command.append(output_path)

    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW).wait()


def crop_square_video(input_path: str, output_name: str = None) -> str:
    """
    横屏视频居中裁剪为正方形（高度不变，宽度按高度值裁剪）
    """
    with VideoFileClip(input_path) as clip:
        width, height = clip.size
        if height >= width:
            return input_path
        crop_width = height
        x_center = width / 2
        y_center = height / 2
        cropped_clip = clip.with_effects(
                [vfx.Crop(x_center=x_center, y_center=y_center, width=crop_width, height=height)])
        
        if not output_name:
            base = os.path.splitext(input_path)[0]
            output_name = f"{base}_square.mp4"
        cropped_clip.write_videofile(output_name, codec="libx264", audio_codec="aac")
        cropped_clip.close()
        return os.path.abspath(output_name)