FROM python:3.8

RUN mkdir /app

ADD requirements.txt /app/requirements.txt
ADD ModelEngine.py /app/ModelEngine.py
ADD QueryEngine.py /app/QueryEngine.py
ADD ValidationEngine.py /app/ValidationEngine.py
ADD config.json /app/config.json
ADD validate.py /app/run.py

COPY templates/ /app/templates
COPY queries/ /app/queries

WORKDIR /app
RUN pip install -r requirements.txt

RUN echo "#!/bin/bash">>run.sh
RUN echo "while true; do">>run.sh
RUN echo "python run.py">>run.sh
RUN echo "sleep 10">>run.sh
RUN echo "done">>run.sh

EXPOSE 5000
CMD ["bash", "run.sh"]
