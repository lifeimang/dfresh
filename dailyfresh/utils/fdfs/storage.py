from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

import os

# 通过后台管理页面上传文件时，Django框架会调用
# 文件存储类中的save方法，save方法的内部调用_save,
# _save方法的返回值最终会被保存在表的image字段中。

# Django保存文件之前，会先调用文件存储类中的
# exists判断文件是否已存在。


class FDFSStorage(Storage):
    """FDFS文件系统存储类"""
    def __init__(self, client_conf=None, nginx_url=None):
        """初始化"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if nginx_url is None:
            nginx_url = settings.FDFS_NGINX_URL
        self.nginx_url = nginx_url

    def _save(self, name, content):
        """保存文件时调用"""
        # name: 选择上传文件的名称
        # content: 是一个File类的实例对象，包含上传文件的内容

        # 创建Fdfs_client类的对象
        client = Fdfs_client(self.client_conf)

        # 获取上传文件的内容
        content = content.read()

        # 上传文件到FDFS文件存储服务器
        # upload_by_buffer：根据文件的内容将文件上传到FDFS系统
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id, # 文件ID
        #     'Status': 'Upload successed.',
        #     'Local file name': '',
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None

        response = client.upload_by_buffer(content)

        if response is None or response.get('Status') != 'Upload successed.':
            # 上传失败，抛出异常
            raise Exception("上传文件到FDFS系统失败")

        # 获取文件ID
        file_id = response.get('Remote file_id')

        # 返回文件ID
        return file_id

    def exists(self, name):
        """判断文件在存储系统中是否存在"""
        return False

    def url(self, name):
        """返回可访问文件的url路径"""
        return self.nginx_url + name
