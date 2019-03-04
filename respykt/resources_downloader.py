#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from os.path import join as path_join
from time import sleep
from typing import Dict, Optional

from requests import Session
from requests import get as pure_get


class ResourcesDownloader:
    res_list: Dict[str, str] = None
    data_directory: str = None
    session: Session = None
    wait_time: float = None

    def __init__(self, data_dir: str = None, wait_time: float = None, session: Session = None) -> None:
        if data_dir is None:
            data_dir = path_join("issue", "resources")
        self.data_directory = data_dir
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

        self.res_list = {}
        self.session = session
        # we don't want to overload the server...
        self.wait_time = wait_time

    def add_url(self, url: str, new_name: str = None) -> str:
        if "." in url:
            extension = url[url.rfind(".") + 1:]
            if len(extension) > 6:
                # this doesn't seem to be extension, forget it
                extension = None
        else:
            extension = None
        if new_name is None:
            # if resource is image, name it accordingly
            if extension in ("jpg", "jpeg", "gif", "bmp", "webp"):
                new_name = "image_"
            else:
                new_name = "resource_"
            # add number of resource, starting with 0
            new_name += "{c:04d}".format(c=len(self.res_list) + 1)
            if extension is not None:
                new_name += "." + extension
        self.res_list[new_name] = url
        return path_join(self.data_directory, new_name)

    def download_all(self) -> None:
        for filename, url in self.res_list.items():
            if url[:3] not in ("htt", "ftp"):
                url = "http://" + url
            response = self.download(url)
            data = response.content
            with open(path_join(self.data_directory, filename), "wb") as fw:
                fw.write(data)
            if self.wait_time is not None:
                sleep(self.wait_time)

    def download(self, url: str) -> Optional[bytes]:
        if self.session is not None:
            get = self.session.get
        else:
            get = pure_get
        response = get(url=url)
        if response is not None:
            return response.content
        else:
            return None
