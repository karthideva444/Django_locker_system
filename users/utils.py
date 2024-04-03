"""
Logger utils file
"""
import logging
import sys, os
LOG_FILE = 'logs'+ os.sep + 'Locker.log'
def get_logger(logger_name, log_file_path):
    """
    Get logger
    """
    LOG_PATH = log_file_path + LOG_FILE

    root_logger = logging.getLogger(logger_name)
    if root_logger.handlers:
        return root_logger
    root_logger.setLevel(logging.INFO)

    # create a logging format
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(process_name)s - '
        '%(levelname)s - %(message)s', datefmt='%B %d %Y, %H:%M:%S'
    )
    # create a stream handler
    stream_handler_out = logging.StreamHandler(sys.stdout)
    stream_handler_out.setLevel(logging.INFO)
    # stream_handler_out.addFilter(
    #     type('', (logging.Filter,),
    #          {'filter': staticmethod(lambda r: r.levelno <= logging.INFO)})
    # )
    stream_handler_out.setFormatter(formatter)

    stream_handler_err = logging.StreamHandler(sys.stderr)
    stream_handler_err.setLevel(logging.WARNING)
    stream_handler_err.addFilter(
        type('', (logging.Filter,),
             {'filter': staticmethod(lambda r: r.levelno > logging.INFO)})
    )
    # Create a file handler for file output
    file_handler = logging.FileHandler(LOG_PATH)  # Specify your log file path here
    file_handler.setLevel(logging.INFO)
    # file_handler.setLevel(logging.ERROR)  # Set the desired logging level for file output
    file_handler.setFormatter(formatter)
    # stream_handler_err.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(stream_handler_out)
    root_logger.addHandler(stream_handler_err)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    return root_logger

