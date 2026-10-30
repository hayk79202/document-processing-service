# Document Processing Service

A small FastAPI prototype for uploading a text document, starting a background job, and polling its status. The current processor returns a SHA-256 digest, byte count, and word count.

## Run locally

```bash
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API reference. Upload a UTF-8 `.txt` file with `POST /documents`, then poll `GET /documents/{job_id}`.

## API

| Method | Path | Response |
| --- | --- | --- |
| `GET` | `/health` | Service status |
| `POST` | `/documents` | `202` and a job ID |
| `GET` | `/documents/{job_id}` | Status and result when complete |

The upload limit is 2 MiB. The service accepts text files only. It holds jobs in memory and uses FastAPI background tasks, so restarting the server loses job history. Run one server process for this prototype.

## Design direction

```text
Upload -> validation -> queued job -> text processor -> status/result
```

For a durable version, move job state to PostgreSQL via SQLAlchemy, run workers with Celery and Redis, add object storage for uploaded files, and package the services with Docker. Those components are planned and are **not implemented here**.

## License

MIT
