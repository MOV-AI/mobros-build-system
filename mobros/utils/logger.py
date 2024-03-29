"""Module that contains a wrapper logger to ease interacting with the python logging module"""
import logging

# pylint: disable=W0611
import sys
from os import environ

from termcolor import colored

logging.basicConfig(level=environ.get("PYLOGLEVEL", "INFO"), format="%(message)s")


def error(msg, *args, **kwargs):
    """Wrapping the error method from logging."""
    red_colored_msg = colored("[Error] " + str(msg), "red")
    logging.error(red_colored_msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Wrapping the warning method from logging."""
    yellow_colored_msg = colored("[Warning] " + str(msg), "yellow", attrs=["bold"])
    logging.warning(yellow_colored_msg, *args, **kwargs)


def userWarning(msg, *args, **kwargs):
    """Wrapping the notice method from logging."""
    notice_colored_msg = colored(msg, "cyan", attrs=["bold"])
    logging.warning(notice_colored_msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Wrapping the info method from logging."""
    logging.info(msg, *args, **kwargs)


def userInfo(msg, *args, **kwargs):
    """Wrapping the info method from logging for important stuff."""
    cyan_colored_msg = colored(msg, "cyan")
    logging.info(cyan_colored_msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    """Wrapping the debug method from logging."""
    purple_colored_msg = colored("[Debug] " + msg, "magenta")
    logging.debug(purple_colored_msg, *args, **kwargs)


def log(level, msg, *args, **kwargs):
    """Wrapping the log method from logging."""
    logging.log(level, msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """Wrapping the exception method from logging."""
    logging.exception(msg, *args, **kwargs)
