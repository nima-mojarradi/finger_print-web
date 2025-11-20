# accounts/middleware.py

import time
import json
import datetime
import io  # نیاز به این پکیج برای استفاده در صورت نیاز
from .tasks import log_to_elastic_task

class ElasticsearchLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # 1. ذخیره بدنه خام قبل از خواندن توسط میان‌افزار و View
        # request.body را فراخوانی می‌کنیم تا داده‌ها را بخوانیم.
        # پس از این خط، request.body برای View خالی است!
        request_body_data = request.body 
        
        # 2. پردازش Request (با استفاده از داده ذخیره شده)
        request_data = self.build_request_data(request_body_data, request) 
        
        # 3. بازسازی Stream درخواست برای View
        # ⚠️ از آنجایی که 'body' یک property است و setter ندارد، از ویژگی داخلی _body استفاده می‌کنیم.
        if hasattr(request, '_body'):
            request._body = request_body_data
            # تنظیم مجدد وضعیت خوانده شدن بدنه (برای اطمینان)
            request._read_status = True 
            
        # --- 4. دریافت Response از ویو ---
        response = self.get_response(request)
        
        # --- 5. پردازش Response و ساخت لاگ نهایی ---
        duration = int((time.time() - start_time) * 1000)
        response_data = self.build_response_data(response)

        log_payload = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'request': request_data,
            'response': response_data,
            'duration_ms': duration,
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip_address': request.META.get('REMOTE_ADDR'),
        }

        # --- 6. ارسال به Celery ---
        log_to_elastic_task.delay(log_payload)

        return response

    # -----------------------------------------------------
    # متد اصلاح‌شده برای دریافت بدنه خام به عنوان پارامتر
    def build_request_data(self, request_body_data, request): 
        data = {
            'path': request.path,
            'method': request.method,
            'headers': dict(request.headers),
        }
        if 'Authorization' in data['headers']:
            data['headers']['Authorization'] = '[REDACTED]'

        try:
            # استفاده از request_body_data که در __call__ ذخیره شده است
            if request_body_data and 'application/json' in request.content_type:
                body_json = json.loads(request_body_data.decode('utf-8'))
                
                # پاکسازی فیلدهای حساس
                sensitive_keys = ['password', 'old_password', 'new_password', 'template_data']
                for key in sensitive_keys:
                    if key in body_json:
                        body_json[key] = '[REDACTED]'
                
                data['body'] = body_json
            else:
                data['body'] = 'Non-JSON body or no body'
        except Exception:
            data['body'] = 'Could not parse request body'
            
        return data

    def build_response_data(self, response):
        data = {
            'status_code': response.status_code,
        }

        if (not getattr(response, 'streaming', False) 
            and 'application/json' in response.get('Content-Type', '')
            and response.content):
            
            try:
                content = response.content.decode('utf-8')
                if len(content) < 4096:
                    response_json = json.loads(content)
                    if 'access_token' in response_json:
                        response_json['access_token'] = '[REDACTED]'
                    if 'password' in response_json:
                        response_json['password'] = '[REDACTED]'
                    data['body'] = response_json
                else:
                    data['body'] = 'Response body too large to log'
            except Exception:
                data['body'] = 'Could not parse response body'
        
        return data