#!/usr/bin/env python
from flask import Flask, abort, request
from uuid import uuid4
import requests
import requests.auth
import urllib

CLIENT_ID = "fOnhARgm9Kn22PNFSQlNhrlpw6goofqIPYNKmPDl"
CLIENT_SECRET = "L7l7sNvBVA4aes1TNee8efzaLEUjPE1BDbN7s6MFm2w0NlxEz5gizAF0tlgb9z17Y8oM6Yh5lwh3UArbCdpQSRaSYOpwlijyqVLM6zlY9fkgLvqlpFP7kzEooWUDPQxR"
REDIRECT_URI = "http://127.0.0.1:3000/reddit_callback"


def base_headers():
    return {"User-Agent": "Someone"}


app = Flask(__name__)


@app.route("/")
def homepage():
    text = '<a href="%s">Authenticate with reddit</a>'
    return text % make_authorization_url()


def make_authorization_url():
    # Generate a random string for the state parameter
    # Save it for use later to prevent xsrf attacks
    state = str(uuid4())
    save_created_state(state)
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "state": state,
        "redirect_uri": REDIRECT_URI,
        "duration": 360000,
        "scope": "userinfo-v1",
    }
    url = "http://127.0.0.1:8000/o/authorize/?" + urllib.parse.urlencode(params)
    return url


# Left as an exercise to the reader.
# You may want to store valid states in a database or memcache.
def save_created_state(state):
    pass


def is_valid_state(state):
    return True


@app.route("/reddit_callback")
def reddit_callback():
    error = request.args.get("error", "")
    if error:
        return "Error: " + error
    state = request.args.get("state", "")
    if not is_valid_state(state):
        # Uh-oh, this request wasn't started by us!
        abort(403)
    code = request.args.get("code")
    access_token = get_token(code)
    # Note: In most cases, you'll want to store the access token, in, say,
    # a session for use in other parts of your web app.
    return "Your reddit username is: %s" % get_username(access_token)


def get_token(code):
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = base_headers()
    response = requests.post(
        "http://127.0.0.1:8000/o/token/",
        auth=client_auth,
        headers=headers,
        data=post_data,
    )
    token_json = response.json()
    return token_json["access_token"]


def get_username(access_token):
    headers = base_headers()
    headers.update({"Authorization": "Bearer " + access_token})
    response = requests.get("http://127.0.0.1:8000/api/v1/userinfo/", headers=headers)
    me_json = response.json()
    return me_json["name"]


if __name__ == "__main__":
    app.run(debug=True, port=3000)
