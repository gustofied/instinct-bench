FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

RUN useradd --create-home --shell /bin/bash agent \
    && mkdir -p /opt/evidence /usr/local/lib/instinct-bench /var/lib/evidence /workspace \
    && chown agent:agent /workspace \
    && chmod 700 /opt/evidence /var/lib/evidence

COPY evidence_server.py evidence_cli.py isolation_probe.py entrypoint.sh /opt/evidence/

RUN install -m 0755 /opt/evidence/evidence_cli.py /usr/local/bin/evidence \
    && install -m 0755 /opt/evidence/isolation_probe.py /usr/local/lib/instinct-bench/isolation_probe.py \
    && chmod 0700 /opt/evidence/evidence_server.py \
    && chmod 0755 /opt/evidence/entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["/opt/evidence/entrypoint.sh"]
