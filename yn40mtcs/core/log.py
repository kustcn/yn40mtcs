#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import logging.handlers
from yn40mtcs.core.constants import LOGGER_NAME

def setup_logging(logfile=f"{LOGGER_NAME}.log", log_level=logging.INFO):
    """ Setup logging configuration """

    cfmt = logging.Formatter(('%(asctime)s - %(name)s - %(filename)s - %(levelname)s - %(message)s'))

    # File formatter, mention time
    ffmt = logging.Formatter(('%(asctime)s - %(filename)s - %(levelname)s - %(message)s'))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level) #将日志处理器的日志级别设置为上述级别之一
    ch.setFormatter(cfmt) #将指定的格式化器应用于日志处理程序，以便对日志消息进行格式化输出

    logs_dir = os.getenv("YN40MTCS_LOGS_DIR", "logs")

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    # File handler
    fh = logging.handlers.RotatingFileHandler(os.path.join(logs_dir, logfile),
        maxBytes=100*1024*1024, backupCount=10)
    fh.setLevel(log_level)
    fh.setFormatter(ffmt)

    # Create the logger,
    # adding the console and file handler
    yn40m_logger = logging.getLogger(LOGGER_NAME)
    yn40m_logger.handlers = []
    yn40m_logger.setLevel(log_level)
    yn40m_logger.addHandler(ch)
    yn40m_logger.addHandler(fh)

    return yn40m_logger
