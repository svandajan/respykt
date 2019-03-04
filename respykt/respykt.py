#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
from os.path import join as path_join
from typing import Dict, List, Union

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session

from request_soap import RequestSoap
from resources_downloader import ResourcesDownloader
from template_engine import TemplateEngine
from utils import get_text, replace_figure_with_img, log_error


class Respykt:
    config_file: str = None
    session: Session = None
    dl_wait_time: float = None
    url: Dict[str, str] = None
    folder: Dict[str] = None
    issue: Dict[str] = None
    user: Dict[str] = None

    requester: RequestSoap = None
    downloader: ResourcesDownloader = None
    templater: TemplateEngine = None

    articles: List[Dict[str, str]] = None
    categories: Dict[str, Dict[str, Union[str, List]]] = None

    def __init__(self, config_file: str = None, issue: str = None):
        self.session = Session()
        self.folder = {}
        self.url = {"home": "https://www.respekt.cz/"}
        self.config_file = config_file
        if config_file:
            self.load_configuration(config_file)

        if "issue" not in self.folder:
            self.folder["issue"] = "issue"
        self.folder["issue_res"] = path_join(self.folder["issue"], "resources")
        if "templates" not in self.folder:
            self.folder["templates"] = "templates"
        if "mako_modules" not in self.folder:
            self.folder["mako_modules"] = "mako_modules"

        self.requester = RequestSoap(session=self.session)
        self.downloader = ResourcesDownloader(session=self.session, wait_time=self.dl_wait_time,
                                              data_dir=self.folder["issue_res"])
        self.templater = TemplateEngine(templates_dir=self.folder["templates"],
                                        module_dir=self.folder["mako_modules"])

    def load_configuration(self, config_file: str = None) -> None:
        if config_file is None:
            config_file = self.config_file
        if config_file is None:
            log_error("Error - Respkyt::load_configuration: No config file provided")
            return
        if not os.path.exists(config_file):
            log_error(
                "Error - Respkyt::load_configuration: File '{config}' does not exist".format(config=config_file))
            return

        config = configparser.ConfigParser()
        config.read(config_file)

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
        if "DONWLOAD" in config:
            if "wait_time" in config["DOWNLOAD"]:
                self.dl_wait_time = config["DOWNLOAD"]["wait_time"]

    def login(self):
        if "username" in self.user and "password" in self.user:
            login_postdata = {"username": self.user["username"], "password": self.user["password"],
                              "do": "authBox-loginForm-submit", "_do": "authBox-loginForm-submit"}
            login_url = self.url["home"]
            self.requester.post(url=login_url, data=login_postdata)

    def get_current_issue(self):
        home_page = self.requester.get(self.url["home"])
        issue_url = home_page.find(class_="currentissue").a["href"]
        self.url["issue"] = issue_url
        return issue_url

    def parse_toc_page(self):
        if "issue" not in self.url:
            self.get_current_issue()
        toc_page = self.requester.get(self.url["issue"])

        articles_raw = toc_page(class_="issuedetail-categorized-item")
        self.articles = []
        self.categories = {}
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

            if ("despekt" in article["category"].lower()) or ("anketa" in article["category"].lower()):
                # those are special cases, will deal with them later
                # (each will require special template and 'anketa' ('survey') entirely different parsing)
                continue
            if article["is_locked"]:
                # hit paywal...
                continue

            article["no"] = articles_count
            art_category = get_text(art.find_previous_sibling(class_="issuedetail-categorized-sectionname"))
            if art_category not in self.categories:
                categories_count += 1
                self.categories[art_category] = {"name": art_category, "id": categories_count, "articles": []}

            article["category"] = art_category
            self.categories[art_category]["articles"].append(article)
            self.articles.append(article)

    def download_resources(self):
        self.downloader.download_all()

    def get_articles(self):
        article_filename_format = "article_{no:04d}.html"

        if self.articles is None:
            self.parse_toc_page()

        folder_articles = path_join(self.folder["issue"], "html")
        if not os.path.exists(folder_articles):
            os.mkdir(folder_articles)

        for article in self.articles:
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
            article["template_name"] = "article.html"
            article["filename"] = article_filename_format.format(no=article["no"])
            article["filename"] = path_join(folder_articles, article["filename"])
            with open(path_join(article["filename"]), mode="w", encoding="utf8") as fw:
                fw.write(self.templater.serve_template(**article))

    def run(self):
        self.login()
        self.parse_toc_page()
        self.get_articles()
        self.download_resources()

# TODO:
#   - generate TOC html page
#   - generate toc.ncx and opf file
#   - create ebooks
