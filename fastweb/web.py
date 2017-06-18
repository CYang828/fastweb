# coding:utf8

"""网络层模块"""

import json
import shlex
import urllib
import traceback
import subprocess


from fastweb.accesspoint import (web, coroutine, Task, Return, options,
                                 AsyncHTTPClient, HTTPError, Subprocess, httpserver, ioloop, HTTPRequest, run_on_executor)

import fastweb.components
from fastweb.util.tool import timing
from fastweb.util.log import recorder
from fastweb.util.thread import FThread
from fastweb.util.python import to_plain
from fastweb.exception import HttpError, SubProcessError


__all__ = ['Api', 'Page', 'Request', 'options', 'arguments', 'start_web_server']


class Request(HTTPRequest):

    def __init__(self, url, method="GET", headers=None, body=None,
                 auth_username=None, auth_password=None, auth_mode=None,
                 connect_timeout=None, request_timeout=None,
                 if_modified_since=None, follow_redirects=None,
                 max_redirects=None, user_agent=None, use_gzip=None,
                 network_interface=None, streaming_callback=None,
                 header_callback=None, prepare_curl_callback=None,
                 proxy_host=None, proxy_port=None, proxy_username=None,
                 proxy_password=None, allow_nonstandard_methods=None,
                 validate_cert=None, ca_certs=None,
                 allow_ipv6=None,
                 client_key=None, client_cert=None, body_producer=None,
                 expect_100_continue=False, decompress_response=None,
                 ssl_options=None, params=None):
        if params:
            url = '{url}?{params}'.format(url, urllib.urlencode(params))
        if body:
            body = urllib.urlencode(body)
        super(Request, self).__init__(url, method=method, headers=headers, body=body,
                                      auth_username=auth_username, auth_password=auth_password, auth_mode=auth_mode,
                                      connect_timeout=connect_timeout, request_timeout=request_timeout,
                                      if_modified_since=if_modified_since, follow_redirects=follow_redirects,
                                      max_redirects=max_redirects, user_agent=user_agent, use_gzip=use_gzip,
                                      network_interface=network_interface, streaming_callback=streaming_callback,
                                      header_callback=header_callback, prepare_curl_callback=prepare_curl_callback,
                                      proxy_host=proxy_host, proxy_port=proxy_port, proxy_username=proxy_username,
                                      proxy_password=proxy_password, allow_nonstandard_methods=allow_nonstandard_methods,
                                      validate_cert=validate_cert, ca_certs=ca_certs,
                                      allow_ipv6=allow_ipv6,
                                      client_key=client_key, client_cert=client_cert, body_producer=body_producer,
                                      expect_100_continue=expect_100_continue, decompress_response=decompress_response,
                                      ssl_options=ssl_options)

    def __str__(self):
        return '<Request {method} {url} {body}>'.format(method=self.method, url=self.url, body=self.body)


class AsynComponents(fastweb.components.Components):
    """异步组件类"""

    @coroutine
    def http_request(self, request):
        """http请求

        :parameter:
          - `request`:http请求
        """

        self.recorder(
            'INFO', 'http request start\n{request}'.format(request=request))

        with timing('ms', 10) as t:
            try:
                response = yield AsyncHTTPClient().fetch(request)
            except HTTPError as ex:
                self.recorder('ERROR', 'http request error {request} ({e})'.format(
                    request=request, e=ex))
                raise HttpError

        self.recorder('INFO', 'http request successful\t({response} <{time}>)'.format(
            response=response.code, time=t))
        raise Return(response)

    @coroutine
    def call_subprocess(self, command, stdin_data=None, stdin_async=True):
        """命令行调用

        :parameter:
          - `command`:命令行
          - `stdin_data`:传入数据
        """

        # TODO:待优化
        self.recorder(
            'INFO', 'call subprocess start <{cmd}>'.format(cmd=command))

        with timing('ms', 10) as t:
            stdin = Subprocess.STREAM if stdin_async else subprocess.PIPE
            sub_process = Subprocess(shlex.split(command),
                                     stdin=stdin,
                                     stdout=Subprocess.STREAM,
                                     stderr=Subprocess.STREAM)
            try:
                if stdin_data:
                    if stdin_async:
                        yield Task(sub_process.stdin.write, stdin_data)
                    else:
                        sub_process.stdin.write(stdin_data)

                if stdin_async or stdin_data:
                    sub_process.stdin.close()

                result, error = yield [Task(sub_process.stdout.read_until_close),
                                       Task(sub_process.stderr.read_until_close)]
            except (OSError, ValueError) as ex:
                self.recorder('ERROR', 'call subprocess <{cmd} <{time}> {e} {msg}'.format(
                    cmd=command, time=t, e=ex, msg=result.strip() if result else error.strip()))
                raise SubProcessError

        if sub_process.returncode != 0:
            self.recorder('ERROR', 'call subprocess <{cmd}> <{time}> {msg}'.format(
                cmd=command, time=t, msg=result.strip() if result else error.strip()))
            raise SubProcessError

        self.recorder('INFO', 'call subprocess <{cmd}> <{time} {msg}>'.format(
            cmd=command, time=t, msg=result.strip() if result else error.strip()))
        raise Return((result, error))

    def call_celery(self, *args, **kwargs):
        pass


class Api(web.RequestHandler, AsynComponents):
    """Api操作基类"""

    def __init__(self, application, request, **kwargs):
        super(Api, self).__init__(application, request, **kwargs)

        self.uri = request.uri
        self.host = request.host
        self.remoteip = request.remote_ip
        self.arguments = self.request.arguments
        self.requestid = self.get_argument('requestid') if self.get_argument('requestid', None) else self.gen_requestid()

        # TODO: 远程ip获取不准确
        self.recorder(
            'IMPORTANT',
            'Api request\nIp:<{ip}>\nHost:<{host}{uri}\nArguments:<{arguments}>\nUserAgent:<{ua}>'.format(
                ip=self.remoteip,
                host=self.host,
                uri=self.uri,
                arguments=self.request.body,
                ua=self.request.headers['User-Agent']))
        self.set_header_json()

    def data_received(self, chunk):
        pass

    def log_exception(self, typ, value, tb):
        """日志记录异常,并自动返回系统错误"""

        self.recorder('ERROR', '{message}'.format(
            message=traceback.format_exc()))
        self.end('SVR')

    def set_ajax_cors(self, allow_ip):
        """设置CORS"""

        header = 'Access-Control-Allow-Origin'
        self.set_header(header, allow_ip)
        self.recorder('INFO', 'set header <{key}:{ip}>'.format(
            key=header, ip=allow_ip))

    def set_header_json(self):
        """设置返回格式为json"""

        header = 'Content-type'
        self.add_header(header, 'text/json')
        self.recorder('INFO', 'set header <{key}:{type}>'.format(
            key=header, type='text/json'))

    def end(self, code='SUC', log=True, **kwargs):
        """请求结束"""

        ret = self.errcode[code]
        ret = dict(ret, **kwargs)
        self.write(json.dumps(ret))
        self.finish()
        self.release()
        t = (self.request._finish_time-self.request._start_time) * 1000

        if log:
            self.recorder(
                'IMPORTANT',
                'Api response\nResponse:<{ret}>\nTime:<{time}ms>'.format(
                    ret=ret, time=t))
        else:
            self.recorder(
                'IMPORTANT',
                'Api response\nTime:<{time}ms>'.format(time=t))


class Page(web.RequestHandler, AsynComponents):
    """Page操作基类"""

    def __init__(self, application, request, **kwargs):
        super(Page, self).__init__(application, request, **kwargs)

        self.uri = request.uri
        self.host = request.host
        self.remoteip = request.remote_ip
        self.arguments = self.request.arguments
        self.requestid = self.get_argument('requestid') if self.get_argument('requestid', None) else self.gen_requestid()

        self.recorder(
            'IMPORTANT',
            'Page request\nIp:<{ip}>\nHost:<{host}{uri}\nArguments:<{arguments}>\nUserAgent:<{ua}>'.format(
                ip=self.remoteip,
                host=self.host,
                uri=self.uri,
                arguments=self.request.body,
                ua=self.request.headers['User-Agent']))

    def data_received(self, chunk):
        pass

    def log_exception(self, typ, value, tb):
        """日志记录异常"""

        self.recorder('error', '{message}'.format(
            message=traceback.format_exc()))

    def end(self, template=None, log=True, **kwargs):
        """ 请求结束"""

        if template:
            # TODO:模版位置的正确性
            self.render(template, **kwargs)

        self.release()
        t = (self.request._finish_time - self.request._start_time) * 1000

        if log:
            self.recorder(
                'IMPORTANT',
                'Page response\nTemplate:{tem}\nTemArgs:{args}\nTime:<{time}ms>'.format(
                    tem=template, args=kwargs, time=t))
        else:
            self.recorder(
                'IMPORTANT',
                'Page response\nTemplate:{tem}\nTime:<{time}ms>'.format(
                    tem=template, time=t))


def arguments(convert=None, **ckargs):
    """检查并转换请求参数是否合法并转换参数类型

    :parameter:
      - `convert`:待转换的key,但非必要参数
      - `**ckargs`:必要参数
    """

    def _deco(fn):
        def _wrap(cls, *args, **kwargs):
            if convert:
                for cname, ctype in convert.items():
                    cvalue = cls.request.arguments.get(cname)
                    cvalue = to_plain(cvalue)
                    if cvalue:
                        cls.request.arguments[cname] = ctype(cvalue)

            for cname, ctype in ckargs.items():
                cvalue = cls.request.arguments.get(cname)
                cvalue = to_plain(cvalue)

                def invalid_recorder(msg):
                    diff = set(cls.request.arguments.keys()).symmetric_difference(set(ckargs.keys()))
                    cls.recorder('error', 'check arguments invalid <{diff}> {msg}'.format(
                        msg=msg, diff=to_plain(diff)))
                    cls.end('SVR')

                if cvalue:
                    if ctype is int:
                        if not cvalue.isdigit():
                            invalid_recorder('argument type error')
                            return
                    elif not isinstance(cvalue, ctype):
                        invalid_recorder('argument type error')
                        return
                else:
                    if isinstance(cls, Api):
                        invalid_recorder('argument empty')
                        return
                    elif isinstance(cls, Page):
                        invalid_recorder('argument empty')
                        return
                cls.request.arguments[cname] = ctype(cvalue)
            return fn(cls, *args, **kwargs)
        return _wrap
    return _deco


def start_web_server(port, handlers, **settings):
    """启动服务器"""

    application = web.Application(
        handlers,
        **settings
    )

    http_server = httpserver.HTTPServer(
        application, xheaders=settings.get('xheaders'))
    http_server.listen(port)
    recorder('INFO', 'server start on {port}'.format(port=port))
    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        ioloop.IOLoop.current().stop()
        FThread.stop(0)
        recorder('INFO', 'server stop on {port}'.format(port=port))


def set_error_handler():
    # TODO:设置错误的句柄
    pass


