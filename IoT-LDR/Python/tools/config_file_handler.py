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
import asyncio
from watchdog.events import FileSystemEventHandler

# Set up logging
logger = logging.getLogger("ConfigFileHandler")
logger.setLevel(logging.DEBUG)

class ConfigFileHandler(FileSystemEventHandler):
    """
    Custom file system event handler that listens for modifications to a configuration file (config.json)
    and triggers a callback function.
    """

    def __init__(self, loop, on_modified_callback):
        """
        Initializes the event handler.
        
        Parameters:
        loop (asyncio.AbstractEventLoop): The asyncio event loop where the callback will be executed.
        on_modified_callback (coroutine): The callback function to be called when the file is modified.
        """
        self.loop = loop
        self.on_modified_callback = on_modified_callback

    def on_modified(self, event):
        """
        This method is called when a file modification is detected.
        
        If the modified file is config.json, it logs the event and triggers the callback function.
        
        Parameters:
        event (watchdog.events.FileSystemEvent): The event object containing details about the file change.
        """
        if event.src_path.endswith('config.json'):
            logger.info("New JSON configurations detected.")
            # Run the callback asynchronously on the event loop
            asyncio.run_coroutine_threadsafe(self.on_modified_callback(), self.loop)
