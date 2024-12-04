from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import threading
from dotenv import load_dotenv
import requests
import os
import random

class Authorize:
    def __init__(self, localhost_port: int = 3000):
        load_dotenv()
        # get the client id and client secret from the environment, raise an error if not found
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")
        self.localhost_port = localhost_port
        if not self.client_id or not self.client_secret:
            raise ValueError("Please set CLIENT_ID and CLIENT_SECRET in .env file")

    def authorize(self, scope: str) -> dict:
        endpoint = "https://accounts.spotify.com/authorize?"
        # get random number for state parameter
        state = random.randint(1000000000, 9999999999)
        response_type = "code"
        redirect_uri = f"http://localhost:{self.localhost_port}"
        endpoint += f"client_id={self.client_id}&response_type={response_type}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
        
        # start a local server to listen for the redirect in a background thread
        server_thread = threading.Thread(target=self._listen_on_port, args=(self.localhost_port,))
        server_thread.start()
        
        response = requests.get(url=endpoint)
        response.raise_for_status()

        print("Visit the url to login:")
        print(response.url)

        # Wait for the server thread to finish
        server_thread.join()

        # check if the state parameter matches
        if self.auth_redirect_params["state"][0] != str(state):
            raise ValueError("State parameter does not match")

        # get the authorization code from the query parameters
        authorization_code = self.auth_redirect_params["code"][0]
        print(f"Authorization code: {authorization_code}")

        return authorization_code


    def _listen_on_port(self, port: int):
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query parameters
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes(f"Received query parameters: {query_params}", "utf-8"))
                # Save the query parameters to the server instance
                self.server.query_params = query_params
                # Shutdown the server after receiving the request
                threading.Timer(1, self.server.shutdown).start()

        server = HTTPServer(('localhost', port), RequestHandler)
        server.serve_forever()
        self.auth_redirect_params = server.query_params