import json, os, re
from pydub import AudioSegment
import sys


def test_dir():
    user_path = os.path.expanduser('~')
    jian_dir = user_path+r'\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft'
    return jian_dir

def get_text(text):
    return re.search(r'\[([^\[\]]+)\]', text).group(1) or None

def get_subtitles(input_file):
    base_dir = os.path.dirname(input_file)
    with open(input_file, 'r', encoding='utf-8') as json_data:
        data = json.load(json_data)
    id_to_text = {text['id']: text['content'] for text in data['materials']['texts']}
    audios = [{"path": base_dir + audio['path'].split("##")[-1], "text_id": audio['text_id'], "name": audio['name']} for audio in data['materials']['audios']]
    tracks = [{'id': segment['id'], 'material_id': segment['material_id'], 'text': id_to_text[segment['material_id']], 'start': segment['target_timerange']['start'], 'duration': segment['target_timerange']['duration']} for track in data['tracks'] if track['type'] == 'text' for segment in track['segments']]
    subtitles = [{'id': track['id'], 'material_id': track['material_id'], 'text': get_text(track['text']), 'start': track['start'] // 1000, 'end': (track['start'] + track['duration']) // 1000} for track in tracks]
    return [{**subtitle, **audio} for subtitle in subtitles for audio in audios if subtitle['material_id'] == audio['text_id']]

def to_srt(input_file, output_file):
    subtitles = get_subtitles(input_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, subtitle in enumerate(subtitles):
            start_time = ms_to_time(subtitle['start'])
            end_time = ms_to_time(subtitle['end'])
            f.write(f"{i + 1}\n{start_time} --> {end_time}\n{subtitle['text']}\n\n")

def ms_to_time(ms):
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                    
def combine_audio_clips(clips, output_file, use_absolute_time=False):
    clips.sort(key=lambda x: x['start'])
    combined = AudioSegment.silent(duration=clips[-1]['end']) if use_absolute_time else AudioSegment.empty()
    for clip in clips:
        path = clip['path']
        if not os.path.isfile(path):
            print(f"文件不存在：{path}")
            continue
        audio = AudioSegment.from_file(path, format="wav")
        combined = combined.overlay(audio, position=clip['start']) if use_absolute_time else combined + audio
    combined.export(output_file, format="wav")

if __name__ == "__main__":
    os.startfile(test_dir())
    
    while True:
        input_dir = sys.argv[1].strip('"').replace('"','').replace("'","") if len(sys.argv) > 1 else input("请输入文件夹路径：").strip('"').replace('"','').replace("'","")

        while not os.path.isdir(input_dir):
            input_dir = input("\n############\n请输入有效的文件夹路径===>：\n")
            input_dir = input_dir.strip('"').replace('"','').replace("'","")
        
        input_file = os.path.join(input_dir, "draft_content.json")

        print('\n############\n1. 生成srt字幕文件\n2. 精准时间合并音频文件\n3. 连续时间合并音频文件\n4. 退出程序\n############\n')
        select = input("请输入数字===>：")
        if select == "1":
            print('\n############\n请输入要保存的文件（例如：aaa.srt）')
            output_file=input("请输入===>：")
            to_srt(input_file, output_file)
            print(f"{output_file} 字幕文件，任务完成！")
        elif select == "2":
            use_absolute_time = True
            print('\n############\n请输入要保存的文件（例如：aaa.mp3 bbb.wav）')
            output_file = input("请输入===>：")
            subtitles = get_subtitles(input_file)
            combine_audio_clips(subtitles, output_file, use_absolute_time)
            print(f"{output_file} 精准时间，语音合并完成！")
        elif select == "3":
            use_absolute_time = False
            print('\n############\n请输入要保存的文件（例如：aaa.mp3 bbb.wav）')
            output_file = input("请输入===>：")
            subtitles = get_subtitles(input_file)
            combine_audio_clips(subtitles, output_file, use_absolute_time)
            print(f"{output_file} 连续时间，合并完成！")
        elif select == "4":
            print("退出程序！")
            break
        else:
            print("输入错误！")
        print('\n\n================= 新任务 =================\n\n')
