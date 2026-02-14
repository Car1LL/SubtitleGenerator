import pytest
from unittest import mock
import os
import sys
from project import *


def test_is_valid_language():
    assert is_valid_language("en") == True
    assert is_valid_language("es") == True
    assert is_valid_language("English") == False
    assert is_valid_language("EN") == False


@mock.patch("os.path.exists")
@mock.patch("sys.argv", new_callable=lambda: ["prog", "--input", "input.mp4", "--output", "output.mp4"])
def test_get_args(mock_argv, mock_exists):
    mock_exists.return_value = True

    result = get_args()

    assert result == ("input.mp4", "output.mp4")


@mock.patch("os.path.exists")
@mock.patch("sys.argv", new_callable=lambda: ["prog", "--input", "input.mp4", "--output", "output.mp4", "--subs", "small"])
def test_get_args_with_subs(mock_argv, mock_exists):
    mock_exists.return_value = True
    result = get_args()
    assert result == ("input.mp4", "output.mp4", "small")


@mock.patch("os.path.exists")
@mock.patch("sys.argv", new_callable=lambda: ["prog", "--input", "missing.mp4", "--output", "output.mp4"])
def test_get_args_input_not_exist(mock_argv, mock_exists):
    mock_exists.return_value = False

    with pytest.raises(FileNotFoundError):
        get_args()


@mock.patch("os.path.exists")
@mock.patch("sys.argv", new_callable=lambda: ["prog", "--input", "file.mp4", "--output", "file.mp4"])
def test_get_args_same_input_output(mock_argv, mock_exists):
    mock_exists.return_value = True
    with pytest.raises(FileExistsError):
        get_args()


@mock.patch("os.path.exists")
@mock.patch("sys.argv", new_callable=lambda: ["prog", "--input", "file.wav", "--output", "file.mp3"])
def test_get_args_wrong_extensions(mock_argv, mock_exists):
    mock_exists.return_value = True
    with pytest.raises(ValueError):
        get_args()
