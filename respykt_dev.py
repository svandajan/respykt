#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pickle
from typing import Optional

from respykt.binding.template_engine import TemplateEngine
from respykt.respykt import Respykt


class RespyktPickle:
    filename: str = None

    def __init__(self, filename: str = "respekt_vole.pickle"):
        self.filename = filename

    def pickle(self, respykt: Respykt):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        with open(self.filename, mode="wb") as fw:
            respykt.templater = None
            print("(PICKLE) - storing <Respykt> object to '" + self.filename + "'")
            pickle.dump(respykt, fw)

    def unpickle(self) -> Optional[Respykt]:
        with open(self.filename, mode="rb") as fr:
            result: Respykt = pickle.load(fr)
            if type(result) is Respykt:
                result.templater = TemplateEngine(templates_dir=result.folder["templates"],
                                                  module_dir=result.folder["mako_modules"])
                return result
            else:
                return None


kindlegen_command = "kindlegen.exe -dont_append_source -verbose -gen_ff_mobi7 {opf_file}"

pickled_filename = os.path.join("data", "respekt_2019_13.pickle")
pick = RespyktPickle(filename=pickled_filename)
download = True

if download:
    current: Respykt = Respykt(os.path.join("data", "config.ini"))
    current.run()
    pick.pickle(current)
else:
    if not os.path.isfile(pickled_filename):
        print("! Error: Pickle file not found: '{filename}'".format(filename=pickled_filename))
        exit(1)

    current: Respykt = pick.unpickle()
    for article in current.articles:
        print(article["id"], len(article["perex"]), article["perex"])
    current.write_files()
    current.copy_static_res()
