import os

def get_all_video_files(folder, exts=None):
    if exts is None:
        exts = ['.mp4', '.avi', '.mov', '.mkv']
    video_files = []
    for root, _, files in os.walk(folder):
        for f in files:
            if os.path.splitext(f)[1].lower() in exts:
                video_files.append(os.path.join(root, f))
    return video_files 