from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel
# Create your models here.


# 使用django默认的认证系统
# python manage.py createsuperuser->auth_user->User模型类
class User(AbstractUser, BaseModel):
    """用户模型类"""

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

# 模型类.objects: objects(类型: models.Manager)是django框架给每一个模型类生成一个模型管理器类的对象

# 自定义模型管理器类:
# 1. 定义一个类，继承models.Manager
# 2. 在对应模型类中创建一个自定义模型管理器类的对象


class AddressManager(models.Manager):
    """地址模型管理器类"""
    # 使用场景
    # 1. 改变原有查询的结果集
    def all(self):
        # 先调用父类的all获取所有数据
        res = super(AddressManager, self).all() # QuerySet

        # 对数据进行过滤
        res = res.filter(is_delete=False)

        # 返回
        return res

    # 2. 封装方法: 用于操作模型类对应的数据表(增，删，改，查)
    def get_default_address(self, user):
        """查询user用户的默认收货地址"""
        # self.model: 获取self对象所在模型类
        try:
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            # 用户没有默认收货地址
            address = None

        # 返回address
        return address


# Address.objects.get_default_address()
class Address(BaseModel):
    """地址模型类"""
    user = models.ForeignKey('User', verbose_name='所属账户')
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    # 自定义模型管理器类的对象
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

