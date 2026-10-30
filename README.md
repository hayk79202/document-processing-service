# Document Processing Service

A small FastAPI service for uploading a text document, starting a background job, and polling its status. The processor returns a SHA-256 digest, byte count, and word count. Job records are stored in SQLite.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API reference. Upload a UTF-8 `.txt` file with `POST /documents`, then poll `GET /documents/{job_id}`.

```bash
curl -F "file=@sample.txt" http://127.0.0.1:8000/documents
```

Run `python -m unittest discover -s tests -v` for the core service checks. GitHub Actions runs them on each push.

## API

| Method | Path | Response |
| --- | --- | --- |
| `GET` | `/health` | Service status |
| `POST` | `/documents` | `202` and a job ID |
| `GET` | `/documents/{job_id}` | Status and result when complete |

The upload limit is 2 MiB. The service accepts UTF-8 `.txt` files only. Job status survives a restart in `data/jobs.sqlite3`; uploaded content is not stored. A job interrupted by a server restart can remain `queued`, because workers run in the web process. Run one server process for this version.

## Design direction

```text
Upload -> validation -> queued job -> text processor -> status/result
```

The included Dockerfile runs the same single-process service. Build it with `docker build -t document-service .` and mount `/app/data` if job history should persist across container restarts.

For a distributed version, move job state to PostgreSQL, run workers with Celery and Redis, and add object storage for uploaded files. Those components are planned and are **not implemented here**.

## License

MIT
