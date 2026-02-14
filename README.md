# Subtitle Generator

# Video url - [Video](https://youtu.be/hilEnPWXGao)

## Features

- [MoviePy](https://zulko.github.io/moviepy/)
- [Whisper-OpenAI](https://pypi.org/project/openai-whisper/)
- [Deep-Translator](https://pypi.org/project/deep-translator/)

My project is a simple program designed to create subtitles for videos in different languages. I use the **MoviePy** library as a main tool to render and edit videos. 
**Whisper-OpenAI** is a powerful open-source set of models that transcribes speech into text with quite good quality. 
**Deep-Translator** is also an open-source library that provides various language sets and helps translate text directly inside the code.

## Additional files

- ### `./editor/editor.py`:
 This file contains all the main logic. It includes single class - `SubtitleGenerator`, which comes with several methods. `SubtitleGenerator` analyzes the input video, extracts its audio to generate an SRT file, and then creates a new copy of the video with subtitles attached. The class has two main logic methods:

1. `generate_srt()`: Extracts segments from a temporary audio file, using **Whisper-OpenAI**. Each segment contains timestamps and text. Using this information, `generate_srt()` dynamically creates an SRT file. It can optionally translate text if language is specified by user. 
What is an SRT file? 
SRT (SubRip Subtitle) - is a subtitle format where each entry contains an ID number, timestamps, and the text. Example:
```
1
00.00.00,000 --> 00.00.03,125
Hello, World!
```
2. `apply_subtitles()`: Using **MoviePy** this method creates a new **TextClip** based on the generated SRT fle. It then produces a new copy of the input video with subtitles added. 

#### How to use:
```python
    video = SubtitleGenerator(
        input_path="input.mp4",
        output_path="output.mp4",
        set_language="en",
        subtitle_model="small"
    )
    video.run()

```

- ### `./editor/helper.py`:
 This file contains a single class - `LoadingBar`. The main reason for creating this class is that **MoviePy** uses many loops and **NumPy** matrices to render each frame of the video. As a result, some videos may take several minutes (or even longer) to render. `LoadingBar` solves this problem by displaying simple loading animation so the user knows the program is working and not frozen. 

##### Why use custom class instead of existing libraries?
 Libraries such as **rich** or **tqdm** can show a progress bar only when they are applied to a function that explicitly uses a loop. However, **MoviePy** runs loops deep under the hood, so tools like **tqdm** simply fail to work.
 `LoadingBar` creates a separate thread with a simple animation that does not block the main thread. It has different animation styles and is easy to use, even outside of this project.
#### Hot to use:

```python
    @LoadingBar.simple_loading(style="hash")
    def heavy_func():
        ...
```

## Additional info

`SubtitleGenerator` also uses method called `detect_script()`. This method helps adjust how subtitles should be displayed. For example, some fonts cannot display Japanese characters. `detect_script()` determines which language is being used for subtitles, and helps configure the correct font, size and other text parameters.

## How to run it?
run program using `python project.py` and then specified necessary parameters
```
    python project.py --input input_video.mp4 --output output_video.mp4
```