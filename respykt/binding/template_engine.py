#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from mako.lookup import TemplateLookup
from mako.template import Template


class TemplateEngine(object):
    templates_directory: str = None
    module_directory: str = None
    lookup: TemplateLookup = None

    def __init__(self, templates_dir: str = os.path.join("..", "resources", "templates"),
                 module_dir: str = os.path.join("..", "resources", "mako_modules")) -> None:
        if module_dir is None:
            module_dir = "templates"
        if not os.path.exists(module_dir):
            os.mkdir(module_dir)
        self.templates_directory = templates_dir
        self.module_directory = module_dir

        self.lookup = TemplateLookup(directories=[templates_dir], module_directory=module_dir, collection_size=100,
                                     output_encoding="utf8", encoding_errors="replace", input_encoding="utf8")

    def serve_template(self, template_name: str, **kwargs) -> str:
        new_template: Template = self.lookup.get_template(template_name)
        return new_template.render_unicode(**kwargs)
