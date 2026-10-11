import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        message="Hello from the ServiceNow-integrated CI/CD pipeline",
        host=socket.gethostname(),
        version=os.getenv("APP_VERSION", "1.0"),
    )


@app.route("/health")
def health():
    return jsonify(status="ok")
