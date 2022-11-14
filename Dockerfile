# docker build -t enzojimenez/vmware-hw-monitor-app .
FROM python:3.7.15-bullseye

COPY ./app /opt/app

WORKDIR /opt/app

RUN pip install -r requirements.txt

EXPOSE 9877

CMD ["python3", "/opt/app/main.py"]