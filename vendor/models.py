from django.db import models
from django.contrib.auth.models import User
from users.models import CustomerDetails

# Create your models here.


class Category(models.Model):
    category_name = models.CharField(max_length=200,null=True,blank=True)
    category_image = models.FileField(null=True,blank=False,upload_to='category/category_images')

    @property
    def ImageURL(self):
        try:
            url = self.category_image.url
        except:
            url = ''    
        return url


class Product(models.Model):
    product_name = models.CharField(max_length=200,null=True)
    image = models.FileField(null=True,blank=False,upload_to='product/product_images')
    price = models.FloatField(null=True,blank=True)
    stock = models.IntegerField(null=True,blank=True)
    category = models.ForeignKey(Category, null=True,on_delete=models.CASCADE)
    description = models.CharField(max_length=2500,null=True,blank=True)
    offer_price = models.FloatField(default=0,null=True,blank=True)
    offer_percentage = models.IntegerField(default=0,null=True,blank=True)


    def __str__(self):
        return str(self.product_name)

    @property
    def ImageURL(self):
        try:
            url = self.image.url
        except:
            url = ''    
        return url

class Product_Images(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True)
    extra_images = models.FileField(max_length=2555,upload_to='product/product_images')

    @property
    def ImageURL(self):
        try:
            url = self.extra_images.url
        except:
            url = ''    
        return url
    

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    date_ordered = models.DateField(auto_now_add=True)
    time_ordered = models.TimeField(auto_now_add=True)
    complete = models.BooleanField(default=False,null=True,blank=False)
    transaction_id = models.CharField(max_length=200,null=True)
    status = models.CharField(default='placed', max_length=200,null=True)
    grand_total = models.CharField(max_length=255,null=True,blank=True)
    discounted =  models.CharField(max_length=255,null=True,blank=True)
    user_cancelled = models.CharField(default='NO',max_length=255,null=True,blank=True)
    refund_status = models.BooleanField(default=False,null=True,blank=True)
    refund_status_value = models.CharField(default='waiting for aprooval',null=True,blank=True,max_length=200)

    
    def get_cart_total(self,discount=0):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        profit = total * discount / 100 
        discounted_price =  total - profit
        if discount == 0 :
            return total
        else:
            return discounted_price

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True,null=True)
    quantity = models.IntegerField(default=0,null=True,blank=True)
    date_added = models.DateField(auto_now_add=True)
    time_added = models.TimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

class WishList(models.Model):
    customer = models.ForeignKey(User,blank=True,null=True,on_delete=models.SET_NULL)
    product = models.ForeignKey(Product,blank=True,null=True,on_delete=models.SET_NULL)
    

class ShippingAddress(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL,blank=True,null=True)
    address = models.CharField(max_length=200,null=True)
    city = models.CharField(max_length=200,null=True)
    state = models.CharField(max_length=200,null=True)
    country = models.CharField(max_length=200,null=True)
    mobilenumber = models.CharField(max_length=15,null=True,blank=True)
    zipcode = models.CharField(max_length=200,null=True)
    date_added = models.DateField(auto_now_add=True)
    time_added = models.TimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=200,null=True)

    def __str__(self):
        return self.address


class Offer(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,null=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,null=True)
    offer_name = models.CharField(max_length=20,null=True,blank=True)
    offer_image = models.FileField(max_length=255,null=True,blank=True,upload_to='offers/offer_images')
    offer_start = models.DateField(null=True)
    offer_expiry = models.DateField(null=True)
    discount_amount = models.FloatField(null=True)
    offer_type = models.CharField(null=True,blank=True,max_length=40)
    offer_status = models.CharField(default='Valid',blank=True,max_length=40)

    @property
    def ImageURL(self):
        try:
            url = self.offer_image.url
        except:
            url = ''
        return url

class Coupens(models.Model):
    coupen_name = models.CharField(max_length=255,null=True,blank=True)
    coupen_code = models.CharField(max_length=20,null=True,blank=True)
    validity_starts = models.DateField(null=True)
    validity_expire = models.DateField(null=True)
    coupen_status = models.BooleanField(default=False)
    discount_amount = models.FloatField(null=True)
    
class Wallet(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL,blank=True,null=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL,null=True,blank=True)
    transaction_name = models.CharField(max_length=200,null=True,blank=True)
    trasaction_type = models.CharField(max_length=200,null=True,blank=True)
    transaction_id = models.CharField(max_length=200,null=True)
    debit_amount = models.FloatField(default=0,null=True)
    credit_amount = models.FloatField(default=0,null=True)
    net_amount = models.FloatField(default=0,null=True)
    cashback_amount = models.FloatField(default=0,null=True)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'time'