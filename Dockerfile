FROM python:3.10
RUN git clone https://github.com/Happylkx/gpu-sentry \
    && pip install -r gpu-sentry/requirements.txt \
    && wget  # config \
CMD ["python", "./gpu-sentry/gpu-sentry/server.py"]