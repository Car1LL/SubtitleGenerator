import argparse
import pyfiglet
import os
import sys
from editor.helper import LoadingBar
from editor.editor import SubtitleGenerator


def main():
    args = get_args()
    start_menu(args)


def get_args() -> tuple:
    """
    Parse and validate command-line arguments for the program

    Checks the existence of input and output paths, ensures they are not identical, and
    that the file formats are '.mp4'. Optionally, retrieves the subtitle model name.

    :return: Tuple containing input path, output path, and optionally the subtitle model
    :rtype: tuple

    :raises FileNotFoundError: If the input file does not exists
    :raises FileNotFoundError: If input and output paths are the same
    :raises ValueError: If input and output file extensions are not '.mp4'
    """

    parser = argparse.ArgumentParser(description="Video Processing Tool")

    parser.add_argument("--input", "-i", required=True,
                        help="Input path to video file")
    parser.add_argument("--output", "-o", required=True,
                        help="Output path to video file")
    parser.add_argument(
        "--subs", "-s", help="Choose model for generating subtitles.\n"
        "Available models: ['tiny', 'small', 'medium', 'large', 'turbo']"
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"{args.input} does not exists")
    if args.input == args.output:
        raise FileExistsError(f"Input and output files share the same name")
    if not args.input.endswith(".mp4") or not args.output.endswith(".mp4"):
        raise ValueError("Input and Output format should be '.mp4'")
    if args.subs:
        return (args.input, args.output, args.subs)

    return (args.input, args.output)


def start_menu(args):
    """
    Display an interactive menu to the user.

    Allows user:
    1. Add subtitles
    2. Add translated subtitles
    3. Exit the program

    Handles user input, validates language codes for translation and runs the
    SubtitleGenerator with appropriate settings.

    :param args: Arguments to run the Subtitle Generator
    :type args: tuple
    """
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print(pyfiglet.figlet_format(
            "Subtitle Generator", font="doom"))
        print("1. Add subtitles")
        print("2. Add translated subtitles")
        print("3. Exit\n")

        choice = input("Choice: ")

        match choice:
            case "1":
                video = SubtitleGenerator(*args)
                video.run()
                LoadingBar.clean_terminal()
                print(f"Done, video located at: {video.output_path}")
                input("Press Enter to return to menu...")

            case "2":
                while True:
                    language = input(
                        "Select language for subtitles: ").strip()
                    if is_valid_language(language):
                        break
                    print(f"'{language}' is invalid code. Please try again")
                    print("Supported code languages:\n")
                    for k, v in SubtitleGenerator.get_supported_languages().items():
                        print(f"{k} = '{v}'")
                    print("\n")

                video = SubtitleGenerator(*args, set_language=language)
                video.run()
                LoadingBar.clean_terminal()
                print(f"Done, video located at {video.output_path}")
                input("Press Enter to return to menu...")

            case "3":
                LoadingBar.clean_terminal()
                sys.exit("Exiting...")

            case _:
                input("Unknown choice. Press Enter to continue...")


def is_valid_language(code: str) -> bool:
    """
    Checks if given string satisfies code language system

    :param code: String to be checked
    :type code: str

    :return: True if string is in language code system, False otherwise
    :rtype: bool
    """

    return code in SubtitleGenerator.get_supported_languages().values()


if __name__ == "__main__":
    main()
