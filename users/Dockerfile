FROM python:3.13-slim

WORKDIR /app/

COPY requirements.txt .

RUN pip install --no-cache-dir --verbose -r requirements.txt

COPY . .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. users.proto 

EXPOSE 50051

CMD ["python", "main.py"]

