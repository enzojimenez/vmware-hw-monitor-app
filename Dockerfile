# docker build -t enzojimenez/vmware-hw-monitor-app:TAG .
FROM python:3.7.15-bullseye

RUN mkdir /monitor-app

COPY app /monitor-app

WORKDIR /monitor-app

RUN pip install -r requirements.txt

EXPOSE 9877

CMD ["python3", "main.py"]