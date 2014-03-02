from bs4 import BeautifulSoup

class HtmlParser(object):
    """for different host, we need build different parser.
    this parser only used for 22mm.cc
    """
    IMAGE = 0
    PAGE = 1

    def _gen_url(self, host, url):
        if url.startswith("/"):
            url = host + url
        return url.strip()

    def _is_vaild_resource(self, url):
        """simple check is vaild image resource
        TODO: we can rewrite this method to get more effective result
        """
        if self._is_vaild_url(url) and url.endswith(".jpg") and url.find("meimei22.com/") != -1 and url.find("pic") != -1:
            return True
        return False

    def _is_vaild_url(self, url):
        """ simple check is a vaild url
        TODO: we can rewrite this method to get more effective result
        """
        return True if url and url.startswith("http://") and (url.find("meimei22") != -1 or url.find("22mm") != -1) else False

    def parser_html(self, url, html):
        """parser html and get the needed resources"""
        soup = BeautifulSoup(html)
        links, image_links, href_links = [], [], []
        for img_tag in soup.find_all("img"):
            link = img_tag.get("src")
            if link:
                link = self._gen_url(url, link)
            image_links.append(link)
        links.extend([(self.IMAGE, link) for link in image_links if self._is_vaild_resource(link)])
        for href_tag in soup.find_all("a"):
            link = href_tag.get("href")
            if link:
                link = self._gen_url(url, link)
                href_links.append(link)
        links.extend([(self.PAGE, link) for link in href_links if self._is_vaild_url(link)])
        return links
