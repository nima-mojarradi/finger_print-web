from celery import shared_task
from elasticsearch import Elasticsearch, ConnectionError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

es_client = None


def get_es_client():
    global es_client

    if es_client:
        try:
            if es_client.ping():
                return es_client
        except:
            es_client = None

    try:
        client = Elasticsearch(
            settings.ELASTICSEARCH_HOST,
            retry_on_timeout=True,
            max_retries=3
        )

        if not client.indices.exists(index=settings.ELASTICSEARCH_INDEX):
            client.indices.create(index=settings.ELASTICSEARCH_INDEX)

        es_client = client
        return es_client

    except Exception as e:
        logger.error(f"ES connect error: {e}")
        return None


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError,)
)
def log_to_elastic_task(self, payload):
    try:
        es = get_es_client()

        if es:
            es.index(
                index=settings.ELASTICSEARCH_INDEX,
                body=payload
            )
        else:
            raise ConnectionError("ES Unavailable")

    except Exception as e:
        logger.error(f"Failed to log to ES: {e}")
