def test_wisselwerking_frontend(browser, base_address):
    browser.get(base_address)
    try:
        assert 'Wisselwerking' in browser.title
    except:
        print(browser.title)
        raise


def test_wisselwerking_admin(browser, admin_address):
    browser.get(admin_address)
    try:
        assert 'Django' in browser.title
    except:
        print(browser.title)
        raise


def test_wisselwerking_api(browser, api_address):
    browser.get(api_address)
    try:
        assert 'Api Root' in browser.title
    except:
        print(browser.title)
        raise


def test_wisselwerking_api_auth(browser, api_auth_address):
    browser.get(api_auth_address + 'login/')
    try:
        assert 'Django REST framework' in browser.title
    except:
        print(browser.title)
        raise
