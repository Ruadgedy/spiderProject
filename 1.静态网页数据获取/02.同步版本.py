from typing import List

import requests
from bs4 import BeautifulSoup
from common import *


FIRST_N_PAGE = 10
BASE_HOST = "https://www.ptt.cc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
PROXY = {'http':'http://localhost:8889', 'https':'http://localhost:8889'}

def parse_note_use_bs(html_content: str) -> NoteContent:
    """
        使用BeautifulSoup提取帖子标题、作者、发布日期，基于css选择器提取
        需要注意的时，我们在提取帖子的时候，可能有些帖子状态不正常，会导致没有link之类的数据，所以我们在取值时最好判断一下元素长度
        :param html_content: html源代码内容
        :return:
     """

    # 初始化一个帖子保存容器
    note_content = NoteContent()
    soup = BeautifulSoup(html_content, "lxml")

    # 提取标题并去除左右除换行的空白字符
    note_content.title = soup.select("div.r-ent div.title a")[0].text.strip() if len(soup.select("div.r-ent div.title a")) > 0 else ""

    # 提取作者
    note_content.author = soup.select("div.r-ent div.meta div.author")[0].text.strip() if len(soup.select("div.r-ent div.meta div.author")) > 0 else ""

    # 提取发布日期
    note_content.publish_date = soup.select("div.r-ent div.meta div.date")[0].text.strip() if len(soup.select("div.r-ent div.meta div.date")) > 0 else ""

    # 提取帖子链接
    note_content.detail_link = soup.select("div.r-ent div.title a")[0]['href'] if len(soup.select("div.r-ent div.title a")) > 0 else ""

    return note_content

def get_previous_page_number() -> int:
    """
    打开首页提取上一页的分页Number
    :return:
    """
    uri = "/bbs/Stock/index.html"

    response = requests.get(url=BASE_HOST+uri, headers=HEADERS, proxies=PROXY)
    if response.status_code != 200:
        raise Exception("send request got error status code, reason: ", response.text)
    soup = BeautifulSoup(response.text, "lxml")

    # css选择器
    css_selector = "#action-bar-container > div > div.btn-group.btn-group-paging > a:nth-child(2)"
    pagination_link = soup.select(css_selector)[0]["href"].strip()

    # pagination_link 提取数字部分
    previous_page_number = int(pagination_link.replace("/bbs/Stock/index","").replace(".html",""))

    return previous_page_number

def fetch_bbs_note_list(previous_number: int) -> List[NoteContent]:
    """
    获取前N页的帖子列表
    :param previous_number:
    :return:
    """
    notes_list: List[NoteContent] = []

    # 计算分页的起始位置和终止位置，由于我们也是要爬首页的，所以得到上一页的分页Number之后，应该还要加1才是我们的起始位置
    start_page_number = previous_number + 1
    end_page_number = start_page_number - FIRST_N_PAGE
    for page_number in range(start_page_number, end_page_number, -1):
        print(f"开始获取第 {page_number} 页的帖子列表...")

        # 拼接url
        url = f"/bbs/Stock/index{page_number}.html"
        response = requests.get(url = BASE_HOST+url, headers=HEADERS, proxies=PROXY)
        if response.status_code != 200:
            print(f"第 {page_number} 页页面数据获取出错")
            continue

        # 使BeautifulSoup的CSS选择器解析数据，div.r-ent 是帖子列表html页面中每一个帖子都有的css class
        soup = BeautifulSoup(response.text, "lxml")

        # TODO: 有问题的选择器  fixed
        all_notes_elements = soup.select("#main-container > div.r-list-container.action-bar-margin.bbs-screen > div.r-ent")
        for note_element in all_notes_elements:
            note_content = parse_note_use_bs(note_element.prettify())  # TODO:验证替换为 text是否可行->不可行，prettify返回的是html的字符串格式，text仅返回了文本
            notes_list.append(note_content)
        # print(f"结束获取第 {page_number} 页的帖子列表，本次获取到 {len(all_notes_elements)} 条数据")
        # 打印内容保存在文件里
        with open('backlog.txt', "a+") as f:
            f.writelines(f"结束获取第 {page_number} 页的帖子列表，本次获取到 {len(all_notes_elements)} 条数据\n")

    return notes_list

def fetch_bbs_note_detail(note_content: NoteContent) -> NoteContentDetail:
    """
    获取帖子详情页数据
    :param note_content:
    :return:
    """

    print(f"开始获取帖子 {note_content.detail_link} 详情页...")
    note_content_detail = NoteContentDetail()

    # note_content有值的, 我们直接赋值，就不要去网页提取了，能偷懒就偷懒（初学者还是要老老实实的都去提取一下数据）
    note_content_detail.title = note_content.title
    note_content_detail.author = note_content.author
    note_content_detail.detail_link = BASE_HOST + note_content.detail_link

    # TODO:还差推文详情 和  推文时间  DONE

    response = requests.get(note_content_detail.detail_link, headers=HEADERS, proxies=PROXY)
    if response.status_code != 200:
        print(f"帖子：{note_content.title} 获取异常,原因：{response.text}")
        return note_content_detail

    soup = BeautifulSoup(response.text, "lxml")
    note_content_detail.publish_datetime = soup.select("#main-content > div:nth-child(4) > span.article-meta-value")[0].text

    # 处理推文
    note_content_detail.push_comment = []
    all_push_elements = soup.select("#main-content > div.push")
    for push_element in all_push_elements:
        note_push_comment = NotePushComment()
        if len(push_element.select("span")) < 3:
            continue

        note_push_comment.push_user_name = push_element.select("span.push-userid")[0].text.strip()
        note_push_comment.push_content = push_element.select("span.push-content")[0].text.strip()
        note_push_comment.push_time = push_element.select("span.push-ipdatetime")[0].text.strip()

        note_content_detail.push_comment.append(note_push_comment)
        # print(note_content_detail)
        # 写入文件处理
        with open('backlog.txt', "a+") as f:
            f.writelines(str(note_content_detail))

    return note_content_detail

def run_crawler(save_notes: List[NoteContentDetail]):
    """
        爬虫主程序
        :param save_notes: 数据保存容器
        :return:
    """
    # step1: 获取分页number
    previous_number = get_previous_page_number()

    # step2: 获取前N页帖子集合列表
    note_list = fetch_bbs_note_list(previous_number)

    # step3: 获取帖子详情+推文
    for note_content in note_list:
        note_content_detail = fetch_bbs_note_detail(note_content)
        save_notes.append(note_content_detail)

    print(f"任务已完成")

if __name__ == '__main__':
    with open("backlog.txt", "w+") as f:
        f.truncate(0)
    all_notes_content_detail = []
    run_crawler(all_notes_content_detail)