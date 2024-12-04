import pytest

from spotify_playlist_toolbox.authorize import Authorize

def test_authorize():
    auth_client = Authorize()
    # TODO: make it a unit test;
    # mock request to spotify and do a get call to the localhost:3000 to mock response redirecting there
    result = auth_client.authorize(scope="playlist-modify-private playlist-modify-public")
    assert "code" in result