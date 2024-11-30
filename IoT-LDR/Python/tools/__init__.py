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

import logging

from .color_format import ColorFormatter
from .config_file_handler import ConfigFileHandler

__all__ = ['ConfigFileHandler', 'ColorFormatter']

console_handler = logging.StreamHandler()

formatter = ColorFormatter("%(asctime)s - %(name)s : %(message)s", datefmt="%H:%M:%S")
console_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)