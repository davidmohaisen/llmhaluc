import threading

class Progress:
    def __init__(self):
        self.file_progress = 0
        self.total_progress = 0
        self.lock = threading.Lock()

    def update(self, file_progress, total_progress):
        with self.lock:
            self.file_progress = file_progress
            self.total_progress = total_progress

    def get(self):
        with self.lock:
            return self.file_progress, self.total_progress

progress = Progress()

def update_progress(file_index, total_files, obj_index, total_objects):
    file_progress = (obj_index / total_objects) * 100
    total_progress = ((file_index - 1 + (obj_index / total_objects)) / total_files) * 100
    progress.update(file_progress, total_progress)