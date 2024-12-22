import base64
import os
from typing import List
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from enum import Enum

class GrantType(Enum):
    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"


class SpotifyAPIClient:
    def __init__(self, redirect_uri_localhost_port: int = 3000):
        load_dotenv()
        # get the client id and client secret from the environment, raise an error if not found
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.auth_code = os.getenv("AUTH_CODE")
        if not self.client_id or not self.client_secret:
            raise ValueError("Please set CLIENT_ID and CLIENT_SECRET environment variables")
        if self.auth_code:
            print("AUTH_CODE env variable found, using it for authenticating requests")
            print("Note: The authorization code is valid for max. 10 minutes and can only be used once.")
            print("If the code is expired, do authorization again for the fresh code.")
            self.grant_type = GrantType.AUTHORIZATION_CODE
        else:
            print("AUTH_CODE env variable not found, defaulting to client credentials flow (no private data access)")
            self.grant_type = GrantType.CLIENT_CREDENTIALS

        self._token = None
        self._token_expires_at = None
        self.redirect_uri_localhost_port = redirect_uri_localhost_port
        self._refresh_token = None
        self._scope = None

    def _prepare_token(self):
        # if token is already present, and it's not about to expire in 5 minutes, return
        if self._token and self._token_expires_at > datetime.now() + timedelta(seconds=300):
            return
        
        # otherwise prepare to send a POST request to the Spotify Accounts service /api/token endpoint
        endpoint = "https://accounts.spotify.com/api/token"
        # base64 encode the client id and client secret
        client_credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(client_credentials.encode("utf-8")).decode("utf-8")
    
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }
        # case 1: client credentials grant type
        if self.grant_type == GrantType.CLIENT_CREDENTIALS:
            body = {
                "grant_type": self.grant_type.value,
            }
        # case 2: authorization code grant type, first time with this auth code
        elif self.grant_type == GrantType.AUTHORIZATION_CODE and not self._refresh_token:
            body = {
                "grant_type": self.grant_type.value,
                "code": self.auth_code,
                "redirect_uri": f"http://localhost:{self.redirect_uri_localhost_port}",
            }
        # case 3: authorization code grant type, refresh token
        elif self.grant_type == GrantType.AUTHORIZATION_CODE and self._refresh_token:
            body = {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            }

        # send a POST request
        response = requests.post(url=endpoint, headers=headers, data=body)
        if response.status_code != 200:
            print(response.json())
        
        response.raise_for_status()
        self._token_expires_at = datetime.now() + timedelta(seconds=3600)
        self._token = response.json()["access_token"]

        msg = f"New token obtained, expires at: {self._token_expires_at}"
        # for authorization code grant type, save the refresh token and scope
        if self.grant_type == GrantType.AUTHORIZATION_CODE:
            self._refresh_token = response.json()["refresh_token"]
            self._scope = response.json()["scope"]
            msg += f", scope: {self._scope}"
        print(msg)


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
    
    def add_items_to_playlist(self, playlist_id: str, uris: str | List[str], position: int = None) -> dict:
        self._prepare_token()
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        # if uris is a list, join them with a comma
        if isinstance(uris, list):
            uris = ",".join(uris)
        body = {
            "uris": uris,
            "position": position,
        }
        response = requests.post(url=endpoint, headers=headers, json=body)
        response.raise_for_status()
        return response.json()