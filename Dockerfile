FROM debian:bookworm

LABEL version="0.0.1"
LABEL description="Populate elasticsearch indices from enexgroup.gr data"
LABEL org.opencontainers.image.authors="akosiaris@uname.gr"

RUN useradd enexgr2elasticsearch -M -d /nonexistent && \
	apt-get update && \
	apt-get install -y python3-pip

COPY . /opt/enexgr2elasticsearch
RUN cd /opt/enexgr2elasticsearch && \
	python3 -m pip install . && \
	rm -rf /opt/enexgr2elasticsearch
USER enexgr2elasticsearch
ENTRYPOINT ["enexgr2elasticsearch"]
