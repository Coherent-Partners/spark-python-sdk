try:
    from ._main import __version__, main  # noqa: F401
except ImportError:

    def main() -> None:
        import sys

        print(  # noqa: T201
            'The cspark command-line client could not run because the required '
            'dependencies were not installed.\nMake sure you have installed '
            f"everything with: \x1b[32mpip install 'cspark[cli]'\x1b[39m"
        )
        sys.exit(1)
