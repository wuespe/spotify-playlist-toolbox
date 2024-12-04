import pytest

from spotify_playlist_toolbox.api_client import SpotifyAPIClient


def test_get_token():
    api_client = SpotifyAPIClient()
    token = api_client._get_new_token()
    assert token is not None


def test_get_playlist():
    api_client = SpotifyAPIClient()
    playlist = api_client.get_playlist("3cEYpjA9oz9GiPac4AsH4n")
    assert playlist["name"] == "Progressive Psy Trance Picks Vol.8"


def test_get_playlist_items():
    api_client = SpotifyAPIClient()
    playlist_items = api_client.get_playlist_items("3cEYpjA9oz9GiPac4AsH4n", fields="items(track(name, artists(name)))", limit=5)
    assert len(playlist_items.items) == 5

def test_create_playlist():
    api_client = SpotifyAPIClient()
    playlist = api_client.create_playlist("21ezbtsr3punwa643bniqbshy", "Test Playlist", description="This is a test playlist", public=False)
    