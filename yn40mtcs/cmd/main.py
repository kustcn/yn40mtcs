import optparse
import os, sys
import logging

from yn40mtcs.core.log import setup_logging
from yn40mtcs.core.constants import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


def init_parser_cmd():
    parser = optparse.OptionParser(usage="Usage: python %prog [options]")
    parser.disable_interspersed_args()
    parser.add_option("-n", "--name", type="string", default="", help="device name")
    parser.add_option("-d", "--device_host", type="string", default="127.0.0.1", help="device's host")
    parser.add_option("-m", "--mode", type="string", default="sync", help="sync or async")
    parser.add_option("-s", "--steward", type="string", default="127.0.0.1:7001", help="steward's host:port")
    parser.add_option("-q", "--quiet", action="store_true", default=False, help="be quiet", )
    parser.add_option("-l", "--logfile", type="string", default="device.log", help="log file", )
    parser.add_option("-v", "--verbose", action="store_true", help="show more useful log", )
    return parser

def options_check():
    return True

def parse_options():
    parser = init_parser_cmd()
    (options, _) = parser.parse_args()
    if not options:
        parser.print_help()
        sys.exit(2)     

    options.logLevel = (options.quiet and logging.ERROR or options.verbose and logging.DEBUG or logging.INFO)
    setup_logging(options.logfile, options.logLevel)

    if not options_check():
        sys.exit(2)
    return options
    
def entry_point():
    parse_options()
    logger.info("%s is ready to start... ♨️ " %(LOGGER_NAME))

if __name__ == "__main__":
    entry_point()