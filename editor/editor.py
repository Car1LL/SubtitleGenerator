import regex
import shutil
import sys
import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException
from itertools import islice
from editor.helper import LoadingBar
import textwrap
import whisper


class SubtitleGenerator:
    SUBTITLE_PATH = "./temp/subs.srt"
    TEMP_PATH = "./temp/"
    TEMP_AUDIO = f"{TEMP_PATH}temp_audio.mp3"
    SUBTITLE_MODELS = ["tiny", "small", "medium", "large", "turbo"]
    FONTS = {
        "latin-cyrillic": "./fonts/Roboto-Regular.ttf",
        "asian": "./fonts/NotoSansSC.ttf",
        "arabic": "./fonts/NotoSansArabic.ttf"
    }

    @LoadingBar.simple_loading()
    def __init__(self, input_path, output_path, subtitle_model="small", set_language=None):
        """
        Initialize the SubtitleGenerator instance

        :param input_path: Path to input video file
        :type input_path: str

        :param output_path: Path to save the final video with subtitles
        :type output_path: str

        :param subtitle_model: Whisper model for subtitle generation. 
        Options: 'tiny', 'small', 'medium', 'large', 'turbo'
        :type subtitle_model: str

        :param set_language: Optional target language code for subtitle translation
        :type set_language: str, optional
        """
        self.input_path = input_path
        self.output_path = self.get_unique_filename(output_path)
        self.subtitle_model = subtitle_model
        self.set_language = set_language

        if subtitle_model not in SubtitleGenerator.SUBTITLE_MODELS:
            raise ValueError(
                f"Wrong model name {subtitle_model} for subtitle_model")
        if not os.path.exists(SubtitleGenerator.TEMP_PATH):
            os.makedirs(SubtitleGenerator.TEMP_PATH)

        self.model = whisper.load_model(self.subtitle_model)
        self.generate_temp_audio()

    def __str__(self):
        try:
            return f"Language is spoken in video: {self.detect_language()}"
        except FileNotFoundError:
            return f"No video currently uploaded or it was an error reading audio file"

    @LoadingBar.simple_loading(style_name="hash", length=20)
    def generate_srt(self):
        """
        Generate a SRT subtitle file based on the detected or selected language

        if 'set_language' is provided, the subtitle text will be translated before being 
        written to the file. Line width is adjusted based on character set (Latin or non-Latin)
        """
        segments = self.get_segments()

        if self.set_language:
            example_string = self.translate_text(
                self.set_language, segments[0]["text"])
        else:
            example_string = segments[0]["text"]

        if SubtitleGenerator.detect_script(example_string) == "latin-cyrillic":
            width = 65
        elif SubtitleGenerator.detect_script(example_string) == "asian":
            width = 22
        elif SubtitleGenerator.detect_script(example_string) == "arabic":
            width = 30
        else:
            raise ValueError(
                f"Could not define language font usage for {example_string}")

        with open(SubtitleGenerator.SUBTITLE_PATH, "w", encoding="utf-8") as f:
            for segment in segments:
                start = SubtitleGenerator.convert_time_to_srt_format(
                    segment.get("start"))
                end = SubtitleGenerator.convert_time_to_srt_format(
                    segment.get("end"))

                if self.set_language:
                    text = self.translate_text(
                        self.set_language, segment.get("text"))
                else:
                    text = segment.get("text")

                formatted_text = textwrap.fill(text.strip(), width=width)

                f.write(f"{segment.get('id')+1}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{formatted_text}\n\n")

    def get_segments(self) -> list:
        """
        Transcribes speech from the temporary audio file into text segments

        :raises FileNotFoundError: If the temporary audio file does not exist
        :return: List of segment dictionaries containing timestamps and text
        :rtype: list
        """

        if os.path.exists(SubtitleGenerator.TEMP_AUDIO):
            result = self.model.transcribe(
                SubtitleGenerator.TEMP_AUDIO,
                fp16=False,
                word_timestamps=True
            )
        else:
            raise FileNotFoundError("Path to audio does not exist")

        return result.get("segments")

    def detect_language(self) -> str:
        """
        Detects the spoken language in the audio file

        :return: Two-letter language code (e.g., 'en', 'es', 'ja')
        :rtype: str
        :raises FileNotFoundError: If audio file does not exist
        """

        if not os.path.exists(SubtitleGenerator.TEMP_AUDIO):
            raise FileNotFoundError(
                f"{SubtitleGenerator.TEMP_AUDIO} does not exist")
        audio = whisper.load_audio(SubtitleGenerator.TEMP_AUDIO)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(
            audio, n_mels=self.model.dims.n_mels).to(self.model.device)

        _, probs = self.model.detect_language(mel)

        return str(max(probs, key=probs.get))

    def generate_temp_audio(self):
        """
        Extracts the audio track from the input video and save it as temporary file.
        """
        with VideoFileClip(self.input_path) as clip:
            temp_audio = clip.audio
            temp_audio.write_audiofile(
                SubtitleGenerator.TEMP_AUDIO, logger=None)

    def translate_text(self, language: str, text: str) -> str:
        """
        Translate a given text into the specified target language

        :param language: Target language code
        :type language: str
        :param text: Text to translate
        :type text: str
        :return: Translated text
        :rtype: str
        """

        try:
            translated = GoogleTranslator(
                source="auto",
                target=language
            ).translate(text)
        except LanguageNotSupportedException:
            sys.exit("Unsupported language is set")

        return translated

    @staticmethod
    def get_supported_languages() -> dict:
        """
        Retrieve a dictionary of all language supported by GoogleTranslator.

        :return: Dictionary mapping language codes to language names
        :rtype: dict
        """
        _ = GoogleTranslator()
        return _.get_supported_languages(as_dict=True)

    @LoadingBar.simple_loading(style_name="dots", length=15)
    def apply_subtitles(self):
        """
        Render subtitles onto the original video and save the final output file.

        The method detects which font to use based on the first subtitle line,
        merges the subtitles with the input video, and clears the temporary 
        directory afterwards

        """
        with open(SubtitleGenerator.SUBTITLE_PATH, "r", encoding="utf-8") as f:
            lines = list(islice(f, 3))
            text = lines[2]

            if SubtitleGenerator.detect_script(text) == "latin-cyrillic":
                font = SubtitleGenerator.FONTS.get("latin-cyrillic")
                font_size = 32
                stroke_width = 3
            elif SubtitleGenerator.detect_script(text) == "asian":
                font = SubtitleGenerator.FONTS.get("asian")
                font_size = 36
                stroke_width = 6
            elif SubtitleGenerator.detect_script(text) == "arabic":
                font = SubtitleGenerator.FONTS.get("arabic")
                font_size = 34
                stroke_width = 4
            else:
                raise ValueError(
                    f"Could not define language usage font for {text}")

        with VideoFileClip(self.input_path) as clip:
            def generator(text): return TextClip(
                text=text,
                font=font,
                font_size=font_size,
                stroke_color="black",
                stroke_width=stroke_width,
                color="white",
                text_align="center",
                margin=(None, None, None, 20),
                transparent=True
            )

            with SubtitlesClip(subtitles=SubtitleGenerator.SUBTITLE_PATH, make_textclip=generator, encoding="utf-8") as sub_clip:
                with CompositeVideoClip(
                    (clip, sub_clip.with_position(("center", "bottom"))),
                    size=clip.size
                ) as result:
                    result.write_videofile(
                        filename=self.output_path,
                        fps=clip.fps,
                        threads=8,
                        temp_audiofile_path=SubtitleGenerator.TEMP_PATH,
                        logger=None
                    )

    def get_unique_filename(self, path: str) -> str:
        """
        Generate a unique file path by appending a counter if the file already exists

        :param path: Original desired file path
        :type path: str

        :return: Unique file path that does not currently exists
        :rtype: str
        """
        if not os.path.exists(path):
            return path

        directory, filename = os.path.split(path)
        name, ext = os.path.splitext(filename)

        counter = 1
        while True:
            new_name = f"{name} ({counter}){ext}"
            new_path = os.path.join(directory, new_name)

            if not os.path.exists(new_path):
                return new_path

            counter += 1

    @classmethod
    def detect_script(cls, text: str) -> str | None:
        """
        Detect the writing system of the given text

        The method analyzes the entire string and determines which script is belongs to.
        The text must consist exclusively of characters from one script category, with punctuation 
        marks allowed

        If the text contains a mixture of scripts or unsupported characters, None is returned

        :param text: Text to analyze
        :type text: str

        :return: Detected script identifier or None if the script cannot be determined
        :rtype: str | None
        """
        text = text.strip()

        if not text:
            return None

        if (
            regex.fullmatch(r"[\p{Arabic}\p{Common}\p{Inherited}]+", text) and
            regex.search(r"\p{Arabic}", text)
        ):
            return "arabic"

        if (
            regex.fullmatch(r"[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}\p{Common}\p{Inherited}]+", text) and
            regex.search(r"[\p{Han}\p{Hiragana}\p{Katakana}\p{Hangul}]", text)
        ):
            return "asian"

        if (
            regex.fullmatch(r"[\p{Latin}\p{Cyrillic}\p{Common}\p{Inherited}]+", text) and
            regex.search(r"[\p{Latin}\p{Cyrillic}]", text)
        ):
            return "latin-cyrillic"

        return None

        # pattern = r"[\p{Latin}\p{Cyrillic} \-'!.,:;\?\"]+"
        # return bool(regex.fullmatch(pattern, text))

    @classmethod
    def convert_time_to_srt_format(cls, time: float) -> str:
        """
        Convert a floating point time value (seconds) into SRT time format

        :param time: Time in seconds (e.g., 5.25)
        :type time: float
        :return: Time formatted as 'HH:MM:SS,mmm'
        :rtype: str
        """

        # seconds = int(time)
        # milliseconds = int((time - seconds) * 1000)
        # hours = seconds // 3600
        # minutes = (seconds % 3600) // 60
        # seconds = seconds % 60

        total_milliseconds = int(round(time * 1000))

        seconds, milliseconds = divmod(total_milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    @classmethod
    def clean_temp(cls):
        """
        Delete all files and subdirectories inside the temporary directory

        :raises: FileNotFoundError: if the temporary directory does not exist
        """
        if not os.path.exists(SubtitleGenerator.TEMP_PATH):
            raise FileNotFoundError("temp directory does not exist")

        for item in os.listdir(SubtitleGenerator.TEMP_PATH):
            path = os.path.join(SubtitleGenerator.TEMP_PATH, item)

            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

    def run(self):
        """
        Run the full subtitle generation and video rendering pipeline

        If a target language is specified, subtitles will be translated before rending.
        Temporary files are cleaned up after processing
        """
        if self.set_language:
            self.generate_srt()
            self.apply_subtitles()
            SubtitleGenerator.clean_temp()
        else:
            self.generate_srt()
            self.apply_subtitles()
            SubtitleGenerator.clean_temp()
