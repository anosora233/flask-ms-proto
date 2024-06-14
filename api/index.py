from flask import Flask, render_template

from .tools import query_proto

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('content.j2', proto=query_proto())
