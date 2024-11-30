"""
Copyright 2024 Lorenzo Grandi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from colorama import Fore, Style, init
import logging

# Initialize colorama to automatically reset colors after each log message.
init(autoreset=True)

class ColorFormatter(logging.Formatter):
    """
    Custom logging formatter that adds color to log messages based on their severity.
    
    This formatter uses colorama to format log messages with different colors for
    each logging level: DEBUG, INFO, WARNING, ERROR, and CRITICAL.
    """

    def format(self, record):
        """
        Format the log record with color based on the log level.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to be formatted.

        Returns
        -------
        str
            The formatted log message with the appropriate color.
        """
        
        # Dictionary mapping log levels to colors
        log_colors = {
            logging.DEBUG: Fore.CYAN,      # DEBUG messages in Cyan
            logging.INFO: Fore.GREEN,      # INFO messages in Green
            logging.WARNING: Fore.YELLOW,  # WARNING messages in Yellow
            logging.ERROR: Fore.RED,       # ERROR messages in Red
            logging.CRITICAL: Fore.MAGENTA, # CRITICAL messages in Magenta
        }

        # Get the color for the current log level, default to white if unknown
        level_color = log_colors.get(record.levelno, Fore.WHITE)

        # Format the log message with the selected color and reset the color after
        record.msg = f"{level_color}{record.msg}{Style.RESET_ALL}"

        # Use the default formatter to format the rest of the log record
        return super().format(record)
