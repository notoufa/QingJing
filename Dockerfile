FROM hubdocker.aminer.cn/library/python-base:1.0.0

COPY devlop_home /app/devlop_home/

RUN pip install --no-cache-dir -r /app/devlop_home/requirements.txt && \
    rm -rf /root/.cache

ARG ZHIPUAI_API_KEY
ENV ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}

WORKDIR /app/
