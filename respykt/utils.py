#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union, List

from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet

from .resources_downloader import ResourcesDownloader


def log(message: str, type_: str) -> None:
    if type_.upper() == "ERROR":
        print("Error - " + message)
    elif type_.upper() == "INFO":
        print("(info) - " + message)
    else:
        print(message)


def log_error(error_message: str) -> None:
    log(error_message, "ERROR")


def log_info(message: str) -> None:
    log(message, "INFO")


def return_max_figure_source(sourceset: str, width: int = None) -> Optional[str]:
    """
    Returns source with less than or equal specified width
    :param sourceset: string like 'url1 180w, url2 320w, url3 640w'
    :param width: maximum allowed width, if None, uses MAXINT to get maximum width
    :return:
    """
    # python3 doesn't have MAXINT value, so we use this value as quite large width
    if width is None:
        width = 2 ** 31 - 1
    try:
        # create dictionary with pairs of (width: 'url') like {180: 'url1', 320: 'url2', 640: 'url3'}
        sources = {int(s.split(" ")[1][:-1]): s.split(" ")[0] for s in sourceset.split(", ")}
        # get maximum of keys list limited by specified width
        max_size = max(filter(lambda x: x <= width, sources.keys()))
        # return url
        return sources[max_size]
    except ValueError as e:
        # 'sourceset' is probably in wrong format
        log_error("return_max_figure_source(sourceset={sset}, width={width}): failed "
                  "because of ValueError: {e}".format(sset=str(sourceset), width=width, e=e))
        return None
    except TypeError as e:
        log_error("return_max_figure_source(sourceset={sset}, width={width}): failed "
                  "because of TypeError: {e}".format(sset=str(sourceset), width=width, e=e))
        return None


def get_text(tag: Union[Tag, ResultSet]) -> Union[str, List[str]]:
    if tag is None:
        return ""
    elif type(tag) is Tag:
        return tag.get_text().strip(", ")
    elif type(tag) is ResultSet:
        result = []
        for t in tag:
            if t is None:
                result.append("")
            else:
                result.append(t.get_text().strip(", "))
        return result
    else:
        return tag


def replace_figure_with_img(res_dl: ResourcesDownloader, parent: BeautifulSoup, figure: Tag, max_width=1024,
                            image_folder: str = "../resources", return_src: bool = False) -> Optional[Union[Tag, str]]:
    # get source data from either 'srcset' or 'src' tags
    try:
        srcset: str = figure.img["srcset"]
        src: str = return_max_figure_source(srcset, max_width)
    except TypeError as e_type:
        # no "img" children of figure
        log_error("Error - replace_figure_with_img: figure does not have img tag defined: " + str(e_type))
        return None
    except KeyError:
        # img doesn't have "srcset" attribute, let's check for "src" instead
        try:
            src = figure.img["src"]
        except KeyError:
            # no "src" either, so skip it
            log_error("Error - replace_figure_with_img: figure's img doesn't have neither 'src' nor 'srcset' defined")
            return None
    if src is None or src == "":
        log_error("Error - replace_figure_with_img: no source image found")
        return None
    # get alternative text (caption)
    try:
        alt_text = get_text(figure.figcaption)
    except TypeError:
        # no "figcaption" of figure
        try:
            alt_text = figure.img["alt"]
        except KeyError as e_key:
            log_error("Warning - replace_figure_with_img: cannot find title text for image: {e}".format(e=str(e_key)))
            alt_text = None
    new_src = image_folder + "/" + res_dl.add_url(src)
    img = parent.new_tag("img", src=new_src, alt=alt_text)
    # BeautifulSoup function for tag replacement
    figure.replace_with(img)
    if return_src:
        return new_src
    else:
        return img
