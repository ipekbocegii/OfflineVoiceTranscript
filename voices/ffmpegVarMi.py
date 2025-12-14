import shutil

ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    print("ffmpeg bulundu:", ffmpeg_path)
else:
    print("ffmpeg yüklü değil veya PATH’e eklenmemiş!")
