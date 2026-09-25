FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY provision_dashboard.py dashboard_definitions.json ./
CMD ["python", "provision_dashboard.py"]
