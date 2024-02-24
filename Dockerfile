FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN python3 setup.py install

ENTRYPOINT ["python", "-m", "deezer_arl"]