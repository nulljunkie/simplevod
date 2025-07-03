Run gRPC server and Celery worker

```sh
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. users.proto
celery -A tasks worker --loglevel=info
python main.py
```
