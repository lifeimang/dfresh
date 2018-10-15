from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View

from goods.models import GoodsSKU

from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin
# Create your views here.


# 前端需要传递的参数: 商品id(sku_id) 商品数量(count)
# 采用ajax post请求
# /cart/add
class CartAddView(View):
    """购物车记录-添加"""
    def post(self, request):
        """添加"""
        # 获取登录用户
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 参数校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品id
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 校验商品的数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 3, 'errmsg': '商品数目非法'})

        if count <= 0:
            return JsonResponse({'res': 3, 'errmsg': '商品数目非法'})

        # 业务处理：添加购物车记录
        # cart_2 : {'1':5, '3':2, '4':3}
        # 如果用户的购物车中已经添加过该商品，数目需要累加
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d'%user.id

        # hget(key, field): 如果field存在，返回field的值，否则返回None
        cart_count = conn.hget(cart_key, sku_id)

        if cart_count:
            # 数目累加
            count += int(cart_count)

        # 判断商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 设置购物车中商品的数目
        # hset(key, field, value): 如果field存在则更新值，如果不存在则添加新属性
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车中商品的条目数
        cart_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'message': '添加成功'})


# /cart/
class CartInfoView(LoginRequiredMixin, View):
    """购物车页面显示"""
    def get(self, request):
        """显示"""
        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        user = request.user
        cart_key = 'cart_%d'%user.id

        # 从redis中获取用户购物车商品的记录
        # cart_用户id : {'商品id': '商品数量'}
        # hgetall(key): 返回一个字典: {'商品id': '商品数量'}
        cart_dict = conn.hgetall(cart_key)

        skus = []
        total_count = 0
        total_amount = 0
        # 获取对应商品的信息
        for sku_id, count in cart_dict.items():
            # 根据sku_id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 计算商品的小计
            amount = sku.price*int(count)

            # 给sku对象增加属性amount和count
            # 分别保存用户购物车中添加商品的小计和商品的数目
            sku.amount = amount
            sku.count = int(count)

            # 追加商品
            skus.append(sku)

            # 累加计算用户购物车中商品的总件数和总价格
            total_count += int(count)
            total_amount += amount

        # 组织上下文
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_amount': total_amount}

        # 使用模板
        return render(request, 'cart.html', context)


# 前端传递的参数: 商品id(sku_id) 更新数量(count)
# 采用ajax post请求
# /cart/update
class CartUpdateView(View):
    """购物车记录更新"""
    def post(self, request):
        """更新"""
        # 获取登录用户
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 参数校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品id
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 校验商品的数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 3, 'errmsg': '商品数目非法'})

        if count <= 0:
            return JsonResponse({'res': 3, 'errmsg': '商品数目非法'})

        # 业务处理：购物车记录更新
        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d'%user.id

        # 判断商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新redis中对应的购物车记录的商品数目
        # hset(key, field, value)
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车记录中商品的总件数
        # hvals(key): 返回hash中所有属性的值，返回的是列表
        cart_vals = conn.hvals(cart_key)
        cart_count = 0
        for val in cart_vals:
            cart_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'message': '更新成功'})


# 前端传递的参数: 商品id(sku_id)
# 采用ajax post请求
# /cart/delete
class CartDeleteView(View):
    """购物车记录-删除"""
    def post(self, request):
        """删除"""
        # 获取登录用户
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 校验参数
        if not all([sku_id]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品id
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 业务处理: 购物车记录删除
        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d'%user.id

        # 删除redis对应的记录
        # hdel(key, *args): 删除hash中对应属性和它的值
        conn.hdel(cart_key, sku_id)

        # 获取用户购物车记录中商品的总件数
        # hvals(key): 返回hash中所有属性的值，返回的是列表
        cart_vals = conn.hvals(cart_key)
        cart_count = 0
        for val in cart_vals:
            cart_count += int(val)

        # 返回应答
        return JsonResponse({'res': 3, 'cart_count': cart_count, 'message': '删除成功'})











