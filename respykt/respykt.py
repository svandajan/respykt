#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
import re
from hashlib import md5
from shutil import copy2 as copy_file
from typing import Dict, List, Union, Optional, Any

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session

from request_soap import RequestSoap
from resources_downloader import ResourcesDownloader
from template_engine import TemplateEngine
from utils import get_text, replace_figure_with_img, log_error, log_info

StringDict = Dict[str, Optional[str, List]]


class Respykt:
    config_file: str = None
    session: Session = None
    dl_wait_time: float = None
    url: StringDict = None
    folder: StringDict = None
    issue: StringDict = None
    user: StringDict = None

    requester: RequestSoap = None
    downloader: ResourcesDownloader = None
    templater: TemplateEngine = None

    articles: List[StringDict] = None
    categories: List[StringDict] = None

    _issue_url_pattern = re.compile(r"respekt\.cz/tydenik/([0-9]{4})/([0-9]+)")

    def __init__(self, config_file: str = None):
        self.session = Session()
        self.folder = {}
        self.issue = {}
        self.user = {}
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
        self.folder["issue_res"] = os.path.join(self.folder["issue"], "resources")
        if "templates" not in self.folder:
            self.folder["templates"] = os.path.join("resources", "templates")
        if "mako_modules" not in self.folder:
            self.folder["mako_modules"] = os.path.join("resources", "mako_modules")
        if "static" not in self.folder:
            self.folder["static"] = os.path.join("resources", "static")
        if self.dl_wait_time is None:
            self.dl_wait_time = 0.1

    def login(self):
        if "username" in self.user and "password" in self.user:
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

    @staticmethod
    def get_date_from_datestring(datestring: str):
        # 51/2002, 16.–23. 12. 2002
        # 9/2019, 25. 2. – 3. 3. 2019
        # 9/2019, 25. 2. – 3. 3. 2019
        # 1/2003, 23. 12. 2002–2. 1. 2003
        datestring_format = re.compile(
            r"(\d{1,2})/(\d{4}), ?(\d{1,2})\. ?(\d{1,2})?\.? ?(\d{4})?[–-] ?(\d{1,2})\. ?(\d{1,2})\. ?(\d{4})")
        issue_datematch = datestring_format.search(datestring).groups()
        return "{year}{month:02d}{day:02d}".format(year=issue_datematch[-1], month=int(issue_datematch[-2]),
                                                   day=int(issue_datematch[2]))

    def parse_toc_page(self):
        if "issue" not in self.url:
            self.get_current_issue()
        toc_page = self.requester.get(self.url["issue"])
        log_info("parsing TOC page with URL = '{url}'".format(url=self.url["issue"]))

        self.issue["title"] = get_text(toc_page.find(class_="heroissue").h2)
        self.issue["subtitle"] = get_text(toc_page.find(class_="heroissue").find("div", class_="heroissue-theme"))
        cover_image = self.downloader.add_url(toc_page.find(class_="heroissue").a["href"])
        self.issue["cover"] = cover_image

        issue_datestring = get_text(toc_page.find(class_="heroissue").find("time", class_="heroissue-date"))
        self.issue["datestring"] = issue_datestring
        self.issue["date"] = self.get_date_from_datestring(issue_datestring)
        hash_source = md5()
        hash_source.update("Respekt_".encode("utf8"))
        hash_source.update(self.issue["date"].encode("utf8"))
        hash_source.update(self.user["username"].encode("utf8") if "username" in self.user else "(free)".encode("utf8"))
        self.issue["uid"] = hash_source.hexdigest()
        self.issue["username"] = self.user["username"] if "username" in self.user else None

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

            if art_category not in categories:
                categories_count += 1
                articles_count = 0
                categories[art_category] = {"name": art_category, "id": categories_count, "articles": []}
            articles_count += 1
            article["id"] = categories_count * 100 + articles_count
            categories[art_category]["articles"].append(article)
            self.articles.append(article)
            log_info("adding article number {category}/{count} with title '{title}' of "
                     "category '{cat}'".format(category=categories_count, count=articles_count,
                                               title=article["title"], cat=article["category"]))

        # sort categories by their ids
        self.categories = sorted([cat_dict for cat_name, cat_dict in categories.items()],
                                 key=lambda kv: kv["id"])
        self.issue["articles"] = self.articles
        self.issue["categories"] = self.categories

    def download_resources(self):
        log_info("downloading resources to folder '{issue_res}'".format(issue_res=self.folder["issue_res"]))
        self.downloader.download_all()
        log_info("  done")

    def download_articles(self):
        if self.articles is None:
            self.parse_toc_page()

        for art_no, article in enumerate(self.articles):
            log_info("processing article {no}/{count}: '{title}'".format(no=art_no + 1, count=len(self.articles),
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

            article_content: Tag = soap_article.find(id="postcontent")
            # replace all figures in article content with simple <img> tag
            for article_figure in article_content("figure"):
                replace_figure_with_img(self.downloader, soap_article, article_figure, max_width=500)
            # kindlegen breaks on <blockquote> tags, so get rid of them
            for quote in article_content(class_="quote"):
                quote.extract()
            article["content"] = str(article_content)

    def run(self):
        self.login()
        self.parse_toc_page()
        self.download_articles()
        self.write_files()
        self.download_resources()
        self.copy_static_res()

    def copy_static_res(self):
        source_dir = self.folder["static"]
        dest_dir = self.folder["issue_res"]
        log_info("copying content of directory '{source}' "
                 "to resource dir '{dest}'".format(source=source_dir, dest=dest_dir))
        for filename in os.listdir(source_dir):
            log_info("  '{filename}'".format(filename=filename))
            copy_file(os.path.join(source_dir, filename), os.path.join(dest_dir, filename))

    def write_files(self):
        # prepare folder for article files
        article_filename_format = "article_{no:04d}.html"
        folder_articles = os.path.join(self.folder["issue"], "text")
        if not os.path.exists(folder_articles):
            os.mkdir(folder_articles)

        self.issue["date"] = self.get_date_from_datestring(self.issue["datestring"])

        # list of files to render using templates
        files_to_render: List[Dict] = []

        # add articles to list
        for art_no, article in enumerate(self.articles):
            article["filename"] = article_filename_format.format(no=article["id"])
            article["filepath"] = os.path.join(folder_articles, article["filename"])
            files_to_render.append({"filename": article["filepath"], "template": "article.html", "data": article})

        # add title page
        files_to_render.append({"filename": os.path.join(self.folder["issue"], "title.html"),
                                "template": "title.html", "data": self.issue})
        # add TOC HTML page
        files_to_render.append({"filename": os.path.join(self.folder["issue"], "toc.html"),
                                "template": "toc.html", "data": self.issue})
        # add TOC NCX file
        files_to_render.append({"filename": os.path.join(self.folder["issue"], "toc.ncx"),
                                "template": "mobi_toc.ncx", "data": self.issue})
        # add OPF file
        files_to_render.append({"filename": os.path.join(self.folder["issue"], "respekt.opf"),
                                "template": "opf.opf", "data": self.issue})

        # render files
        for file_ in files_to_render:
            with open(file_["filename"], mode="w", encoding="utf-8-sig") as fw:
                log_info("using template '{tname}' to generate "
                         "file '{filepath}'".format(tname=file_["template"], filepath=file_["filename"]))
                raw_data = self.templater.serve_template(template_name=file_["template"], **file_["data"])
                fw.write(raw_data)
