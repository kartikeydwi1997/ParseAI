import os
import zipfile
import tarfile
import uuid
import shutil


class ArchiveExtractor:
    def __init__(self, file_name, file_contents, project_id):
        """
        Initialize the ArchiveHandler with a file path.

        Args:
            file_path (str): Path to the archive file
        """
        self.file_name = file_name
        self.file_contents = file_contents
        self.project_id = project_id

    def extract_and_get_tree(self):
        """
        Extract the archive based on its extension and return the file tree.
        """
        # Get the file extension
        file_extension = self.file_name.split(".")[-1].lower()

        with open(self.file_name, "wb") as f:
            f.write(self.file_contents)

        # Extract based on file extension
        if file_extension == "zip":
            self._extract_zip()
        elif file_extension in ["gz", "tar", "tgz"]:
            self._extract_tar()
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

        os.remove(self.file_name)

    def _extract_zip(self):
        """Extract a zip file to the extracted_path directory."""
        os.makedirs(self.project_id, exist_ok=True)

        with zipfile.ZipFile(self.file_name, "r") as zip_ref:
            zip_ref.extractall(self.project_id)

    def _extract_tar(self):
        """Extract a tar or gzip file to the extracted_path directory."""
        os.makedirs(self.project_id, exist_ok=True)

        with tarfile.open(self.file_name, "r:*") as tar_ref:
            tar_ref.extractall(self.project_id)

    def cleanup(self):
        """Remove the extracted directory."""
        shutil.rmtree(self.project_id)
