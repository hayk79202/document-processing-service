import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


class DocumentHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("DOCUMENT_DB_PATH")
        os.environ["DOCUMENT_DB_PATH"] = str(Path(self.temp.name) / "jobs.sqlite3")

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("DOCUMENT_DB_PATH", None)
        else:
            os.environ["DOCUMENT_DB_PATH"] = self.previous
        self.temp.cleanup()

    def test_upload_lookup_and_listing_over_http(self):
        with TestClient(app) as client:
            upload = client.post(
                "/documents",
                files={"file": ("sample.txt", b"hello from HTTP", "text/plain")},
            )
            self.assertEqual(upload.status_code, 202)
            job_id = upload.json()["job_id"]

            lookup = client.get(f"/documents/{job_id}")
            self.assertEqual(lookup.status_code, 200)
            self.assertEqual(lookup.json()["status"], "completed")
            self.assertEqual(lookup.json()["result"]["words"], 3)

            listing = client.get("/documents?limit=1")
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(listing.json()[0]["job_id"], job_id)

            self.assertEqual(client.get("/documents/missing").status_code, 404)
            self.assertEqual(
                client.post("/documents", files={"file": ("bad.png", b"bad")}).status_code,
                415,
            )


if __name__ == "__main__":
    unittest.main()
