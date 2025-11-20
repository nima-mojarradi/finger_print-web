# accounts/tasks.py

from celery import shared_task
from elasticsearch import Elasticsearch, ConnectionError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# ما کلاینت را در سطح جهانی تعریف می‌کنیم، اما اگر None بود،
# در داخل تسک دوباره آن را می‌سازیم.
es_client = None

def get_es_client():
    """
    یک کلاینت ES را برمی‌گرداند یا می‌سازد (Lazy Singleton).
    """
    global es_client
    
    if es_client:
        # اگر کلاینت وجود داشت و سالم بود، برگردان
        try:
            if es_client.ping():
                return es_client
        except ConnectionError:
            logger.warning("Elasticsearch connection lost, attempting to reconnect...")
            es_client = None # اتصال قطع شده، مجبور به ساخت مجدد هستیم

    # اگر کلاینت None بود یا اتصال قطع شده بود، یکی جدید بساز
    try:
        logger.info("Attempting to initialize new Elasticsearch client...")
        client = Elasticsearch(
            settings.ELASTICSEARCH_HOST,
            retry_on_timeout=True,
            max_retries=3
        )
        
        # بررسی اتصال و ساخت ایندکس
        if not client.indices.exists(index=settings.ELASTICSEARCH_INDEX):
            client.indices.create(index=settings.ELASTICSEARCH_INDEX)
            logger.info(f"Created Elasticsearch index: {settings.ELASTICSEARCH_INDEX}")
            
        es_client = client # کلاینت جدید را در متغیر جهانی ذخیره کن
        return es_client

    except ConnectionError as e:
        logger.error(f"Could not connect to Elasticsearch: {e}")
        return None # در صورت شکست اتصال، None برگردان


@shared_task(
    bind=True, # این اجازه می‌دهد تا به self.retry دسترسی داشته باشیم
    max_retries=3, 
    default_retry_delay=60,
    autoretry_for=(ConnectionError,) # به صورت خودکار برای خطاهای اتصال تلاش مجدد کن
)
def log_to_elastic_task(self, log_payload):
    """
    این تسک در بکگراند (توسط Celery Worker) اجرا شده
    و لاگ را به الاستیک ارسال می‌کند.
    """
    try:
        es = get_es_client() # کلاینت را دریافت کن

        if es:
            es.index(
                index=settings.ELASTICSEARCH_INDEX,
                document=log_payload
            )
            logger.debug("Log successfully sent to Elasticsearch.")
        else:
            # اگر get_es_client نتوانست وصل شود، تسک را به تعویق بینداز
            logger.warning("Elasticsearch client is not available. Retrying task...")
            raise ConnectionError("Failed to get ES client, retrying.")

    except Exception as e:
        # برای خطاهای غیرمنتظره (مثلاً خطای فرمت داده)
        logger.error(f"Failed to send log to Elasticsearch: {e}", exc_info=True)
        # برای این خطاها retry نکن تا از لوپ بی‌نهایت جلوگیری شود
        pass