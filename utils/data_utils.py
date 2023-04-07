import requests
from lxml import etree


def get_page_info(page):
    img_divs = page.xpath('//div[@id="posts"]/div')
    title = page.xpath('/html/body/div[2]/div/h1/text()')
    title = "".join(title).strip().replace(" ", "-")
    img_dict_list = []
    for img_div in img_divs:
        img_dict = {}
        img_url = img_div.xpath('./div[@class="img"]/a/@href')
        img_url = "".join(img_url).strip().replace(" ", "-")
        img_title = img_div.xpath('./div[@class="img"]/a/@title')
        img_title = "".join(img_title).strip().replace(" ", "-")
        img_dict["img_page_url"] = img_url
        img_dict["img_page_title"] = img_title
        img_dict_list.append(img_dict)
    page_dict = {"title": title, "img_page_list": img_dict_list}
    return page_dict


def send_get(page_url, headers):
    resp = requests.get(page_url, headers=headers)
    resp.encoding = "utf-8"
    page = etree.HTML(resp.text)
    return page
