FROM docker.io/python:latest
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY decryptor.py /app/
CMD ["python3", "-u", "/app/decryptor.py"]
