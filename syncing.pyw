import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class FolderChangeHandler(FileSystemEventHandler):
    def __init__(self, source_folder, target_folder):
        self.source_folder = source_folder
        self.target_folder = target_folder

    def _files_are_identical(self, src_path, target_path):
        """Check if two files are identical based on modification time and size."""
        if not os.path.exists(target_path):
            return False
        src_stat = os.stat(src_path)
        target_stat = os.stat(target_path)
        return src_stat.st_mtime == target_stat.st_mtime and src_stat.st_size == target_stat.st_size

    def _sync_file(self, src_path):
        """Sync a file from source to target if it's newer or missing."""
        if not os.path.exists(src_path):
            print(f"File does not exist (skipping): {src_path}")
            return

        # Skip temporary files
        if src_path.endswith(".tmp") or "DotNetZip" in src_path:
            print(f"Temporary file ignored: {src_path}")
            return

        relative_path = os.path.relpath(src_path, self.source_folder)
        target_path = os.path.join(self.target_folder, relative_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Skip if files are identical
        if self._files_are_identical(src_path, target_path):
            print(f"File identical (skipping): {src_path}")
            return

        try:
            shutil.copy2(src_path, target_path)
            print(f"File synced: {src_path} -> {target_path}")
        except Exception as e:
            print(f"Error copying file {src_path}: {e}")

    def _remove_file(self, src_path):
        """Remove a file from the target folder if it no longer exists in the source."""
        relative_path = os.path.relpath(src_path, self.source_folder)
        target_path = os.path.join(self.target_folder, relative_path)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                print(f"File removed: {target_path}")
            except Exception as e:
                print(f"Error removing file {target_path}: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._sync_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            # Delay to handle files still being written
            time.sleep(0.1)
            self._sync_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._remove_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._remove_file(event.src_path)
            self._sync_file(event.dest_path)

def monitor_folders(folder_pairs):
    observers = []

    for source_folder, target_folder in folder_pairs:
        event_handler = FolderChangeHandler(source_folder, target_folder)
        observer = Observer()
        observer.schedule(event_handler, source_folder, recursive=True)
        observers.append(observer)
        observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()

if __name__ == "__main__":
    tmodLoader_Players_Folder = r"C:\Users\Tuan\Documents\My Games\Terraria\tModLoader\Players"
    terraria_Players_Folder = r"C:\Users\Tuan\Documents\My Games\Terraria\Players"
    tmodLoader_Worlds_Folder = r"C:\Users\Tuan\Documents\My Games\Terraria\tModLoader\Worlds"
    terraria_Worlds_Folder = r"C:\Users\Tuan\Documents\My Games\Terraria\Worlds"

    folder_pairs = [
        # Synchronize Players folder
        (tmodLoader_Players_Folder, terraria_Players_Folder),
        (terraria_Players_Folder, tmodLoader_Players_Folder),
        # Synchronize Worlds folder
        (tmodLoader_Worlds_Folder, terraria_Worlds_Folder),
        (terraria_Worlds_Folder, tmodLoader_Worlds_Folder),
    ]

    monitor_folders(folder_pairs)
