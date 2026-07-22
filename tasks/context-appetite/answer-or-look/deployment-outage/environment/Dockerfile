FROM python:3.13-slim

RUN useradd --create-home --shell /bin/bash agent \
    && mkdir -p /opt/evidence /var/lib/evidence /workspace \
    && chown agent:agent /workspace \
    && chmod 700 /opt/evidence /var/lib/evidence

COPY evidence_server.py evidence_cli.py entrypoint.sh /opt/evidence/

RUN install -m 0755 /opt/evidence/evidence_cli.py /usr/local/bin/evidence \
    && chmod 0700 /opt/evidence/evidence_server.py \
    && chmod 0755 /opt/evidence/entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/opt/evidence/entrypoint.sh"]
