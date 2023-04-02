import logging
import sys
import time
from tkrminal import make_terminal


def main():
    logging.basicConfig(level=logging.INFO)
    time.sleep(1)
    print("Printing here")
    time.sleep(1)
    print("To stderr too", file=sys.stderr)
    time.sleep(1)
    logging.info("And logging as well")
    time.sleep(1)


if __name__ == '__main__':
    def open_browser():
        pass

    def quit():
        sys.exit(0)

    make_terminal(
        main,
        title="Taguette",
        actions=[
            ("Open browser", open_browser),
            ("Quit", quit),
        ],
    )
