"""RQ worker for resume parse jobs.

Run from apps/api:

    .\\.venv\\Scripts\\Activate.ps1
    python -m workers.parse_worker
"""

from redis import Redis
from rq import Worker

from config import get_settings
from services.queue import PARSE_QUEUE_NAME


def main() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    worker = Worker([PARSE_QUEUE_NAME], connection=redis)
    worker.work()


if __name__ == "__main__":
    main()
