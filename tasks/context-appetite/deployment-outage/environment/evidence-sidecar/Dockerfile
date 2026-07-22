FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

RUN useradd --system --create-home --shell /usr/sbin/nologin evidence \
    && mkdir -p /opt/evidence /var/lib/evidence /evidence-artifacts \
    && chown -R evidence:evidence /var/lib/evidence /evidence-artifacts

COPY evidence_server.py snapshot.py task_data.json /opt/evidence/

RUN chmod 0555 /opt/evidence/evidence_server.py /opt/evidence/snapshot.py \
    && chmod 0444 /opt/evidence/task_data.json

USER evidence
WORKDIR /opt/evidence

ENTRYPOINT ["python3", "/opt/evidence/evidence_server.py"]
