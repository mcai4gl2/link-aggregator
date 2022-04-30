from selenium import webdriver
import requests
import time


def test_web_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument('--ignore-certificate-errors')
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=options
    )
    try:
        result = requests.put("http://mockserver:1080/mockserver/expectation", json={
            'httpRequest': {
                'method': 'GET',
                'path': '/ping'
            },
            'httpResponse': {
                'statusCode': 200,
                'body': '<!DOCTYPE html><html><head><title>test title</title></head></html>'
            }
        })

        driver.get("http://mockserver:1080/ping")
        assert driver.title == "test title"
    finally:
        # needs to close, otherwise next run is blocking
        driver.close()
        driver.quit()
        response = requests.put("http://mockserver:1080/mockserver/reset")
        assert response.status_code == 200
