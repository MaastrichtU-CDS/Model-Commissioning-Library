FROM python:3.8

COPY app/ /app

WORKDIR /app
RUN pip install -r requirements.txt

RUN echo "#!/bin/bash">>run.sh
RUN echo "while true; do">>run.sh
RUN echo "python validate.py">>run.sh
RUN echo "sleep 10">>run.sh
RUN echo "done">>run.sh

CMD ["bash", "run.sh"]
