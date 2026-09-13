from rq import Connection, Worker

from config import get_settings
from services.queue import PARSE_QUEUE_NAME, get_redis


def main() -> None:
    settings = get_settings()
    redis_conn = get_redis(settings)
    with Connection(redis_conn):
        worker = Worker([PARSE_QUEUE_NAME])
        worker.work()


if __name__ == "__main__":
    main()
