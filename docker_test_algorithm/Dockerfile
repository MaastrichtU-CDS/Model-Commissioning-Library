FROM python:3-slim

ADD requirements.txt /requirements.txt
ADD run.py /run.py

RUN pip install -r /requirements.txt

EXPOSE 5000
CMD ["python", "run.py"]