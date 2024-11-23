from bs4 import BeautifulSoup
from parsel import Selector


class NoteContent:
    title: str = ""
    author: str = ""
    publish_date: str = ""
    detail_link: str = ""

    def __str__(self):
        return f"""
Title: {self.title}
User: {self.author}
Publish Data: {self.publish_date}
Detail Link: {self.detail_link}
"""

def parse_html_use_bs(html_content: str):
    """
        使用BeautifulSoup提取帖子标题、作者、发布日期，基于css选择器提取
        :param html_content: html源代码内容
        :return:
    """
    note_content = NoteContent()
    soup = BeautifulSoup(html_content, "lxml")

    # extract the title and remove the line break and space characters on the left and right
    note_content.title = soup.select("div.r-ent div.title a")[0].text.strip()

    # extract author
    note_content.author = soup.select("div.r-ent div.meta div.author")[0].text.strip()

    # extract publish data
    note_content.publish_date = soup.select("div.r-ent div.meta div.date")[0].text.strip()

    # extract note link
    note_content.detail_link = soup.select("div.r-ent div.title a")[0]["href"]

    print("BeautifulSoup" + "*" *30)
    print(note_content)
    print("BeautifulSoup" + "*" *30)

def parse_html_use_parse(html_content: str):
    """
        使用parsel提取帖子标题、作者、发布日期，基于xpath选择器提取
        :param html_content: html源代码内容
        :return:
    """
    note_content = NoteContent()
    # use parsel selector
    selector = Selector(html_content)

    note_content.title = selector.xpath("//div[@class='r-ent']/div[@class='title']/a/text()").extract_first().strip()
    note_content.author = selector.xpath("//div[@class='r-ent']/div[@class='meta']/div[@class='author']/text()").extract_first().strip()
    note_content.publish_date = selector.xpath("//div[@class='r-ent']/div[@class='meta']/div[@class='date']/text()").extract_first().strip()
    note_content.detail_link = selector.xpath("//div[@class='r-ent']/div[@class='title']/a/@href").extract_first()

    print("parsel" + "*" * 30)
    print(note_content)
    print("parsel" + "*" * 30)

if __name__ == '__main__':
    ori_html = """
    <div class="r-ent">
        <div class="nrec"><span class="hl f3">11</span></div>
        <div class="title">

            <a href="/bbs/Stock/M.1711544298.A.9F8.html">[新聞] 童子賢：用稅收補貼電費非長久之計 應共</a>

        </div>
        <div class="meta">
            <div class="author">addy7533967</div>
            <div class="article-menu">

                <div class="trigger">⋯</div>
                <div class="dropdown">
                    <div class="item"><a href="/bbs/Stock/search?q=thread%3A%5B%E6%96%B0%E8%81%9E%5D+%E7%AB%A5%E5%AD%90%E8%B3%A2%EF%BC%9A%E7%94%A8%E7%A8%85%E6%94%B6%E8%A3%9C%E8%B2%BC%E9%9B%BB%E8%B2%BB%E9%9D%9E%E9%95%B7%E4%B9%85%E4%B9%8B%E8%A8%88+%E6%87%89%E5%85%B1">搜尋同標題文章</a></div>

                    <div class="item"><a href="/bbs/Stock/search?q=author%3Aaddy7533967">搜尋看板內 addy7533967 的文章</a></div>

                </div>

            </div>
            <div class="date"> 3/27</div>
            <div class="mark"></div>
        </div>
    </div>
    """
    parse_html_use_bs(ori_html)
    print("")
    parse_html_use_parse(ori_html)
