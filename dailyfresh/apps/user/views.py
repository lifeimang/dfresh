from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from celery_tasks.tasks import send_register_active_email
import re
# Create your views here.


# /user/register
def register_1(request):
    """注册"""
    return render(request, 'register.html')

# web开发视图处理通用的流程:
    # 1. 接收参数
    # 2. 参数校验（后端校验)
    # 3. 业务处理
    # 4. 返回应答


# /user/register_handle
def register_handle(request):
    """注册处理"""
    # 1. 接收参数
    username = request.POST.get('user_name') # None
    password = request.POST.get('pwd')
    email = request.POST.get('email')

    # 2. 参数校验（后端校验)
    # 校验数据的完整性
    if not all([username, password, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    # 校验用户名是否存在
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名不存在
        user = None

    if user:
        # 用户名已存在
        return render(request, 'register.html', {'errmsg': '用户名已存在'})

    # 3. 业务处理：用户注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    # 4. 返回应答：跳转的首页
    return redirect(reverse('goods:index'))


# 注册页面显示和注册处理使用同一url地址:/user/register, 根据请求方式作为区分
# /user/register
def register(request):
    """注册"""
    if request.method == 'GET':
        # 显示注册页面
        return render(request, 'register.html')
    elif request.method == 'POST':
        # 进行注册处理
        # 1. 接收参数
        username = request.POST.get('user_name') # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2. 参数校验（后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 3. 业务处理：用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 4. 返回应答：跳转的首页
        return redirect(reverse('goods:index'))


# 类视图: 访问一个url地址可以采用不同的请求方式，使用类视图就是根据不同的请求方式调用类中不同的方法
# /user/register
class RegisterView(View):
    """注册"""
    def get(self, request):
        """显示"""
        # print('get')
        return render(request, 'register.html')

    def post(self, request):
        """注册处理"""
        # print('post')
        # 1. 接收参数
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2. 参数校验（后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 3. 业务处理：用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 用户注册成功之后，需要给用户的注册邮箱发送激活邮件
        # 在激活邮件中需要包含激活的连接：/user/active/用户id
        # 坏处: 可能造成其他人恶意请求网站进行账户的激活
        # 解决: 对用户的身份信息进行加密，生成一个token，把token信息放在激活链接中
        # /user/active/token信息
        # itsdangerous

        # 生成激活的token信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        # 加密
        token = serializer.dumps(info) # bytes
        # 转换成字符串
        token = token.decode()

        # # 组织邮件的内容
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = """
        #             <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
        #             请点击以下链接激活您的账号<br/>
        #             <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
        #         """ % (username, token, token)
        #
        # # 发生激活邮件
        # # send_mail(subject='邮件标题', message='邮件正文', from_email='发件人', recipient_list='收件人邮箱列表')
        # import time
        # time.sleep(5)
        # send_mail(subject, message, sender, receiver, html_message=html_message)

        # 使用celery发出发送邮件的任务
        send_register_active_email.delay(email, username, token)

        # 4. 返回应答：跳转的首页
        return redirect(reverse('goods:index'))


# /user/active/token信息
class ActiveView(View):
    """激活"""
    def get(self, request, token):
        """激活处理"""
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 解密
            info = serializer.loads(token)

            # 获取待激活用户的id
            user_id = info['confirm']

            # 激活用户
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 返回应答：跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已失效
            # 实际开发：返回页面，显示激活链接已失效，让用户点击页面上的链接再发送一封激活邮件
            return HttpResponse("<h1>激活链接已失效</h1>")


# /user/login
class LoginView(View):
    """登录"""
    def get(self, request):
        """显示"""
        # 尝试从cookie中获取username
        if 'username' in request.COOKIES:
            # 获取username
            username = request.COOKIES['username']
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录验证"""
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 参数校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 业务处理：登录验证
        # 根据用户名和密码查找用户的信息
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 账户已激活
                # 记住用户的登录状态
                login(request, user)

                # 获取登录后跳转url
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                # print(next_url)

                # 返回应答：跳转到首页
                # HttpResponseRedirect类->HttpRespose类的子类
                response = redirect(next_url)

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 清除用户名
                    response.delete_cookie('username')

                # 返回应答：跳转到首页
                return response
            else:
                # 账户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# request对象有一个属性user：request.user
# 如果用户已登录，user是一个认证系统用户模型类的对象(User)
# 如果用户未登录，user是一个匿名用户类(AnonymousUser)的对象
# User和AnonymousUser类中都有一个方法is_authenticated
# User中的is_authenticated永远返回True
# AnonymousUser中的is_authenticated永远返回False
# 在模板文件中可以直接使用user对象


# /user/logout
class LogoutView(View):
    """注销"""
    def get(self, request):
        """注销登录"""
        # 清除用户的登录状态
        logout(request)

        # 返回应答：跳转到登录页面
        return redirect(reverse('user:login'))

from utils.mixin import LoginRequiredView
from utils.mixin import LoginRequiredMixin

# Django中login_required装饰器的使用方式
# 方式1: 在进行url配置时，手动调用login_required装饰器
# 方式2:
# 2.1 定义一个类LoginRequiredView, 继承View
# 2.2 重写as_view, 在重写的as_view方法中调用login_required实现登录验证
# 2.3 需要登录验证的类视图直接继承LoginRequiredView
# 方式3:
# 3.1 定义一个类LoginRequiredMixin, 继承object
# 3.2 定义as_view，先使用super调用as_view, 在调用login_required实现登录验证
# 3.3 需要登录验证的类视图先继承与LoginRequiredMixin, 再继承View


# /user/
# class UserInfoView(View):
# class UserInfoView(LoginRequiredView):
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        """显示"""
        # 获取用户默认地址
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # conn = StrictRedis(host='172.16.179.142', port=6379, db=13)

        from django_redis import get_redis_connection
        conn = get_redis_connection('default')

        # 拼接key
        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的5个商品的id
        sku_ids = conn.lrange(history_key, 0, 4) # 返回列表 [2, 3, 1, 4, 5]

        # 查询用户浏览的商品的信息
        # select * from df_goods_sku where id in (2,3,1,4,5);
        # skus = GoodsSKU.objects.filter(id__in=sku_ids)
        #
        # # 调整顺序
        # skus_li = []
        # for sku_id in sku_ids:
        #     for sku in skus:
        #         if sku.id == int(sku_id):
        #             skus_li.append(sku)

        skus = []
        for sku_id in sku_ids:
            # 根据sku_id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 追加
            skus.append(sku)

        # 组织模板上下文
        context = {'page': 'user',
                   'address': address,
                   'skus': skus}

        # 使用模板
        return render(request, 'user_center_info.html', context)


# /user/order/页码
# class UserOrderView(View):
# class UserOrderView(LoginRequiredView):
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request, page):
        """显示"""
        # 获取登录用户
        user = request.user

        # 获取用户的订单信息
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取每个订单的订单商品的信息
        for order in orders:
            # 查询order订单商品的信息
            order_skus = OrderGoods.objects.filter(order=order)

            # 遍历order_skus，计算订单中每个商品的小计
            for order_sku in order_skus:
                # 计算订单商品的小计
                amount = order_sku.count*order_sku.price

                # 给order_sku增加属性amount, 保存订单商品的小计
                order_sku.amount = amount

            # 计算订单实付款
            total_pay = order.total_price + order.transit_price
            order.total_pay = total_pay

            # 获取订单状态的名称
            status_name = OrderInfo.ORDER_STATUS[order.order_status]
            order.status_name = status_name

            # 给order增加属性order_skus, 保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        from django.core.paginator import Paginator
        paginator = Paginator(orders, 1)

        # 判断页码
        page = int(page)
        if page > paginator.num_pages:
            page = 1

        # 获取第page页内容, 得到Page对象
        order_page = paginator.page(page)

        # 如果分页之后页码过多，最多页面上显示5个页码(当前页前2页，当前页，当前页后2页)
        # 1. 分页之后总页数不足5页，显示所有页码
        # 2. 如果当前页是前3页，显示1-5页
        # 3. 如果当前页是后3页，显示后5页
        # 4. 其他情况，显示当前页前2页，当前页，当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address
# class AddressView(View):
# class AddressView(LoginRequiredView):
class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        """显示"""
        # 获取用户的默认收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 用户没有默认收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        # 组织模板上下文
        context = {'page': 'address',
                   'address': address}

        # 使用模板
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """地址添加"""
        # 接收参数
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 参数校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 业务处理: 添加收货地址
        # 如果用户有默认收货地址，新添加的地址作为非默认地址
        # 如果用户没有默认收货地址，新添加的地址作为默认地址

        # 判断用户是否有默认收货地址
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 用户没有默认收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        is_default = True
        if address:
            # 用户有默认收货地址
            is_default = False

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答: 刷新地址页面, 重定向是get请求
        return redirect(reverse('user:address'))




















