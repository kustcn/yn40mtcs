import optparse
import os, sys
import logging
import pkg_resources

from yn40mtcs.core.log import setup_logging
from yn40mtcs.core.config import ConfigClass
from yn40mtcs.core.constants import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

def init_parser_cmd():
    parser = optparse.OptionParser(usage="Usage: python %prog [options]")
    parser.disable_interspersed_args()
    parser.add_option("-c", "--config", type="string", help="config file path")
    parser.add_option("-d", "--device", type="string", default="telescope", help="telescope or ...")
    parser.add_option("-m", "--command", type="string", default="Tell", help="Tell,AZEL......")
    parser.add_option("-o", "--output", type="string", default="output", help="output directory")
    parser.add_option("-q", "--quiet", action="store_true", default=False, help="be quiet", )
    parser.add_option("-l", "--logfile", type="string", default=f"{LOGGER_NAME}.log", help="log file", )
    parser.add_option("-v", "--verbose", action="store_true", help="show more useful log", )
    return parser

def options_check(options):
    if options.device not in ['telescope']:
        logger.error('device (%s) is not supported' % (options.device, ))
        return False
    return True

def parse_options():
    parser = init_parser_cmd()
    (options, _) = parser.parse_args()
    if not options:
        parser.print_help()
        sys.exit(2)     

    options.logLevel = (options.quiet and logging.ERROR or options.verbose and logging.DEBUG or logging.INFO)
    setup_logging(options.logfile, options.logLevel)

    if not options_check(options):
        sys.exit(2)
    return options
    
def entry_point():
    options = parse_options()
    logger.info("%s is ready to start %s... ♨️ " %(LOGGER_NAME, options.device))

    if options.config is None:
        config_fullpath = pkg_resources.resource_filename('yn40mtcs', 'data/default.cfg')
        config = ConfigClass(config_fullpath)
    else:
        config = ConfigClass(options.config)

    if options.device == 'telescope':
        from yn40mtcs.device.telescope import Telescope
        telescope_device = Telescope(config)
        telescope_device.run(options.command)
    
if __name__ == "__main__":
    entry_point()