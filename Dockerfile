FROM hubdocker.aminer.cn/013861b58d084a79866ded8df8801da1/qingjing:0.0.1

COPY devlop_home /app/devlop_home/
COPY devlop_data/复赛数据.tar.gz /app/devlop_data/复赛数据.tar.gz
COPY devlop_data/input_param.json /app/devlop_data/input_param.json
COPY devlop_data/questions /app/devlop_data/questions
COPY py_devlop.sh /app/py_devlop.sh
# COPY devlop_result/output.json /app/devlop_result/answer.json
RUN pip install --no-cache-dir -r /app/devlop_home/requirements.txt && \
    rm -rf /root/.cache

ARG ZHIPUAI_API_KEY
ENV ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}

WORKDIR /app/
CMD ["/app/py_devlop.sh", "/app/devlop_data/input_param.json", "/app/devlop_result/answer.json" ]