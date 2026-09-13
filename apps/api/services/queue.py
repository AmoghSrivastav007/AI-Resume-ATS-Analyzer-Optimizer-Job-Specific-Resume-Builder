from rq import Queue
from rq.job import Job
from redis import Redis

from config import Settings
from workers.parse_jobs import parse_resume_job

PARSE_QUEUE_NAME = "resume_parse"


def get_redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url)


def get_parse_queue(settings: Settings) -> Queue:
    return Queue(PARSE_QUEUE_NAME, connection=get_redis(settings))


def enqueue_parse_job(
    settings: Settings,
    *,
    resume_id: str,
    version_id: str,
    user_id: str,
    access_token: str | None = None,
) -> Job:
    del access_token
    queue = get_parse_queue(settings)
    return queue.enqueue(
        parse_resume_job,
        user_id,
        resume_id,
        version_id,
        job_id=f"parse-{version_id}",
        meta={"user_id": user_id, "resume_id": resume_id, "version_id": version_id},
        result_ttl=86400,
        failure_ttl=86400,
    )
