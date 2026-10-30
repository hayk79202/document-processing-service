# Document Processing Service

![Python tests](https://github.com/hayk79202/document-processing-service/actions/workflows/ci.yml/badge.svg)

A small FastAPI service for uploading a text document, starting a background job, and polling its status. The processor returns a SHA-256 digest, byte count, and word count. Job records are stored in SQLite.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API reference. Upload a UTF-8 `.txt` file with `POST /documents`, then poll `GET /documents/{job_id}`.

```bash
curl -F "file=@examples/sample.txt" http://127.0.0.1:8000/documents
```

Run `python -m unittest discover -s tests -v` for the core service checks. GitHub Actions runs them and builds the Docker image on each push.

## API

| Method | Path | Response |
| --- | --- | --- |
| `GET` | `/health` | Service status |
| `POST` | `/documents` | `202` and a job ID |
| `GET` | `/documents?limit=20` | Recent job statuses (up to 100) |
| `GET` | `/documents/{job_id}` | Status and result when complete |

The upload limit is 2 MiB. The service accepts UTF-8 `.txt` files only. Job status survives a restart in `data/jobs.sqlite3`; uploaded content is not stored. On restart, unfinished jobs are marked `failed` because their in-process workers cannot resume. Run one server process for this version.

## Design direction

```text
Upload -> validation -> queued job -> text processor -> status/result
```

The Dockerfile runs the same single-process service. To keep job history across container restarts:

```bash
docker build -t document-service .
docker volume create document-jobs
docker run -p 8000:8000 -v document-jobs:/app/data document-service
```

For a distributed version, move job state to PostgreSQL, run workers with Celery and Redis, and add object storage for uploaded files. Those components are planned and are **not implemented here**.

## License

MIT
