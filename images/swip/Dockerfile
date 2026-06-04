FROM python:3.11-slim
WORKDIR /app
COPY swip /app/swip
RUN pip install --no-cache-dir prometheus_client pyinstrument yappi pyyaml
EXPOSE 9100 9101
CMD ["python","/app/swip/service.py"]
