import base64
import os
from typing import List
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta



class SpotifyAPIClient:
    def __init__(self):
        load_dotenv()
        # get the client id and client secret from the environment, raise an error if not found
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise ValueError("Please set CLIENT_ID and CLIENT_SECRET in .env file")
        self._token = None
        self._token_expires_at = None

    def _prepare_token(self):
        if not self._token:
            self._get_new_token()
        # if the token is about to expire in the next 10 minutes, get a new token
        elif self._token_expires_at < datetime.now() + timedelta(seconds=600):
            self._get_new_token()

    def _get_new_token(self):
        # send a POST request to the Spotify Accounts service /api/token endpoint
        endpoint = "https://accounts.spotify.com/api/token"
        # base64 encode the client id and client secret
        client_credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(client_credentials.encode("utf-8")).decode("utf-8")
    
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }
        # grant_type = "client_credentials"
        grant_type = "authorization_code"
        body = {
            "grant_type": grant_type,
        }
        response = requests.post(url=endpoint, headers=headers, data=body)
        response.raise_for_status()
        self._token_expires_at = datetime.now() + timedelta(seconds=3600)
        self._token = response.json()["access_token"]
    
    def get_playlist(self, playlist_id: str, market: str = None, fields: str = None) -> dict:
        self._prepare_token()
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        # get request parameters that are not None
        request_params = ["market", "fields"]
        local_vars_dict = locals()
        request_params_dict = {param: local_vars_dict[param] for param in request_params if local_vars_dict[param] is not None}
        if len(request_params_dict) > 0:
            endpoint += "?" + "&".join([f"{key}={value}" for key, value in request_params_dict.items()])
            
        headers = {
            "Authorization": f"Bearer {self._token}",
        }
        response = requests.get(url=endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_playlist_items(self, playlist_id: str, market: str = None, fields: str = None, limit: int = None, offset: int = None) -> list:
        self._prepare_token()
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        # get request parameters that are not None
        request_params = ["market", "fields", "limit", "offset"]
        local_vars_dict = locals()
        request_params_dict = {param: local_vars_dict[param] for param in request_params if local_vars_dict[param] is not None}
        if len(request_params_dict) > 0:
            endpoint += "?" + "&".join([f"{key}={value}" for key, value in request_params_dict.items()])

        headers = {
            "Authorization": f"Bearer {self._token}",
        }
        response = requests.get(url=endpoint, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def create_playlist(self, user_id: str, name: str, description: str = None, public: bool = True, collaborative: bool = False) -> dict:
        if collaborative and public:
            raise ValueError("A collaborative playlist cannot be public")
        self._prepare_token()
        endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        body = {
            "name": name,
            "description": description,
            "public": public,
            "collaborative": collaborative,
        }
        response = requests.post(url=endpoint, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    
    def add_items_to_playlist(self, playlist_id: str, uris: List[str], position: int = None) -> dict:
        self._prepare_token()
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        body = {
            "uris": uris,
            "position": position,
        }