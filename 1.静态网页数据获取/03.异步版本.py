import httpx
from parsel import Selector

from common import *

FIRST_N_PAGE = 10  # 前N页的论坛帖子数据
BASE_HOST = "https://www.ptt.cc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
PROXY = {'http://':'http://localhost:8889', 'https://':'http://localhost:8889'}

async def parse_note_use_parsel(html_content: str) -> NoteContent:
    """
        使用parse提取帖子标题、作者、发布日期，基于css选择器提取
        需要注意的时，我们在提取帖子的时候，可能有些帖子状态不正常，会导致没有link之类的数据，所以我们在取值时最好判断一下元素长度
        :param html_content: html源代码内容
        :return:
    """
    note_content = NoteContent()
    selector = Selector(html_content)
    title_elements = selector.css("div.r-ent div.title a")
    author_elements = selector.css("div.r-ent div.meta div.author")
    date_elements = selector.css("div.r-ent div.meta div.date")

    note_content.title = title_elements[0].root.text.strip() if len(title_elements) > 0 else ""
    note_content.author = author_elements[0].root.text.strip() if len(author_elements) > 0 else ""
    note_content.publish_date = date_elements[0].root.text.strip() if len(date_elements) > 0 else ""
    note_content.detail_link = title_elements[0].attrib['href'] if len(title_elements) > 0 else ""

    return note_content

async def get_previous_page_number() -> int:
    """
    打开首页提取上一页的分页number
    :return:
    """
    url = "/bbs/Stock/index.html"
    async with httpx.AsyncClient(proxies=PROXY) as client:
        # TODO: 下面的代码极有可能无法访问成功。因为网络不可达
        response = await client.get(BASE_HOST+url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception("send request got error status code, reason is : "+response.text)
        selector = Selector(response.text)
        pagination_link = selector.css("#action-bar-container > div > div.btn-group.btn-group-paging > a:nth-child(2)")[0].attrib['href']
        previous_page_number = int(pagination_link.replace("/bbs/Stock/index","").replace(".html",""))
        return previous_page_number

async def fetch_bbs_note_list(previous_number: int) -> List[NoteContent]:
    """
    获取前N页的帖子列表
    :param previous_number:
    :return:
    """
    note_list: List[NoteContent] = []
    start_page_number = previous_number+1
    end_page_number = start_page_number-FIRST_N_PAGE
    async with httpx.AsyncClient(proxies=PROXY) as client:
        for page_number in range(start_page_number,end_page_number,-1):
            # print(f"开始获取第 {page_number} 页的帖子列表...")
            # 存储到文件中
            with open("async_backlog.txt", "a+") as f:
                f.writelines(f"开始获取第 {page_number} 页的帖子列表...\n")
            url = f"/bbs/Stock/index{page_number}.html"
            # TODO：下面内容可能不生效，因为网络不可达
            response = await client.get(BASE_HOST+url,headers=HEADERS)
            if response.status_code != 200:
                print(f"第{page_number}页帖子获取异常,原因：{response.text}")
                continue
            selector = Selector(text=response.text)
            all_note_elements = selector.css("div.r-ent")
            for note_element_html in all_note_elements:
                node_content = await parse_note_use_parsel(note_element_html.get()) # TODO:看看 get（）方法返回什么
                note_list.append(node_content)
            # print(f"结束获取第 {page_number} 页的帖子列表，本次获取到:{len(all_note_elements)} 篇帖子...")
            with open("async_backlog.txt", "a+") as f:
                f.writelines(f"结束获取第 {page_number} 页的帖子列表，本次获取到:{len(all_note_elements)} 篇帖子...\n")
    return note_list

async def fetch_bbs_note_detail(note_content: NoteContent) -> NoteContentDetail:
    """
        获取帖子详情页数据
        :param note_content:
        :return:
    """
    # print(f"开始获取帖子 {note_content.detail_link} 详情页....")
    with open("async_backlog.txt", "a+") as f:
        f.writelines(f"开始获取帖子 {note_content.detail_link} 详情页....\n")
    note_content_detail = NoteContentDetail()
    note_content_detail.title = note_content.title
    note_content_detail.author = note_content.author
    note_content_detail.detail_link = BASE_HOST + note_content.detail_link

    async with httpx.AsyncClient(proxies=PROXY) as client:
        # TODO:下面代码可能不会执行，因为网络不可达
        response = await client.get(note_content_detail.detail_link, headers=HEADERS)
        if response.status_code != 200:
            print(f"帖子：{note_content.title} 获取异常,原因：{response.text}")
            return note_content_detail
        selector = Selector(response.text)
        note_content_detail.publish_datetime = selector.css("#main-content > div:nth-child(4) > span.article-meta-value")[0].root.text

        # 解析推文
        note_content_detail.push_comment = []
        all_push_contents = selector.css("div.push")
        for push_content in all_push_contents:
            note_push_content = NotePushComment()
            note_push_content.push_user_name = push_content.css("span.push-userid")[0].root.text if push_content.css("span.push-userid") else ""
            note_push_content.push_content = push_content.css("span.push-content")[0].root.text if push_content.css("span.push-content") else ""
            note_push_content.push_time = push_content.css("span.push-ipdatetime")[0].root.text if push_content.css("span.push-ipdatetime") else ""
            note_content_detail.push_comment.append(note_push_content)

    # print(note_content_detail)
    with open("async_backlog.txt", "a+") as f:
        f.writelines(str(note_content_detail)+"\n")
    return note_content_detail

async def run_crawler(save_notes: List[NoteContentDetail]):
    previous_number = await get_previous_page_number()
    note_list = await fetch_bbs_note_list(previous_number)
    for note_content in note_list:
        if not note_content.detail_link:
            continue
        note_content_detail = await fetch_bbs_note_detail(note_content)
        save_notes.append(note_content_detail)
    # print("任务爬取完成.......")
    with open("async_backlog.txt", "a+") as f:
        f.writelines("任务爬取完成......."+"\n")


if __name__ == '__main__':
    import asyncio

    all_note_content_detail: List[NoteContentDetail] = []
    asyncio.run(run_crawler(all_note_content_detail))

