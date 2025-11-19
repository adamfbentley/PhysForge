import os
import sys
import logging
from redis import Redis
from rq import Worker, Queue, Connection

# Add parent directory to path to allow importing backend.pinn_training_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_orchestration_service.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("rq_worker")

def run_worker():
    redis_conn = Redis.from_url(settings.REDIS_URL)
    with Connection(redis_conn):
        worker = Worker(map(Queue, ['default']), connection=redis_conn)
        logger.info("Starting RQ worker...")
        worker.work()

if __name__ == '__main__':
    run_worker()
