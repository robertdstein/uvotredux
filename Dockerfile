ARG heasoft_version=6.35.1

FROM robertdstein/heasoft:$heasoft_version AS base

WORKDIR /app

COPY . /app

ENV PATH=/home/heasoft/.local/bin:/opt/heasoft/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN pip install --upgrade pip && pip install -e ".[dev]" # buildkit

FROM base AS uvotredux

WORKDIR /mydata
ENV UVOTREDUX_DATA_DIR=/mydata
# Let's you run HEASOFT non-interactively
ENV HEADASPROMPT=/dev/null

ENTRYPOINT ["uvotredux"]
