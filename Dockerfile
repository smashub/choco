FROM python:3.9

WORKDIR /app

ADD requirements.txt .

ADD partitions /app/partitions

RUN pip install -r requirements.txt

ADD choco/create.py /app/choco/create.py

ADD choco/utils.py /app/choco/utils.py

ADD choco/jams_utils.py /app/choco/jams_utils.py

ADD choco/autolink.py /app/choco/autolink.py

ADD choco/parsers /app/choco/parsers

ADD choco/namespaces /app/choco/namespaces

ENV JAMS_VERSION converted

ENV INCLUDE ""

ENV EXCLUDE ""

ENV WORKERS 1

ENV LOG_FILE=/app/data/

CMD python choco/create.py /app/data/ --jams_version ${JAMS_VERSION} --include ${INCLUDE} --exclude ${EXCLUDE} --n_workers ${WORKERS} --log_dir ${LOG_FILE}
