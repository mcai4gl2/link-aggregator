import os
import requests
import pytest
import mock

import boto3

from link.aggregator.main import Config, get_url_title, process_files_from_s3


def test_get_url_title():
    result = requests.put("http://mockserver:1080/mockserver/expectation", json={
        'httpRequest': {
            'method': 'GET',
            'path': '/url-title'
        },
        'httpResponse': {
            'statusCode': 200,
            'headers': [
                {
                    'name': 'Content-Type',
                    'values': ['text/html; charset=utf-8']
                }
            ],
            'body': '<html><head><title>test title</title></head></html>'
        }
    })

    title = get_url_title("http://mockserver:1080/url-title")
    assert title == 'test title'

    response = requests.put("http://mockserver:1080/mockserver/reset")
    assert response.status_code == 200


@mock.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'AWS_BUCKET_NAME': 'test-bucket-empty',
    'AWS_ENDPOINT_URL': 'http://localstack:4566'
}, clear=True)
def test_process_files_from_s3_no_files():
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    s3 = session.resource('s3', endpoint_url='http://localstack:4566')
    s3.create_bucket(Bucket='test-bucket-empty')
    bucket = s3.Bucket('test-bucket-empty')
    config = Config()
    process_files_from_s3(config)
    assert bucket.delete()['ResponseMetadata']['HTTPStatusCode'] == 204


@mock.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'AWS_BUCKET_NAME': 'test-bucket-noemail',
    'AWS_ENDPOINT_URL': 'http://localstack:4566'
}, clear=True)
def test_process_files_from_s3_file_with_no_email():
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    s3 = session.resource('s3', endpoint_url='http://localstack:4566')
    config = Config()
    s3.create_bucket(Bucket=config.aws_bucket_name)
    bucket = s3.Bucket(config.aws_bucket_name)
    response = s3.Object(config.aws_bucket_name, 'test.txt').put(Body='Hello World!')

    process_files_from_s3(config)

    files = []
    for file in bucket.objects.all():
        s3_file = s3.Object(config.aws_bucket_name, file.key)
        s3_file.delete()
        files.append(file.key)
    assert bucket.delete()['ResponseMetadata']['HTTPStatusCode'] == 204
    assert all(f.startswith('ignored/') for f in files)


@mock.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'AWS_BUCKET_NAME': 'test-bucket-noemail',
    'AWS_ENDPOINT_URL': 'http://localstack:4566'
}, clear=True)
def test_process_files_from_s3_file_with_from_not_whitelisted(test_mail_content):
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    s3 = session.resource('s3', endpoint_url='http://localstack:4566')
    config = Config()
    s3.create_bucket(Bucket=config.aws_bucket_name)
    bucket = s3.Bucket(config.aws_bucket_name)
    response = s3.Object(config.aws_bucket_name, 'test.txt').put(Body=test_mail_content)

    process_files_from_s3(config)

    files = []
    for file in bucket.objects.all():
        s3_file = s3.Object(config.aws_bucket_name, file.key)
        s3_file.delete()
        files.append(file.key)
    assert bucket.delete()['ResponseMetadata']['HTTPStatusCode'] == 204
    assert all(f.startswith('ignored/') for f in files)


@mock.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test',
    'AWS_BUCKET_NAME': 'test-bucket-noemail',
    'AWS_ENDPOINT_URL': 'http://localstack:4566',
    'FROM_WHITE_LIST': 'Geng Li',
    'GITHUB_API_URL': 'http://mockserver:1080'
}, clear=True)
def test_process_files_from_s3_file_happy_path(test_mail_content):
    session = boto3.Session(aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    s3 = session.resource('s3', endpoint_url='http://localstack:4566')
    config = Config()
    s3.create_bucket(Bucket=config.aws_bucket_name)
    bucket = s3.Bucket(config.aws_bucket_name)
    response = s3.Object(config.aws_bucket_name, 'test.txt').put(Body=test_mail_content)

    requests.put("http://mockserver:1080/mockserver/expectation", json={
        'httpRequest': {
            'method': 'GET',
            'path': '/Geng%20Li/2022-04.md'
        },
        'httpResponse': {
            'statusCode': 404
        }
    })
    requests.put("http://mockserver:1080/mockserver/expectation", json={
        'httpRequest': {
            'method': 'PUT',
            'path': '/Geng%20Li/2022-04.md'
        },
        'httpResponse': {
            'statusCode': 204
        }
    })

    process_files_from_s3(config)

    files = []
    for file in bucket.objects.all():
        s3_file = s3.Object(config.aws_bucket_name, file.key)
        s3_file.delete()
        files.append(file.key)
    assert bucket.delete()['ResponseMetadata']['HTTPStatusCode'] == 204
    assert all(f.startswith('processed/') for f in files)
    response = requests.put("http://mockserver:1080/mockserver/reset")
    assert response.status_code == 200
