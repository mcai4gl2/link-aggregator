import os
import re
import logging
import base64
import urllib.parse
import json
import time

import boto3
import requests
import mailparser
from bs4 import BeautifulSoup
from selenium import webdriver


class Config:
    def __init__(self):
        self.aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
        self.aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        self.aws_default_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.aws_endpoint_url = os.getenv('AWS_ENDPOINT_URL', None)
        self.aws_bucket_name = os.environ['AWS_BUCKET_NAME']
        self.from_white_list = os.getenv('FROM_WHITE_LIST', '').split(',')
        self.github_api_url = os.getenv('GITHUB_API_URL', 'https://api.github.com/repos/mcai4gl2/wiki/contents')
        self.github_auth_token = os.getenv('GITHUB_AUTH_TOKEN', '')
        self.selenium_url = os.getenv('SELENIM_URL', 'http://selenium:4444/wd/hub')


def get_url_title(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, features="html.parser")
    title = soup.find('title').renderContents()
    return title.decode('utf-8')
    

def get_url_title_using_selenim(url, selenium_url):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Remote(
        command_executor=selenium_url,
        options=options
    )
    try:
        driver.get(url)
        time.sleep(2)
        return driver.title
    finally:
        driver.close()
        driver.quit()


def find_urls_from_text(text: str):
    regex = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
    matches = re.findall(regex, text)
    return matches


def encode(input: str):
    message_bytes = input.encode('utf-8')
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode('utf-8')
    return base64_message


def decode(input: str):
    base64_bytes = input.encode('utf-8')
    message_bytes = base64.b64decode(base64_bytes)
    message = message_bytes.decode('utf-8')
    return message


def create_or_update_github(url: str, text: str, config: Config):
    logging.info(f'Checking if {url} already exists')
    default_headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {config.github_auth_token}'
    }
    response = requests.get(url, headers=default_headers)
    if response.status_code == 404:
        logging.info(f'Not found, creating a new file')
        body = {
            "message": "Adding new url",
            "content": encode(text)
        }
    else:
        content = decode(response.json()['content'])
        content += text
        logging.info(f'Found, updating the file')
        body = {
            "message": "Updating the file and adding a new url",
            "content": encode(content),
            "sha": response.json()['sha']
        }
    response = requests.put(url, headers=default_headers, data=json.dumps(body))
    logging.info(f'Updated github with response: {response.json()}')


def process_files_from_s3(config: Config):
    session = boto3.Session(aws_access_key_id=config.aws_access_key_id, 
        aws_secret_access_key=config.aws_secret_access_key, region_name=config.aws_default_region)
    s3 = session.resource('s3', endpoint_url=config.aws_endpoint_url)
    bucket = s3.Bucket(config.aws_bucket_name)
    files = []
    for file in bucket.objects.all():
        if file.key.startswith('processed') or file.key.startswith('failed') or file.key.startswith('ignored'):
            continue
        files.append(file)
    logging.info(f"Found {len(files)} files to process")
    for file in files:
        logging.info(f"Start processing file {file.key}")
        s3_file = s3.Object(config.aws_bucket_name, file.key)
        mail = mailparser.parse_from_string(s3_file.get()['Body'].read().decode('utf-8'))
        if mail.from_ == [] or mail.text_plain == '':
            logging.warning('No from and text_plain found, this may not be an email. Ignoring the file')
            bucket.copy({'Bucket': config.aws_bucket_name, 'Key': s3_file.key}, f'ignored/{s3_file.key}')
            s3_file.delete()
            continue
        if mail.from_[0][0] not in config.from_white_list:
            logging.warning(f'File is from {mail.from_[0][0]}, which is not configured. Ignoring the file')
            bucket.copy({'Bucket': config.aws_bucket_name, 'Key': s3_file.key}, f'ignored/{s3_file.key}')
            s3_file.delete()
            continue
        urls = []
        for text in mail.text_plain:
            urls.extend(find_urls_from_text(text))
        logging.info(f"Finding {len(urls)} urls to process")
        for url in urls:
            logging.info(f"Processing url: {url}")
            title = get_url_title(url)
            if not title:
                logging.info(f"{url} has no title tag, using selenium to get title")
                title = get_url_title_using_selenim(url, config.selenium_url)
            if not title:
                logging.warning(f"Cannot find title from {url}, skipping")
                continue
            logging.info(f"url: {url} has title: {title}")
            file_name = f"{mail.from_[0][0]}/{mail.date.strftime('%Y-%m')}.md"
            str_to_add = f"#### {title}\n@ {mail.date.strftime('%Y-%m-%d %H:%M:%S')}\n\n{url}\n\n"
            logging.info(f"Url to add: \n{str_to_add} to file: {file_name}")
            file_url = '/'.join([config.github_api_url, urllib.parse.quote(file_name)])
            create_or_update_github(file_url, str_to_add, config)
        logging.info(f"Finish processing file {s3_file.key}, moving to processed")
        bucket.copy({'Bucket': config.aws_bucket_name, 'Key': s3_file.key}, f'processed/{s3_file.key}')
        s3_file.delete()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    process_files_from_s3(Config())
