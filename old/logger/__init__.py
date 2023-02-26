# zelda64-import-blender
# Import models from Zelda64 files into Blender
# Copyright (C) 2013 SoulofDeity
# Copyright (C) 2020 Dragorn421
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>

import logging

# https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility
logging_trace_level = 5
logging.addLevelName(logging_trace_level, 'TRACE')

logger_file_handler = None
logger_operator_report_handler = None

logger_formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')

logger_stream_handler = logging.StreamHandler()
logger_stream_handler.setFormatter(logger_formatter)
logger_stream_handler.setLevel(logging.INFO) # default level is INFO

logger = logging.getLogger('z64import')
logger.addHandler(logger_stream_handler)
logger.setLevel(1) # actual level filtering is left to handlers

getLogger('setupLogging').debug('Logging OK')


class OperatorReportLogHandler(logging.Handler):
    def __init__(self, operator):
        super().__init__()
        self.operator = operator

    def flush(self):
        pass

    def emit(self, record):
        try:
            type = 'DEBUG'
            for levelType,  minLevel in (
                    ('ERROR',   logging.WARNING), # comment to allow calling bpy.ops.file.zobj2020 without RuntimeError (makes WARNING the highest report level instead of ERROR)
                    ('WARNING', logging.INFO),
                    ('INFO',    logging.DEBUG)):
                if record.levelno > minLevel:
                    type = levelType
                    break
            msg = self.format(record)
            self.operator.report({type}, msg)
        except Exception:
            self.handleError(record)


def setLoggingLevel(level):
    logger_stream_handler.setLevel(level)

def getLogger(name):
    log = logger.getChild(name)
    def trace(message, *args, **kws):
        if log.isEnabledFor(logging_trace_level):
            log._log(logging_trace_level, message, args, **kws)
    log.trace = trace
    return log

def setLogFile(path):
    if logger_file_handler:
        logger.removeHandler(logger_file_handler)
        logger_file_handler = None
    if path:
        logger_file_handler = logging.FileHandler(path, mode='w')
        logger_file_handler.setFormatter(logger_formatter)
        logger_file_handler.setLevel(1)
        logger.addHandler(logger_file_handler)

def setLogOperator(operator, level=logging.INFO):
    if logger_operator_report_handler:
        logger.removeHandler(root_logger_operator_report_handler)
        logger_operator_report_handler = None
    if operator:
        logger_operator_report_handler = OperatorReportLogHandler(operator)
        logger_operator_report_handler.setFormatter(logger_formatter)
        logger_operator_report_handler.setLevel(level)
        logger.addHandler(logger_operator_report_handler)

def registerLogging():
    pass

def unregisterLogging():
    setLogFile(None)
    setLogOperator(None)
