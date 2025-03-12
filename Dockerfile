FROM hubdocker.aminer.cn/013861b58d084a79866ded8df8801da1/qingjing:0.0.1

COPY devlop_home /app/devlop_home/

RUN pip install --no-cache-dir -r /app/devlop_home/requirements.txt && \
    rm -rf /root/.cache

ARG ZHIPUAI_API_KEY
ENV ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}

WORKDIR /app/
