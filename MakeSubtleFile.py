import speech_recognition as sr
from moviepy.editor import *
from janome.tokenizer import Tokenizer
import csv
import os
from PIL import Image, ImageDraw, ImageFont


def extract_audio_from_video(video_path):
    video = VideoFileClip(video_path)
    audio_path = "document/temp_audio.wav"
    video.audio.write_audiofile(audio_path)
    return audio_path


def recognize_audio_with_speechrecognition(audio_path):
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data, language="ja-JP")
            return text
        except sr.UnknownValueError:
            return "音声認識ができませんでした"
        except sr.RequestError:
            return "APIのリクエストに失敗しました"


def split_text_with_janome(text, max_length=30):
    t = Tokenizer()
    tokens = t.tokenize(text)
    chunks = []
    chunk = ""
    for token in tokens:
        if len(chunk + token.surface) > max_length:
            chunks.append(chunk)
            chunk = ""
        chunk += token.surface
    if chunk:
        chunks.append(chunk)
    return chunks


def text_to_png(text, font_path, output_path, font_size=24):
    font = ImageFont.truetype(font_path, font_size)
    width, height = font.getsize(text)
    img = Image.new('RGBA', (width + 10, height + 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((5, 5), text, font=font, fill="white")
    img.save(output_path, "PNG")


def add_subtitles_to_video(video_path, subtitles, font_path="path_to_your_font.ttf"):
    video = VideoFileClip(video_path)
    duration_per_subtitle = video.duration / len(subtitles)

    annotated_clips = []
    for idx, subtitle in enumerate(subtitles):
        start_time = idx * duration_per_subtitle
        end_time = (idx + 1) * duration_per_subtitle

        # 字幕テキストをPNGとして保存
        png_path = f"temp_subtitle_{idx}.png"
        text_to_png(subtitle, font_path, png_path)

        clip = video.subclip(start_time, end_time)
        img_clip = ImageClip(png_path).set_duration(duration_per_subtitle).set_position(("center", "bottom"))
        annotated_clip = CompositeVideoClip([clip, img_clip])
        annotated_clips.append(annotated_clip)

    final_video = concatenate_videoclips(annotated_clips, method="compose")
    final_video = final_video.set_audio(video.audio)  # Ensure the original audio is used
    output_path = "document/with_subtitles.mp4"
    final_video.write_videofile(output_path, audio_codec='aac')  # Specify audio codec

    return output_path


def main():
    video_path = "document/toyama.mp4"
    csv_path = "document/subtitles.csv"
    font_path = "/Library/Fonts/Arial Unicode.ttf"  # ここに適切なフォントのパスを指定してください

    # If subtitles.csv exists, load subtitles from it, otherwise recognize and save them
    if os.path.exists(csv_path):
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            subtitles = [row[0] for row in reader]
    else:
        audio_path_candidate = video_path.replace(".mp4", ".wav")
        if os.path.exists(audio_path_candidate):
            audio_path = audio_path_candidate
        else:
            audio_path = extract_audio_from_video(video_path)

        text = recognize_audio_with_speechrecognition(audio_path)
        subtitles = split_text_with_janome(text)

        with open(csv_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for subtitle in subtitles:
                writer.writerow([subtitle])

    output_video_path = add_subtitles_to_video(video_path, subtitles, font_path)

    print(f"字幕付きの動画: {output_video_path}")
    print(f"字幕の内容を保存したCSV: {csv_path}")


main()
