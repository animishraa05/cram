"""cram - Spaced repetition TUI for problems and concepts with FSRS scheduling."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cram")
except PackageNotFoundError:
    __version__ = "0.0.0"
