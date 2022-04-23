import os
import mock

from link.aggregator.main import Config, find_urls_from_text, encode, decode


@mock.patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'TEST_KEY',
    'AWS_SECRET_ACCESS_KEY': 'TEST_SECRET_KEY',
    'AWS_BUCKET_NAME': 'TEST_BUCKET'
}, clear=True)
def test_config():
    config = Config()
    assert config.aws_access_key_id == 'TEST_KEY'
    assert config.aws_secret_access_key == 'TEST_SECRET_KEY'
    assert config.aws_default_region == 'us-east-1'
    assert config.aws_endpoint_url == None
    assert config.aws_bucket_name == 'TEST_BUCKET'


def test_extract_url():
    text = """
    add1 http://mit.edu.com abc
    add2 https://facebook.jp.com.2. abc
    add3 www.google.be. uvw
    add4 https://www.google.be. 123
    add5 www.website.gov.us test2
    Hey bob on www.test.com. 
    another test with ipv4 http://192.168.1.1/test.jpg. toto2
    website with different port number www.test.com:8080/test.jpg not port 80
    www.website.gov.us/login.html
    test with ipv4 (192.168.1.1/test.jpg).
    search at google.co.jp/maps.
    test with ipv6 2001:0db8:0000:85a3:0000:0000:ac1f:8001/test.jpg.
    """
    results = find_urls_from_text(text)
    assert results == ['http://mit.edu.com', 'https://facebook.jp.com', 
        'www.google.be', 'https://www.google.be', 'www.website.gov.us', 
        'www.test.com', 'http://192.168.1.1/test.jpg', 
        'www.test.com:8080/test.jpg', 'www.website.gov.us/login.html', 
        '192.168.1.1/test.jpg', 'google.co.jp/maps', 
        '2001:0db8:0000:85a3:0000:0000:ac1f:8001/test.jpg'
    ]

    results = find_urls_from_text('no url')
    assert results == []


def test_base64_encode_and_decode():
    msg = 'bXkgdXBkYXRlZCBmaWxlIGNvbnRlbnRz'
    decoded_msg = decode(msg)
    encoded_msg = encode(decoded_msg)
    assert msg == encoded_msg
    assert decoded_msg == 'my updated file contents'
