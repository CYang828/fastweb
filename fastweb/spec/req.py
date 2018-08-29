# coding:utf8

from fastweb.compat import unquote
from fastweb.accesspoint import requests


class HttpClient(object):
    """同步的http访问客户端"""

    @staticmethod
    def fetch(request):
        method = request.method.lower()
        url = request.url

        if method == 'get':
            response = requests.get(url)
        elif method == 'post':
            if request.json:
                response = requests.post(url, json=request.json, headers={'Content-Type':'application/json'})
            elif request.body:
                data = unquote(request.body.decode())
                response = requests.post(url, data=data)

        return response
