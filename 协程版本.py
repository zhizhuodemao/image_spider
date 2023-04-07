from lxml import etree
import asyncio
import aiohttp
import aiofiles
import os
from utils import data_utils
import time

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62"
}
# 爬取几个类别 默认爬取一个类别 取值范围1-7 爬取全部类别为-1
class_num = 2
# 每个类别爬取多少页 从第一页开始 默认爬取1页
page_num = 2
# 从第几页开始爬取
first_page = 1


def get_page_url():
    first_page_url = "https://www.madouplus.cc/"
    page = data_utils.send_get(first_page_url, headers)
    more_url = page.xpath('//a[text()="查看全部" or text()="查看更多"]/@href')[:class_num]
    return more_url


async def get_img_page_url(page_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url, headers=headers) as resp:
            text = await resp.text(encoding="utf-8")
            page = etree.HTML(text)
            page_dict = data_utils.get_page_info(page)
    print(page_url, "请求成功,即将返回数据")
    print(f"该页面共有{len(page_dict['img_page_list'])}个图片集")
    return page_dict


async def get_img_info(page_dict):
    img_info_list = []
    title = page_dict["title"]
    img_list = page_dict["img_page_list"]
    for img_info in img_list:
        img_page_url = img_info["img_page_url"]
        img_page_title = img_info["img_page_title"]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_page_url, headers=headers) as resp:
                    text = await resp.text(encoding="utf-8")
                    html = etree.HTML(text)
                    p_list = html.xpath('//div[@class="content"]//div[@class="article-content clearfix"]/p')
                    for p in p_list[1:]:
                        img_url = p.xpath("./img/@src")[0]
                        img_path = f'./{title}/{img_page_title}/{str(img_url).split("/")[-1]}'
                        img_info = {"img_url": img_url,
                                    "img_path": img_path}
                        img_info_list.append(img_info)
            print(f"页面{img_page_url}提取成功,即将进入图片展示页面")
        except:
            print(img_page_url, "出错了")
            continue
    return img_info_list


async def download_one_img(img_path, img_url):
    img_dir = "/".join(img_path.split("/")[:-1])
    # 设置超时时间
    timeout = aiohttp.ClientTimeout(total=10)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    if os.path.exists(img_path):
        print(f"图片{img_path}已经存在,即将进入下一个图片下载")
    else:
        for i in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url, headers=headers, timeout=timeout) as resp:
                        content = await resp.content.read()
                        async with aiofiles.open(img_path, "wb") as f:
                            await f.write(content)
                print(f"图片{img_path}下载成功")
                break
            except:
                print(f"图片{img_path}下载失败,即将开始第{i + 1}次重新下载")
                await asyncio.sleep(1)


async def main():
    start = time.time()
    all_page_dict = []
    page_url_list = get_page_url()
    tasks = []
    for page_url in page_url_list:
        for i in range(first_page, page_num + first_page):
            if i != 1:
                page_url_new = page_url + f"/page/{i}"
            else:
                page_url_new = page_url
            tasks.append(asyncio.create_task(get_img_page_url(page_url_new)))
    results, _ = await asyncio.wait(tasks)
    for result in results:
        all_page_dict.append(result.result())
    img_info_tasks = []
    for page_dict in all_page_dict:
        img_info_tasks.append(asyncio.create_task(get_img_info(page_dict)))
    img_info_results, _ = await asyncio.wait(img_info_tasks)
    img_info_lists = []
    for img_info_result in img_info_results:
        img_info_lists.append(img_info_result.result())
    img_info_tasks = []
    for img_info_list in img_info_lists:
        for img_info in img_info_list:
            img_url = img_info["img_url"]
            img_path = img_info["img_path"]
            img_info_tasks.append(asyncio.create_task(download_one_img(img_path, img_url)))
    await asyncio.wait(img_info_tasks)
    end = time.time()
    print(f"共花费时间{end - start}秒")


if __name__ == '__main__':
    # 爬取第一个类别 第一页 共花费时间17.23799729347229秒
    # 爬取两个类别 2页 共花费时间19.757012128829956秒 但是少下载了3组图片
    # 只爬取这么点数据 协程就比单线程快10倍以上
    # 可想而知 如果爬取大量数据 协程和单线程就没法比较了
    # 所以说 下载任务就用协程
    asyncio.run(main())
