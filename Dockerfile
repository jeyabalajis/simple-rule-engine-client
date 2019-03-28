FROM python:3.7-alpine
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD [ "gunicorn", "api_rules_engine:application", "-b", "0.0.0.0:5000", "-w", "4" ]