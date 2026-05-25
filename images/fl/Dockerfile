FROM python:3.11-slim
WORKDIR /app
COPY fl /app/fl
RUN pip install --no-cache-dir requests prometheus_client
EXPOSE 9000 9001
CMD ["python","/app/fl/coordinator.py"]
