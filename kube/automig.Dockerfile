# This image runs migration jobs

FROM python:3.7.6-slim

# deps
RUN apt-get update
# todo: is libpq-dev necessary with psycopg2-binary?
RUN apt-get install libpq-dev git -qqy
# note: update this to the latest version if it looks old
RUN pip install automig[postgres]==0.0.20

# files
WORKDIR /migrate
# note: schema is the location of your schema -- should match the AUTOMIG_GLOB you pass to the automig tool
COPY schema schema/
# note: automig relies on a git repo, normally dockerfiles don't include a git repo
COPY .git .git/
