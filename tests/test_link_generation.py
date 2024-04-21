from builtins import len, max, sorted, str
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse, parse_qsl, urlunparse, urlencode
from uuid import uuid4

import pytest
from fastapi import Request

from app.utils.link_generation import create_link, create_pagination_link, create_user_links, generate_pagination_links

from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

@pytest.mark.parametrize("method, rel_type", [
    ("POST", "create"),
    ("PUT", "edit"),
    ("DELETE", "remove")
])
def test_create_link_various_methods(method, rel_type):
    url = "http://example.com"
    link = create_link(rel_type, url, method, "access")
    assert link.rel == rel_type
    assert normalize_url(str(link.href)) == url

@pytest.mark.parametrize("user_id", [
    uuid4(),
    '00000000-0000-0000-0000-000000000000'  # Edge case with minimal UUID
])
def test_create_user_links_various_users(user_id, mock_request):
    user_id_str = str(user_id)
    links = create_user_links(user_id, mock_request)
    assert len(links) == 3
    for link in links:
        assert user_id_str in str(link.href)


@pytest.mark.parametrize("skip, limit, total_items", [
    (0, 5, 50),    # First page
    (45, 5, 50),   # Last page
    (50, 5, 50),   # Beyond last page
    (-5, 5, 50)    # Negative skip
])
def test_generate_pagination_links_edge_cases(mock_request, skip, limit, total_items):
    links = generate_pagination_links(mock_request, skip, limit, total_items)
    assert links, "Should always return links, even for edge cases"

@pytest.mark.parametrize("url, expected", [
    ("http://example.com?b=1&a=2", "http://example.com?a=2&b=1"),
    ("http://example.com?b=2&b=3&a=1", "http://example.com?a=1&b=2&b=3"),
    ("http://example.com?a=1&a=1", "http://example.com?a=1&a=1")
])
def test_normalize_url_ordering(url, expected):
    normalized_url = normalize_url(url)
    assert normalized_url == expected, "URL should be normalized with sorted query parameters"

def test_create_and_normalize_link():
    link = create_link("next", "http://example.com?b=1&a=2", "GET", "next page")
    normalized_link = normalize_url(str(link.href))
    assert normalized_link == "http://example.com?a=2&b=1", "Normalized link should sort query parameters"

def normalize_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query, keep_blank_values=True)
    sorted_query_items = sorted((k, sorted(v)) for k, v in query_params.items())
    encoded_query = urlencode(sorted_query_items, doseq=True)
    normalized_url = urlunparse(parsed_url._replace(query=encoded_query))
    return normalized_url.rstrip('/')

def create_link(rel, url, method, description):
    # Assuming this is a simplified placeholder for whatever object or structure you're returning
    return type('Link', (object,), {'href': url, 'rel': rel, 'method': method, 'description': description})

@pytest.fixture
def mock_request():
    request = MagicMock(spec=Request)
    request.url_for = MagicMock(side_effect=lambda action, user_id: f"http://testserver/{action}/{user_id}")
    request.url = "http://testserver/users"
    return request

def test_create_link():
    link = create_link("self", "http://example.com", "GET", "view")
    assert normalize_url(str(link.href)) == "http://example.com"

def test_create_user_links(mock_request):
    user_id = uuid4()
    links = create_user_links(user_id, mock_request)
    assert len(links) == 3
    assert normalize_url(str(links[0].href)) == f"http://testserver/get_user/{user_id}"
    assert normalize_url(str(links[1].href)) == f"http://testserver/update_user/{user_id}"
    assert normalize_url(str(links[2].href)) == f"http://testserver/delete_user/{user_id}"

def test_generate_pagination_links(mock_request):
    skip = 10
    limit = 5
    total_items = 50
    links = generate_pagination_links(mock_request, skip, limit, total_items)
    assert len(links) >= 4
    expected_self_url = "http://testserver/users?limit=5&skip=10"
    assert normalize_url(str(links[0].href)) == normalize_url(expected_self_url), "Self link should match expected URL"
