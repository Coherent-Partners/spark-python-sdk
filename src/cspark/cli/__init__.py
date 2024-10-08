try:
    from ._main import main
except ImportError:

    def main() -> None:
        import sys

        print(  # noqa: T201
            'The cspark command line client could not run because the required '
            'dependencies were not installed.\nMake sure you have installed '
            "everything with: pip install 'cspark[cli]'"
        )
        sys.exit(1)