# Build with repository root as context; only runtime sources enter the image.
FROM python:3.12.12-slim-bookworm
ARG TORCH_VERSION=2.13.0
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "torch==${TORCH_VERSION}" --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir numpy==2.5.1 pydantic==2.13.4
COPY lassi_x /opt/lassi_x
COPY docker/cpu/probe.py /opt/probe.py
ENV PYTHONPATH=/opt PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
USER 65532:65532
WORKDIR /workspace
CMD ["/usr/local/bin/python", "/opt/probe.py"]
