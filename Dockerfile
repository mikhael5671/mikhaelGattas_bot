FROM python:3.11
WORKDIR /app
COPY bot.py/app/bot.py
COPY requirement.txt/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
CMD python/app/bot.py
