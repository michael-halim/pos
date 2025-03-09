from PyQt6.QtCore import QObject, pyqtSignal, QThread
import traceback
import logging

logger = logging.getLogger(__name__)

class WorkerThread(QThread):
    """
    A worker thread that runs a function with arguments.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        """
        Execute the function with the provided arguments.
        This method is automatically called when the thread starts.
        """
        try:
            self.progress.emit(0)
            result = self.function(*self.args, **self.kwargs)
            self.progress.emit(50)
            self.finished.emit(result)
            self.progress.emit(100)

        except Exception as e:
            error_msg = f"Error in worker thread: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.error.emit(str(e))


class ThreadManager:
    """
    Manages the creation and execution of background threads.
    """
    def __init__(self):
        self.threads = []
        
    def run_in_thread(self, function, on_finished=None, on_error=None, on_progress=None, *args, **kwargs):
        """
        Run a function in a background thread.
        
        Args:
            function: The function to execute
            on_finished: Callback for when the function completes successfully
            on_error: Callback for when an error occurs
            on_progress: Callback for progress updates
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The created thread object
        """
        # Create a worker thread
        thread = WorkerThread(function, *args, **kwargs)
        
        # Connect signals
        if on_finished:
            thread.finished.connect(on_finished)
        
        if on_error:
            thread.error.connect(on_error)
            
        if on_progress:
            thread.progress.connect(on_progress)
        
        # Keep track of the thread
        self.threads.append(thread)
        
        # Connect cleanup
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.error.connect(lambda: self._cleanup_thread(thread))
        
        # Start the thread
        thread.start()
        
        return thread
    
    def _cleanup_thread(self, thread):
        """Remove the thread from our list when it's done"""
        if thread in self.threads:
            self.threads.remove(thread) 