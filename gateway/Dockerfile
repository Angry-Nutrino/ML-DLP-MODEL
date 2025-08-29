FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY smtp_proxy.py ./
EXPOSE 2525
CMD ["python", "smtp_proxy.py"]
