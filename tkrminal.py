import asyncio
import asyncio.protocols
import asyncio.subprocess
import sys
import threading
import tkinter as tk
import traceback
from tkinter import ttk


def _make_terminal(*, title="Terminal", actions=None, max_lines=1000):
    # Create window
    root = tk.Tk()
    root.title(title)

    # Create frame
    mainframe = ttk.Frame(root, padding="3 3 3 3")
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    mainframe.columnconfigure(len(actions) + 1, weight=1)
    mainframe.rowconfigure(2, weight=1)

    # The buttons
    for col, (label, callback) in enumerate(actions or ()):
        button = ttk.Button(
            mainframe,
            text=label,
            command=callback,
        )
        button.grid(column=col + 1, row=1)
    ttk.Frame(root).grid(column=len(actions) + 1, row=1)

    # The console
    console = tk.Text(mainframe)
    console.grid(column=1, row=2, columnspan=len(actions) + 1, sticky=(tk.N, tk.W, tk.E, tk.S))

    def add_text(text):
        console.insert('end', text)
        lines = int(console.index('end - 1 line').split('.')[0]) - 1
        if lines > max_lines:
            console.delete('1.0', '%d.0' % (lines - max_lines + 1))

    # Set up the cross-thread signaling
    add_text_queue = []
    mutex = threading.Lock()

    def add_text_from_queue():
        with mutex:
            for line in add_text_queue:
                add_text(line)
            add_text_queue.clear()

    root.bind('<<AddLineToConsole>>', lambda *args: add_text_from_queue())

    def add_text_threadsafe(text):
        with mutex:
            add_text_queue.append(text)
        root.event_generate('<<AddLineToConsole>>', when='tail')

    root.bind('<<QuitTerminal>>', lambda *args: root.quit())

    def stop_threadsafe():
        root.event_generate('<<QuitTerminal>>', when='tail')

    return root.mainloop, add_text_threadsafe, stop_threadsafe


def run_in_terminal(cmd, *, title="Terminal", actions=None, max_lines=1000):
    run, add_text, stop = _make_terminal(
        title=title,
        actions=actions,
        max_lines=max_lines,
    )

    # Start an asyncio event loop in a thread and run the command
    thread = threading.Thread(
        target=lambda: _start_process(
            cmd,
            add_text,
        ),
    )
    thread.daemon = True
    thread.start()

    run()


def make_terminal(func, *, title="Terminal", actions=None, max_lines=1000):
    run, add_text, stop = _make_terminal(
        title=title,
        actions=actions,
        max_lines=max_lines,
    )

    sys.stdout = TextFileWrapper(add_text)
    sys.stderr = TextFileWrapper(add_text)

    def wrapper():
        try:
            func()
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
        finally:
            stop()

    thread = threading.Thread(
        target=wrapper,
    )
    thread.start()

    run()


class TextFileWrapper(object):
    def __init__(self, add_text):
        self._write = add_text
        self.buffer = BytesFileWrapper(add_text)

    def write(self, data):
        self._write(data)
        return len(data)

    def flush(self):
        pass

    def isatty(self):
        return False

    line_buffering = True
    mode = 'w'
    newlines = None


class BytesFileWrapper(object):
    def __init__(self, add_text):
        self._write = add_text

    def write(self, data):
        self._write(data.decode('utf-8', 'replace'))
        return len(data)

    def flush(self):
        pass

    def isatty(self):
        return False

    mode = 'w'


def _start_process(cmd, add_text):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(loop.subprocess_exec(
        lambda: ProcessProtocol(add_text),
        *cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    ))
    loop.run_forever()


class ProcessProtocol(asyncio.protocols.SubprocessProtocol):
    def __init__(self, add_text):
        self.add_text = add_text
        self.transport = None

    def connection_made(self, transport):
        self.add_text("Process started\n")
        self.transport = transport

    def pipe_data_received(self, fd, data):
        self.add_text(data)

    def process_exited(self):
        retcode = self.transport.get_returncode()
        self.add_text("Process exited with status %d" % retcode)
