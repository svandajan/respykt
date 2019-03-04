#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
import re
from os.path import join as path_join
from shutil import copy2 as copy_file
from typing import Dict, List, Union, Optional, Any

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session

from request_soap import RequestSoap
from resources_downloader import ResourcesDownloader
from template_engine import TemplateEngine
from utils import get_text, replace_figure_with_img, log_error, log_info


class Respykt:
    config_file: str = None
    session: Session = None
    dl_wait_time: float = None
    url: Dict[str, str] = None
    folder: Dict[str, str] = None
    issue: Dict[str, Union[str, List]] = None
    user: Dict[str, str] = None

    requester: RequestSoap = None
    downloader: ResourcesDownloader = None
    templater: TemplateEngine = None

    articles: List[Dict[str, Optional[str]]] = None
    categories: List[Dict[str, Union[str, List]]] = None

    _issue_url_pattern = re.compile(r"respekt\.cz/tydenik/([0-9]{4})/([0-9]+)")

    def __init__(self, config_file: str = None):
        self.session = Session()
        self.folder = {}
        self.issue = {}
        self.url = {"home": "https://www.respekt.cz/"}

        # Read config file for user-defined settings, load default values to the rest of them
        self.config_file = config_file
        if config_file:
            self.load_conf_from_file(config_file)
        self.load_conf_default()

        self.requester = RequestSoap(session=self.session)
        self.downloader = ResourcesDownloader(session=self.session, wait_time=self.dl_wait_time,
                                              data_dir=self.folder["issue_res"])
        self.templater = TemplateEngine(templates_dir=self.folder["templates"],
                                        module_dir=self.folder["mako_modules"])

    def load_conf_from_file(self, config_file: str = None) -> None:
        if config_file is None:
            config_file = self.config_file
        if config_file is None:
            log_error("Error - Respkyt::load_conf_from_file: No config file provided")
            return
        if not os.path.exists(config_file):
            log_error(
                "Error - Respkyt::load_conf_from_file: File '{config}' does not exist".format(config=config_file))
            return

        config = configparser.ConfigParser()
        config.read(config_file)
        log_info("loading settings from file '{config}'".format(config=config_file))

        if "LOGIN" in config:
            if "username" in config["LOGIN"] and "password" in config["LOGIN"]:
                if config["LOGIN"]["username"] != "" and config["LOGIN"]["password"] != "":
                    self.user = {"username": config["LOGIN"]["username"], "password": config["LOGIN"]["password"]}
        if "FOLDERS" in config:
            if "issue" in config["FOLDERS"]:
                self.folder["issue"] = config["FOLDERS"]["issue"]
            if "templates" in config["FOLDERS"]:
                self.folder["templates"] = config["FOLDERS"]["templates"]
            if "mako_modules" in config["FOLDERS"]:
                self.folder["mako_modules"] = config["FOLDERS"]["mako_modules"]
            if "static" in config["FOLDERS"]:
                self.folder["static"] = config["FOLDERS"]["static"]
        if "DONWLOAD" in config:
            if "wait_time" in config["DOWNLOAD"]:
                self.dl_wait_time = config["DOWNLOAD"]["wait_time"]

    def load_conf_default(self) -> None:
        """
        If config settings are not set, initiates them with defualt values
        """

        if "issue" not in self.folder:
            self.folder["issue"] = "issue"
        self.folder["issue_res"] = path_join(self.folder["issue"], "resources")
        if "templates" not in self.folder:
            self.folder["templates"] = path_join("resources", "templates")
        if "mako_modules" not in self.folder:
            self.folder["mako_modules"] = path_join("resources", "mako_modules")
        if "static" not in self.folder:
            self.folder["static"] = path_join("resources", "static")
        if self.dl_wait_time is None:
            self.dl_wait_time = 0.1

    def login(self):
        if self.user is not None and "username" in self.user and "password" in self.user:
            login_postdata = {"username": self.user["username"], "password": self.user["password"],
                              "do": "authBox-loginForm-submit", "_do": "authBox-loginForm-submit"}
            login_url = self.url["home"]
            self.requester.post(url=login_url, data=login_postdata)

    def set_issue(self, year: Union[str, int], number: Union[str, int]):
        self.issue["year"] = str(year)
        self.issue["number"] = str(number)
        self.url["issue"] = "https://www.respekt.cz/tydenik/{year}/{number}".format(year=year, number=number)

    def get_current_issue(self) -> str:
        log_info("issue not set, searching home page current one")
        home_page = self.requester.get(self.url["home"])

        issue_url = home_page.find(class_="currentissue").a["href"]
        issue_url_search = self._issue_url_pattern.search(issue_url)
        self.issue["year"] = issue_url_search.group(1)
        self.issue["number"] = issue_url_search.group(2)
        self.url["issue"] = issue_url
        return issue_url

    def parse_toc_page(self):
        if "issue" not in self.url:
            self.get_current_issue()
        toc_page = self.requester.get(self.url["issue"])
        log_info("parsing TOC page with URL = '{url}'".format(url=self.url["issue"]))

        articles_raw = toc_page(class_="issuedetail-categorized-item")
        self.articles = []
        categories: Dict[str, Any] = {}
        articles_count = 0
        categories_count = 0

        for art in articles_raw:
            article = {"url": art["href"]}
            if article["url"][:3] != "htt" and article["url"][0] == "/":
                article["url"] = self.url["home"] + article["url"][1:]
            article["title"] = get_text(art.find(class_="issuedetail-categorized-title"))
            article["authors"] = get_text(art.find(class_="issuedetail-categorized-author"))
            article["perex"] = get_text(art.find(class_="issuedetail-categorized-perex"))
            article["is_locked"] = True if art.find(class_="lock") is not None else False

            art_category = get_text(art.find_previous_sibling(class_="issuedetail-categorized-sectionname"))
            article["category"] = art_category
            if ("despekt" in article["category"].lower()) or ("anketa" in article["category"].lower()):
                # those are special cases, will deal with them later
                # (each will require special template and 'anketa' ('survey') entirely different parsing)
                continue
            if article["is_locked"]:
                # hit paywal...
                continue

            articles_count += 1
            article["no"] = articles_count
            if art_category not in categories:
                categories_count += 1
                categories[art_category] = {"name": art_category, "id": categories_count, "articles": []}
            categories[art_category]["articles"].append(article)
            self.articles.append(article)
            log_info("adding article number {count} with title '{title}' of "
                     "category '{cat}'".format(count=articles_count, title=article["title"], cat=article["category"]))

        # sort categories by their ids
        self.categories = sorted([cat_dict for cat_name, cat_dict in categories.items()],
                                 key=lambda kv: kv["id"])
        self.issue["categories"] = self.categories

    def download_resources(self):
        log_info("downloading resources to folder '{issue_res}'".format(issue_res=self.folder["issue_res"]))
        self.downloader.download_all()
        log_info("  done")

    def download_articles(self):
        if self.articles is None:
            self.parse_toc_page()

        for article in self.articles:
            log_info("processing article {no}/{count}: '{title}'".format(no=article["no"], count=len(self.articles),
                                                                         title=article["title"]))
            # download and parse article page
            soap_article: BeautifulSoup = self.requester.get(article["url"])
            article["topics"] = get_text(soap_article.find(class_="post-topics")("a"))
            article["subtitle"] = get_text(soap_article.find("h2", class_="post-subtitle"))
            article["date"] = get_text(soap_article.find(class_="authorship-note"))

            # search for header image
            article_header_image = soap_article.find("header", class_="post-header").find("figure", class_="frame")
            if article_header_image is not None:
                article["header_image_src"] = replace_figure_with_img(self.downloader, soap_article,
                                                                      article_header_image,
                                                                      return_src=True, max_width=800)
            else:
                article["header_image_src"] = None

            soap_article_content: Tag = soap_article.find(id="postcontent")
            for article_figure in soap_article_content("figure"):
                # replace all figures in article content with simple <img> tag
                replace_figure_with_img(self.downloader, soap_article, article_figure, max_width=500)
            article["content"] = soap_article_content.prettify()

    def run(self):
        self.login()
        self.parse_toc_page()
        self.download_articles()
        self.write_files()
        self.download_resources()
        self.copy_static_res()

    def write_article_file(self, article: Dict[str, Optional[str]]):

        with open(article["filepath"], mode="w", encoding="utf8") as fw:
            log_info("creating article file content from template '{tname}' and saving "
                     "to {filepath}'".format(tname=article["template_name"], filepath=article["filepath"]))
            raw_data = self.templater.serve_template(**article)
            fw.write(raw_data)

    def copy_static_res(self):
        source_dir = self.folder["static"]
        dest_dir = self.folder["issue_res"]
        log_info("copying content of directory '{source}' "
                 "to resource dir '{dest}'".format(source=source_dir, dest=dest_dir))
        for filename in os.listdir(source_dir):
            log_info("  '{filename}'".format(filename=filename))
            copy_file(path_join(source_dir, filename), path_join(dest_dir, filename))

    def write_files(self):
        # prepare folder for article files
        article_filename_format = "article_{no:04d}.html"
        folder_articles = path_join(self.folder["issue"], "text")
        if not os.path.exists(folder_articles):
            os.mkdir(folder_articles)

        # list of files to render using templates
        files_to_render: List[Dict] = []

        # add articles to list
        for article in self.articles:
            article["filename"] = article_filename_format.format(no=article["no"])
            article["filepath"] = path_join(folder_articles, article["filename"])
            files_to_render.append({"filename": article["filepath"], "template": "article.html", "data": article})

        # add TOC HTML page
        files_to_render.append({"filename": path_join(self.folder["issue"], "toc.html"),
                                "template": "toc.html", "data": self.issue})

        # render files
        for file_ in files_to_render:
            with open(file_["filename"], mode="w", encoding="utf8") as fw:
                log_info("using template '{tname}' to generate "
                         "file '{filepath}'".format(tname=file_["template"], filepath=file_["filename"]))
                raw_data = self.templater.serve_template(template_name=file_["template"], **file_["data"])
                fw.write(raw_data)

# TODO:
#   - generate TOC html page
#   - generate toc.ncx and opf file
#   - create ebooks
