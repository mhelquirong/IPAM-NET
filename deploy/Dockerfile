# Validation / demo image for the CODE-branded NetBox platform.
#
# Builds NetBox from the source checkout in this repository (unmodified) and
# installs the netbox_code_branding plugin on top of it. Nothing in netbox/ is
# patched, which is what makes `git checkout v4.8.0` a viable upgrade path.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# psycopg[c] needs libpq + a compiler; the rest are runtime image/graph deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libssl-dev libffi-dev \
        libjpeg-dev libxml2-dev libxslt1-dev zlib1g-dev \
        curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/netbox

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# NetBox core (unmodified upstream source).
COPY netbox/ ./netbox/
COPY docs/ ./docs/
COPY mkdocs.yml ./

# CODE branding plugin, installed as a normal Python package.
COPY code_branding/ ./code_branding/
RUN pip install -e ./code_branding

COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
