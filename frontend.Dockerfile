FROM python:3.8

COPY app/ /app

WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "run.py"]