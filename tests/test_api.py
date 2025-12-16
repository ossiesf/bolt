def test_shorten(client):
    response = client.post('/shorten', json={'url': 'https://google.com'})
    assert response.status_code == 200
    data = response.json()
    assert 'short_code' in data
    assert 'short_url' in data

def test_redirect(client):
    # First, shorten a URL to get a short code
    shorten_response = client.post('/shorten', json={'url': 'https://google.com'})
    short_code = shorten_response.json()['short_code']

    # Now, test the redirect
    redirect_response = client.get(f'/get/{short_code}', follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers['location'] == 'https://google.com'

def test_redirect_not_found(client):
    response = client.get('/get/nonexistentcode', follow_redirects=False)
    assert response.status_code == 404
    data = response.json()
    assert data['detail'] == "Mapping not found - have you shortened this URL yet?"

def test_shorten_and_redirect(client):
    url_to_shorten = 'https://example.com'
    shorten_response = client.post('/shorten', json={'url': url_to_shorten})
    short_code = shorten_response.json()['short_code']

    redirect_response = client.get(f'/get/{short_code}', follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers['location'] == url_to_shorten 

def test_shorten_invalid_url(client):
    response = client.post('/shorten', json={'url': 'not-a-valid-url'})
    assert response.status_code == 200  # Assuming the app does not validate URL format
    data = response.json()
    assert 'short_code' in data
    assert 'short_url' in data

def test_shorten_empty_url(client):
    response = client.post('/shorten', json={'url': ''})
    assert response.status_code == 200  # Assuming the app does not validate empty URL
    data = response.json()
    assert 'short_code' in data
    assert 'short_url' in data

def test_multiple_shortens(client):
    urls = ['https://site1.com', 'https://site2.com', 'https://site3.com']
    short_codes = set()

    for url in urls:
        response = client.post('/shorten', json={'url': url})
        assert response.status_code == 200
        data = response.json()
        assert 'short_code' in data
        assert 'short_url' in data
        short_codes.add(data['short_code'])

    assert len(short_codes) == len(urls)  # Ensure all short codes are unique

def test_redirect_after_multiple_shortens(client):
    urls = ['https://siteA.com', 'https://siteB.com', 'https://siteC.com']
    short_code_map = {}

    for url in urls:
        response = client.post('/shorten', json={'url': url})
        data = response.json()
        short_code_map[data['short_code']] = url

    for short_code, original_url in short_code_map.items():
        redirect_response = client.get(f'/get/{short_code}', follow_redirects=False)
        assert redirect_response.status_code == 302
        assert redirect_response.headers['location'] == original_url

def test_shorten_large_url(client):
    large_url = 'https://example.com/' + 'a' * 5000  # Very long URL
    response = client.post('/shorten', json={'url': large_url})
    assert response.status_code == 200
    data = response.json()
    assert 'short_code' in data
    assert 'short_url' in data

def test_redirect_special_characters(client):
    special_url = 'https://example.com/?q=hello world&lang=en#section'
    shorten_response = client.post('/shorten', json={'url': special_url})
    short_code = shorten_response.json()['short_code']

    redirect_response = client.get(f'/get/{short_code}', follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers['location'] == 'https://example.com/?q=hello%20world&lang=en#section'

def test_shorten_duplicate_url(client):
    url = 'https://duplicate.com'
    first_response = client.post('/shorten', json={'url': url})
    second_response = client.post('/shorten', json={'url': url})

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert 'short_code' in first_data
    assert 'short_code' in second_data
    assert 'short_url' in first_data
    assert 'short_url' in second_data

    # Depending on implementation, the short codes may or may not be the same
    # Here we just check that both responses are valid
    assert first_data['short_code'] != ''
    assert second_data['short_code'] != ''

def test_redirect_case_sensitivity(client):
    url = 'https://caseSeNsitive.com'
    shorten_response = client.post('/shorten', json={'url': url})
    short_code = shorten_response.json()['short_code']

    # Test with original case
    redirect_response = client.get(f'/get/{short_code}', follow_redirects=False)
    assert redirect_response.status_code == 302
    assert redirect_response.headers['location'] == url

    # Test with different case
    altered_code = short_code.upper() if short_code.islower() else short_code.lower()
    redirect_response_case = client.get(f'/get/{altered_code}', follow_redirects=False)
    assert redirect_response_case.status_code == 404

def test_shorten_invalid_url_format(client):
    response = client.post('/shorten', json={'url': 'ht!tp://invalid-url'})
    assert response.status_code == 200  # Assuming the app does not validate URL format
    data = response.json()
    assert 'short_code' in data
    assert 'short_url' in data