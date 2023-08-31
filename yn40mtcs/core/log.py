#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import logging.handlers

def setup_logging(logfile="yn40mcts.log", log_level=logging.INFO):
    """ Setup logging configuration """

    cfmt = logging.Formatter(('%(asctime)s- %(name)s - %(filename)s - %(levelname)s - %(message)s'))

    # File formatter, mention time
    ffmt = logging.Formatter(('%(asctime)s - %(filename)s - %(levelname)s - %(message)s'))


    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(cfmt)

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
    yn40m_logger = logging.getLogger('yn40m')
    yn40m_logger.handlers = []
    yn40m_logger.setLevel(log_level)
    yn40m_logger.addHandler(ch)
    yn40m_logger.addHandler(fh)

    # Set up the concurrent.futures logger
    cf_logger = logging.getLogger('concurrent.futures')
    cf_logger.setLevel(log_level)
    cf_logger.addHandler(ch)
    cf_logger.addHandler(fh)

    return yn40m_logger
