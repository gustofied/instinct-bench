FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        asciinema=2.2.0-1 \
        tmux=3.3a-3 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash agent \
    && mkdir -p /opt/evidence /workspace \
    && chown agent:agent /workspace \
    && chmod 755 /opt/evidence

COPY evidence_cli.py entrypoint.sh /opt/evidence/

RUN install -m 0755 /opt/evidence/evidence_cli.py /usr/local/bin/evidence \
    && chmod 0755 /opt/evidence/entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/opt/evidence/entrypoint.sh"]
