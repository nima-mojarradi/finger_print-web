FROM python:3.11

WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY . /code/

EXPOSE 8000

# CMD مخصوص app: migrate و runserver
CMD ["/wait-for-it.sh", "db:5432", "--timeout=60", "--strict", "--", "python", "manage.py", "migrate", "&&", "python", "manage.py", "runserver", "0.0.0.0:8000"]