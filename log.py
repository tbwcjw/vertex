import builtins
import time
import inspect
import os
import sys
import threading
import queue
from configloader import ConfigLoader

config = ConfigLoader()

class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Log:
    def __init__(self, format_string='{time} - {level} - {module}.{function} - {message}'):
        self.original_print = builtins.print
        self.write_log = config.get('log.write_log')
        self.print_log = config.get('log.print_log')
        self.log_file = config.get('log.log_file')
        self.format_string = format_string
        self.log_queue = queue.Queue()
        self.is_running = True
        
        if self.write_log:
            self.log_thread = threading.Thread(target=self._write_logs, name="log writer")
            self.log_thread.start()

    def __call__(self, *args, log_level=LogLevel.INFO, **kwargs):
        frame = inspect.currentframe().f_back  
        frame_info = inspect.getframeinfo(frame)
        caller = frame.f_code.co_name
        filename = os.path.basename(frame_info.filename)[:-3]

        message = " ".join(map(str, args))
        log_string = self.format_string.format(
            time=time.asctime(),
            level=log_level,
            module=filename,
            function=caller,
            message=message
        )

        if self.print_log:
            self.original_print(log_string)

        if self.write_log:
            self.log_queue.put(log_string)

    def _write_logs(self):
        while self.is_running:
            try:
                log_string = self.log_queue.get(timeout=1)  
                with open(self.log_file, 'a', encoding='utf-8') as log_file:
                    log_file.write(log_string + '\n')
                self.log_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        self.is_running = False
        self.log_thread.join()

builtins.print = Log(format_string=config.get("log.log_format"))

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    print(f"{exc_type.__name__}: {exc_value}", log_level=LogLevel.ERROR)

sys.excepthook = handle_exception
