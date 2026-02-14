import time
import threading
import os
import re
import sys


class LoadingBar:
    @classmethod
    def get_style(cls, style_name: str, length: int) -> list:
        """
        Returns frames of a loading bar according to the specified style.

        :param style_name: Name of the loading style. Options:
        'simple', 'hash', 'blocks', 'dots'
        :type style_name: str

        :param length: Length of the loading bar (number of steps or characters)
        Must be between 1 and 20
        :type length: int

        :return: List of strings representing frames of the loading animation
        :rtype: list

        :raises ValueError: If length is not an integer or out of the range 1-20
        :raises ValueError: If style_name is invalid
        """

        if not isinstance(length, int):
            raise ValueError(f"{length} must be int")
        if length > 20:
            raise ValueError("n is too big")
        if length <= 0:
            raise ValueError("n can't be less or equal zero")

        match style_name:
            case "simple":
                return ["|", "/", "-", "\\"]
            case "hash":
                return ["[" + "#" * i + "-" * (length - i) + "]" for i in range(1, length+1)]
            case "blocks":
                return ["| " + "█" * i + "░" * (length - i) + " |" for i in range(1, length+1)]
            case "dots":
                return ["⠾", "⠷", "⠯", "⠟", "⠻", "⠽",]
            case _:
                raise ValueError(f"{style_name} not found")

    @classmethod
    def simple_loading(cls, style_name="simple", length=10):
        """
        Decorator to display a loading animation while function executes.

        If applied to a class method, the decorator will automatically determine 
        the class name to display more information. Otherwise, the class name
        will be set to None and ignored

        Note: The decorator may not behave correctly with functions that manipulate
        stdout heavily or use loops internally

        :param style_name: Name of the style that will be used for the animation.
        Options: 'simple', 'hash', 'blocks', 'dots'
        :type style_name: str

        :param length: Length of the loading bar (1-20)
        :type length: int

        :return: Decorated function with loading animation
        :rtype: function

        """
        def decorator(f):
            def wrap(*args, **kwargs):
                stop_event = threading.Event()
                func_name = f.__name__
                formatted_name = cls.format_func_name(func_name)

                instance = args[0] if args else None
                class_name = instance.__class__.__name__ if instance else None

                style = cls.get_style(style_name, length)
                repeat = 5 if style_name == "simple" else 1

                t = threading.Thread(target=cls._animate, args=(
                    formatted_name, style, repeat, class_name, stop_event))
                t.start()

                try:
                    result = f(*args, **kwargs)
                except KeyboardInterrupt:
                    stop_event.set()
                    t.join()
                    raise
                finally:
                    stop_event.set()
                    t.join()

                return result
            return wrap
        return decorator

    @classmethod
    def format_func_name(cls, func_name: str) -> str:
        """
        Format a function name into one or more separated words
        If function name is 'init', it is replaced with 'Initialization'

        :param func_name: Original function name (e.g., my_custom_function)
        :type func_name: str

        :return: New formatted name
        :rtype: str
        """
        words = [w for w in func_name.split("_") if w]

        first_word = words[0].lower().strip()

        if first_word == "init":
            first_word = "Initialization"

        rest_words = [word.title() for word in words[1:]]
        formatted_name = " ".join([first_word.title()] + rest_words)

        return formatted_name

    @staticmethod
    def _animate(formatted_name: str, style: list, repeat: int, class_name: str, stop_event: threading.Event):
        """
        Animate the loading bar in a separated thread, until stop_event is set

        :param formatted_name: Formatted name of the function being executed
        :type formatted_name: str

        :param style: List of strings representing the animation frames
        :type style: list

        :param repeat: Number of times each frame should repeat horizontally
        :type repeat: int

        :param class_name: Name of the current class on which method decorator is applied to
        :type class_name: str

        :param stop_event: Event to signal the animation thread to stop
        :type stop_event: threading.Event
        """
        LoadingBar.clean_terminal()

        idx = 0
        prefix = f"{class_name}: Loading -->" if class_name else "Loading -->"
        formatted_name = formatted_name.strip()

        while not stop_event.is_set():
            frame = style[idx % len(style)] * repeat
            loading_string = f"\r{prefix} {formatted_name} ... {frame} "
            sys.stdout.write(loading_string)
            sys.stdout.flush()
            idx += 1
            time.sleep(0.25)

        sys.stdout.write("\r" + " " * (len(loading_string)) + "\r")
        sys.stdout.write(f"{prefix} {formatted_name} ... Done.\n")
        sys.stdout.flush()

        # while not stop_event.is_set():
        #     loading_string = f"\r{prefix} {formatted_name.strip()} ... {style[idx % len(style)] * repeat} {" " * 20}"
        #     sys.stdout.write(loading_string)
        #     sys.stdout.flush()
        #     idx += 1
        #     time.sleep(0.25)

        # LoadingBar.clean_terminal()
        # sys.stdout.write("Done.\n")
        # sys.stdout.flush()

    @staticmethod
    def clean_terminal():
        """
        Cleans the terminal for both Windows and Unix systems.
        """
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def split_camel(s: str) -> str:
        """
        Split a CamelCase string into separated words

        :param s: String in Camel case
        :type s: str

        :return: New string with words separated by spaces
        :rtype: str

        :raises ValueError: if s is not an instance of str
        """
        if not isinstance(s, str):
            raise ValueError("Parameter should be a string")

        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
        s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)

        return s
