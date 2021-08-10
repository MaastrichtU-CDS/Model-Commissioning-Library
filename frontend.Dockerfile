FROM python:3.8

RUN mkdir /app

ADD requirements.txt /app/requirements.txt
ADD ModelEngine.py /app/ModelEngine.py
ADD QueryEngine.py /app/QueryEngine.py
ADD ValidationEngine.py /app/ValidationEngine.py
ADD config.json /app/config.json
ADD run.py /app/run.py

COPY templates/ /app/templates
COPY queries/ /app/queries

WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "run.py"]
