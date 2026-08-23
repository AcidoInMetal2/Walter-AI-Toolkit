from pathlib import Path
import subprocess

class FFmpegService:
    def __init__(self, ffmpeg_exe='ffmpeg'):
        self.ffmpeg=ffmpeg_exe

    def extract_audio(self,video_file,output_audio):
        out=Path(output_audio)
        cmd=[self.ffmpeg,'-y','-i',str(video_file),'-vn','-acodec','pcm_s16le','-ar','16000','-ac','1',str(out)]
        p=subprocess.run(cmd,capture_output=True,text=True)
        if p.returncode!=0:
            raise RuntimeError(p.stderr)
        return out
