FROM public.ecr.aws/lambda/python:3.10

COPY ./app ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN pip3 install -r requirements.txt -t "${LAMBDA_TASK_ROOT}" -U

CMD ["app.lambda_handler"]