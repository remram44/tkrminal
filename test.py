import sys
from tkrminal import run_in_terminal


if __name__ == '__main__':
    def open_browser():
        pass

    def quit():
        sys.exit(0)

    run_in_terminal(
        ['sh', '-c', 'i=0; while [ $i -lt 5 ]; do i=$((i + 1)); sleep 1; echo "line $i"; done'],
        title="Taguette",
        actions=[
            ("Open browser", open_browser),
            ("Quit", quit),
        ],
    )
