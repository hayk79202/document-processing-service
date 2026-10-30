import asyncio
import io
import os
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, UploadFile

from app import storage
from app.main import get_document, upload_document


class DocumentServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("DOCUMENT_DB_PATH")
        os.environ["DOCUMENT_DB_PATH"] = str(Path(self.temp.name) / "jobs.sqlite3")
        storage.init_db()

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("DOCUMENT_DB_PATH", None)
        else:
            os.environ["DOCUMENT_DB_PATH"] = self.previous
        self.temp.cleanup()

    def test_upload_processes_and_persists_result(self):
        async def exercise():
            tasks = BackgroundTasks()
            upload = UploadFile(file=io.BytesIO(b"hello world"), filename="note.txt")
            response = await upload_document(tasks, upload)
            self.assertEqual(get_document(response["job_id"])["status"], "queued")
            await tasks()
            return get_document(response["job_id"])

        job = asyncio.run(exercise())
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["result"]["words"], 2)
        self.assertEqual(job["result"]["sha256"], sha256(b"hello world").hexdigest())
        self.assertEqual(storage.get_job(job["job_id"]), job)

    def test_rejects_non_text_file(self):
        upload = UploadFile(file=io.BytesIO(b"binary"), filename="photo.png")
        with self.assertRaises(HTTPException) as context:
            asyncio.run(upload_document(BackgroundTasks(), upload))
        self.assertEqual(context.exception.status_code, 415)

    def test_missing_job_is_404(self):
        with self.assertRaises(HTTPException) as context:
            get_document("missing")
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
