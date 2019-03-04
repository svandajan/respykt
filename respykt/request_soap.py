#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Optional

from bs4 import BeautifulSoup
from requests import Session, Response
from requests import get as pure_get
from requests import post as pure_post
from requests.exceptions import RequestException

from utils import log_error


class RequestSoap:
    session: Session = None

    def __init__(self, use_session: bool = True, session: Session = None) -> None:
        if session is None:
            if use_session:
                self.session = Session()
        else:
            self.session = session

    @staticmethod
    def is_good_response(resp: Response) -> bool:
        """
        Check if request was successfull, response has some content and it's type is html

        :param resp: Response
        :return:
        """
        content_type: str = resp.headers['Content-Type'].lower()
        return resp.status_code == 200 and content_type is not None and "html" in content_type

    @staticmethod
    def soap_get(url: str, session: Optional[Session] = None) -> Optional[BeautifulSoup]:
        # use "get" function of Session if it is not None
        if session is None:
            get = pure_get
        else:
            get = session.get
        try:
            resp: Response = get(url=url)
            if RequestSoap.is_good_response(resp):
                return BeautifulSoup(resp.content, "html.parser")
            else:
                return None
        except RequestException as e:
            log_error("Error - soap_get(url={url}): {e}".format(url=url, e=str(e)))
            return None

    @staticmethod
    def soap_post(url: str, data: Dict[str, str], session: Session = None) -> Optional[BeautifulSoup]:
        # use "post" function of Session if it is not None
        if session is None:
            post = pure_post
        else:
            post = session.post
        try:
            resp: Response = post(url=url, data=data)
            if RequestSoap.is_good_response(resp):
                return BeautifulSoup(resp.content, "html.parser")
            else:
                return None
        except RequestException as e:
            log_error("Error - soap_post(url={url}, data={data}): {e}".format(url=url, data=data, e=str(e)))
            return None

    def get(self, url: str) -> Optional[BeautifulSoup]:
        return RequestSoap.soap_get(url=url, session=self.session)

    def post(self, url: str, data: Dict[str, str]) -> Optional[BeautifulSoup]:
        return RequestSoap.soap_post(url=url, session=self.session, data=data)

    def get_session(self):
        return self.session
