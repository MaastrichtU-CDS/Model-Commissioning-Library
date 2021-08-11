FROM python:3.8

COPY app/ /app

WORKDIR /app
RUN pip install -r requirements.txt

RUN echo "#!/bin/bash">>run.sh

RUN echo "" >> run.sh
RUN echo "if [ -z \"\$SLEEPTIME\" ]; then" >> run.sh
RUN echo "    SLEEPTIME=10" >> run.sh
RUN echo "    echo \"SLEEPTIME set to \$SLEEPTIME\"" >> run.sh
RUN echo "fi" >> run.sh
RUN echo "" >> run.sh

RUN echo "CONTINUE=true">>run.sh
RUN echo "while \$CONTINUE; do">>run.sh
RUN echo "python validate.py">>run.sh
RUN echo "STATUS=\$?">>run.sh
RUN echo "if [ \$STATUS -ne 0 ]; then" >> run.sh
RUN echo "    CONTINUE=false" >> run.sh
RUN echo "else" >> run.sh
RUN echo "    sleep 10">>run.sh
RUN echo "fi">>run.sh
RUN echo "done">>run.sh

CMD ["bash", "run.sh"]
