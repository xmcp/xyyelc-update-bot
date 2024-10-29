FROM python:3.13
WORKDIR /app

ADD requirements.txt /app
RUN pip install -r requirements.txt

ADD main.py /app

CMD ["python", "-u", "main.py"]