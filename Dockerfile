FROM inputoutput/cardano-node:1.34.1@sha256:3bffeccf986986cece4d21c1901b564a3180880e136b0e221caa13e2757c751d

WORKDIR /opt/app

COPY ./src /opt/app
COPY ./config /opt/app

CMD ["python3", "-m", "$WORKDIR./src/testtest.py"]