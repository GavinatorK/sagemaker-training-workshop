# Part of the implementation of this container is based on the Amazon SageMaker Apache MXNet container.
# https://github.com/aws/sagemaker-mxnet-container

FROM fastdotai/fastai:latest

LABEL maintainer="Raj Kadiyala"


WORKDIR /

# Installing numpy, pandas, scikit-learn, scipy
RUN pip3 install --no-cache --upgrade requests 

# Setting some environment variables.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib" \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN pip3 install --no-cache --upgrade \
    sagemaker-training

# Copies code under /opt/ml/code where sagemaker-containers expects to find the script to run
COPY code/* /opt/ml/code/
# RUN pip uninstall urllib3
# RUN pip uninstall requests
# RUN pip uninstall chardet
# RUN yum remove python-requests
# RUN yum remove python-urllib3
# RUN pip install --upgrade --force-reinstall 'requests==2.6.0' urllib3
# RUN yum install certbot
# Defines train.py as script entry point
ENV SAGEMAKER_PROGRAM train.py