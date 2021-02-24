from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from users.models import CustomerDetails
from . models import *
import requests
import json
from django.core.files import File
from django.core.files.storage import FileSystemStorage
import base64
from django.core.files.base import ContentFile
from datetime import date
import datetime
import uuid
# Create your views here.

def admin_login(request):
    if request.user.is_authenticated:
        return redirect(admin_dashboard)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        recaptcha_response = request.POST.get('g-recaptcha-response')
        url = 'https://www.google.com/recaptcha/api/siteverify'
        cap_secret="6LdggOwZAAAAAIgOyrSNRpOYLISII4ADvG1_5ydO"
        cap_data = {"secret":cap_secret,"response":recaptcha_response}
        cap_server_response=requests.post(url=url,data=cap_data)
        cap_json=json.loads(cap_server_response.text)
        if cap_json['success']==False:
            messages.error(request,"Inavalid captcha try again")
            return redirect(admin_login)
        user = auth.authenticate(username=username,password=password)
        if user:
            auth.login(request,user)
            return redirect(admin_dashboard)
        else:
            messages.info(request,'invalid credentials') 
            return redirect(admin_login)
    else:
        return render(request, './vendor/AdminLogin.html')

def admin_logout(request):
    auth.logout(request)
    return redirect(admin_login)

def admin_dashboard(request):
    if request.user.is_authenticated:
        customers = User.objects.filter(is_superuser=False)
        products = Product.objects.all()
        orderitem = OrderItem.objects.all()
        length_user = len(customers)
        length_products = len(products)
        length_orderitem = len(orderitem)
        context = {'customers':customers,'length_user':length_user,'length_products':length_products,'length_orderitem':length_orderitem}
        return render(request, './vendor/AdminDashboard.html',context)
    else:
        return redirect(admin_login)

def manage_customers(request):
    if request.user.is_authenticated:
        customers = User.objects.filter(is_superuser=False)
        context = {'customers':customers}
        return render(request, './vendor/ManageCustomers.html',context)
    else:
        return redirect(admin_login)

def create_customer(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            first_name = request.POST['first_name']
            last_name = request.POST['last_name']
            email = request.POST['email']
            username = request.POST['username']
            mobile_number = request.POST['mobile_number']
            password = request.POST['password']
            verify_password = request.POST['verify_password']

            credentials = {"firstname":first_name,"lastname":last_name,"email":email,"username":username,'mobile_number':mobile_number}

            if password == verify_password:
                if User.objects.filter(username=username).exists():
                    messages.info(request, 'username taken',credentials)
                    return render(request, './vendor/CreateCustomer.html',credentials)
                elif User.objects.filter(email=email).exists():
                    messages.info(request, 'email taken',credentials)
                    return render(request, './vendor/CreateCustomer.html',credentials)
                elif CustomerDetails.objects.filter(mobile_number=mobile_number).exists():
                    messages.info(request, 'email taken',credentials)
                    return render(request, './vendor/CreateCustomer.html',credentials)
                else:
                    customer = User.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,password=password)
                    CustomerDetails.objects.create(user=customer,mobile_number=mobile_number)
                    messages.info(request,'User Created') 
                    return redirect(manage_customers)
            else:
                 messages.info(request,'Password Not Matching') 
                 return render(request, './vendor/CreateCustomer.html',credentials)
        else:
            return render(request, './vendor/CreateCustomer.html')
    else:
        return redirect(admin_login)

def view_customers(request,id):
    if request.user.is_authenticated:
        customers_data = User.objects.get(id=id)
        additional_customer_data = CustomerDetails.objects.get(user=customers_data)
        context = {'customers_data':customers_data,'additional_customer_data':additional_customer_data}
        return render(request, './vendor/Customer_View.html',context)
    else:
        return redirect(admin_login)

def update_customers(request,id):
    if request.user.is_authenticated:
        customers_data = User.objects.get(id=id)
        additional_customer_data = CustomerDetails.objects.get(user=customers_data)
        context = {'customers_data':customers_data,'additional_customer_data':additional_customer_data}

        if request.method == 'POST':
            customers_data.first_name = request.POST['first_name']
            customers_data.last_name = request.POST['last_name']
            customers_data.username = request.POST['username']
            customers_data.email = request.POST['email']
            additional_customer_data.mobile_number = request.POST['mobile_number']
            additional_customer_data.save()
            customers_data.save()
            return redirect(manage_customers)
        else:        
            return render(request, './vendor/UpdateCustomer.html',context)
    else:
        return redirect(admin_login)

def delete_customer(request,id):
    if request.user.is_authenticated:
        customer = User.objects.get(id=id)
        customer.delete()
        return redirect(manage_customers)
    else:
        return redirect(admin_login)

def activate_customer(request,id):
    if request.user.is_authenticated:
        customer = User.objects.get(id=id)
        customer.is_active = True
        customer.save()
        return redirect(manage_customers)
    else:
        return redirect(admin_login)

def block_customer(request,id):
    if request.user.is_authenticated:
        customer=User.objects.get(id=id)
        customer.is_active = False
        customer.save()
        return redirect(manage_customers)
    else:
        return redirect(admin_login)

def dashboard(request):
    if request.user.is_authenticated:
        return render(request, './vendor/Dashboard.html')
    else:
        return redirect(admin_login)

def manage_category(request):
    if request.user.is_authenticated:
        category = Category.objects.all()
        context = {'categories':category}
        return render(request, './vendor/ManageCategory.html',context)
    else:
        return redirect(admin_login)

def create_category(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            category_name = request.POST['category_name']
            category_image = request.POST['pro_img']

            if category_image is not '':
                format, imgstr = category_image.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=category_name + '.' + ext)

            Category.objects.create(category_name=category_name,category_image=data)
          
            messages.error(request,"Category Created")
            return redirect(manage_category)
        else:
            return render(request, './vendor/CreateCategory.html')
    else:
        return redirect(admin_login)

def edit_category(request,id):
    if request.user.is_authenticated:
        category = Category.objects.get(id=id)
        if request.method == 'POST':
            category.category_name = request.POST['category_name']
            category_image = request.POST['pro_img']
            category_name = request.POST['category_name']

            if category_image is not '':
                format, imgstr = category_image.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=category_name + '.' + ext)
                
            category.category_image = data
            category.save()
        context = {'category':category}
        return render(request, './vendor/EditCategory.html',context)
    else:
        return redirect(admin_login)

def delete_category(request,id):
    if request.user.is_authenticated:
        delete_category = Category.objects.get(id=id)
        delete_category.delete()
        return redirect(manage_category)
    else:
        return redirect(admin_login)

def manage_products(request):
    if request.user.is_authenticated:
        products = Product.objects.all()
        context = {'products':products}
        return render(request, './vendor/ManageProduct.html',context)
    else:
        return redirect(admin_login)

def view_products(request):
    if request.user.is_authenticated:
        return render(request, './vendor/Products_View.html')
    else:
        return redirect(admin_login)

def create_product(request):
    if request.user.is_authenticated:
        categories = Category.objects.all()
        if request.method == 'POST':
            product_name = request.POST['product_name']
            category_id = request.POST['category']
            price = request.POST['price']
            stocks = request.POST['stocks']
            product_image = request.POST['pro_img']
            description = request.POST['description']
            images = request.FILES.getlist('file[]')
            if product_image is not '':
                format, imgstr = product_image.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=product_name + '.' + ext)

            category = Category.objects.get(id=category_id)
            product_data = Product.objects.create(product_name=product_name,category=category,price=price,image=data,description=description,stock=stocks)

            for img in images:
                fs=FileSystemStorage()
                file_path=fs.save(img.name,img)
                fileurl = fs.url(file_path)
                pimage=Product_Images.objects.create(product=product_data,extra_images=file_path)
                pimage.save()

        context = {'categories':categories}
        return render(request, './vendor/CreateProduct.html',context)
    else:
        return redirect(admin_login)

def edit_product(request,id):
    if request.user.is_authenticated:
        categories = Category.objects.all()
        products = Product.objects.get(id=id)
        if request.method == 'POST':
            product_name = request.POST['product_name']
            products.product_name = request.POST['product_name']
            products.category_id = Category.objects.get(id=request.POST['category'])
            products.price = request.POST['price']
            products.description = request.POST['description']
            product_image = request.POST['pro_img']

            if product_image is not '':
                format, imgstr = product_image.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=product_name + '.' + ext)
                products.image = data
            products.save()
        context = {'categories':categories,'products':products}
        return render(request, './vendor/EditProduct.html',context)
    else:
        return redirect(admin_login)

def delete_product(request,id):
    if request.user.is_authenticated:
        delete_product = Product.objects.get(id=id)
        delete_product.delete()
        return redirect(manage_products)
    else:
        return redirect(admin_login)

def manage_orders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(complete=True)
        context = {'orders':orders}
        return render(request, './vendor/ManageOrders.html',context)
    else:
        return redirect(admin_login)

def manage_order_items(request,id):
    if request.user.is_authenticated:
        orders = Order.objects.get(id=id)
        order_items = OrderItem.objects.filter(order=orders)
        context = {'orders':orders,'order_items':order_items}
        return render(request, './vendor/ManageOrderItems.html',context)
    else:
        return redirect(admin_login)

def manage_refund(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(complete=True,status='cancelled',user_cancelled='YES')
        context = {'orders':orders}
        return render(request, './vendor/ManageRefund.html',context)
    else:
        return redirect(admin_login)

def manage_refund_options(request,id,value):
    order = Order.objects.get(id=id)
    user = order.customer
    if value == 'approove':
        order.refund_status = True
        order.refund_status_value = value
        myuuid = uuid.uuid4().hex[:8]
        total_credit,total_debit = 0,0
        transaction_id = 'ORDER' + str(myuuid)
        wallets = Wallet.objects.create(customer=user,transaction_name='Refund',trasaction_type='Credit',credit_amount=order.grand_total,order=order,transaction_id=transaction_id)

        if Wallet.objects.filter(customer=request.user).exists():
            items = Wallet.objects.filter(customer=request.user)
            for i in items:
                total_credit += i.credit_amount
                total_debit += i.debit_amount
            net_amount = total_credit - total_debit
            i.net_amount = net_amount
            i.save()
        
    else:
        order.refund_status = False
        order.refund_status_value = value
    order.save()
    orders = Order.objects.filter(complete=True,status='cancelled',user_cancelled='YES')
    context = {'orders':orders}
    return render(request, './vendor/ManageRefund.html',context) 

def pending_order(request,id,value):
    order = Order.objects.get(id=id)
    order.status = value
    order.save()
    orders = Order.objects.filter(complete=True)
    context = {'orders':orders}
    return render(request, './vendor/ManageOrders.html',context)

def complete_order(request,id,value):
    orders = Order.objects.filter(complete=True)
    order = Order.objects.get(id=id)
    order.status = value
    order.save()
    context = {'orders':orders}
    return render(request, './vendor/ManageOrders.html',context)

def cancel_order(request,id,value):
    orders = Order.objects.filter(complete=True)
    order = Order.objects.get(id=id)
    order.status = value
    order.save()
    context = {'orders':orders}
    return render(request, './vendor/ManageOrders.html',context)

def report(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            complete =  Order.objects.filter(date_ordered__range=[start_date, end_date], status='deliverd').count()
            pending = Order.objects.filter(date_ordered__range=[start_date, end_date], status='packed').count()
            canceled = Order.objects.filter(status='cancelled').count()
            context =  {'complete':complete,'pending':pending,'canceled':canceled}
            return render(request, './vendor/Reports.html',context)
        else:
            today = date.today()
            complete =  Order.objects.filter(date_ordered = today, status='deliverd').count()
            pending = Order.objects.filter(date_ordered = today, status='packed').count()
            canceled = Order.objects.filter(status='cancelled').count()
            context =  {'complete':complete,'pending':pending,'canceled':canceled}
            return render(request, './vendor/Reports.html',context)
    else:
        return redirect(admin_login)   

def sales_report(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            orders = Order.objects.filter(date_ordered__range=[start_date, end_date], status='deliverd').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/SalesReport.html',context)
        else:
            today = date.today()
            orders = Order.objects.filter(date_ordered=today, status='deliverd').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/SalesReport.html',context)
    else:
        return redirect(admin_login)

def cancel_report(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            orders = Order.objects.filter(date_ordered__range=[start_date, end_date], status='cancelled').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/CancelledReport.html',context)
        else:
            today = date.today()
            orders = Order.objects.filter(date_ordered=today, status='cancelled').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/CancelledReport.html',context)
    else:
        return redirect(admin_login)    

def product_return_report(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            orders = Order.objects.filter(date_ordered__range=[start_date, end_date], user_cancelled='YES').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/ProductReturnReport.html',context)
        else:
            today = date.today()
            orders = Order.objects.filter(date_ordered=today, user_cancelled='YES').order_by('date_ordered')
            dict = {}
            count = 1
            for order in orders:
                if not order.date_ordered in dict.keys():
                    dict[order.date_ordered] = order
                    dict[order.date_ordered].total= order.get_cart_total(discount=0)
                    dict[order.date_ordered].count= count
                
                else:
                    dict[order.date_ordered].total += order.get_cart_total(discount=0)
                    dict[order.date_ordered].count += count
            context = {'dict':dict}
            return render(request, 'vendor/ProductReturnReport.html',context)
    else:
        return redirect(admin_login)   

def manage_offer(request):
    if request.user.is_authenticated:
        offers = Offer.objects.all()
        context = {'offers':offers}
        return render(request, './vendor/ManageOffer.html',context)
    else:
        return redirect(admin_login)

def create_offer(request):
    if request.user.is_authenticated:
        categories = Category.objects.all()
        products = Product.objects.all()
        if request.method == 'POST':
            offer_type = request.POST['offer_type']
            if offer_type == 'single':
                offer_name = request.POST['offer_name']  
                product_id = request.POST['product'] 
            else:
                category_id = request.POST['category']
                offer_name = request.POST['offer_name']  
            discount_percentage = int(request.POST['discount_amount'])
            offer_image = request.FILES['images']
            offer_starts = request.POST['offer_start']
            offer_ends = request.POST['offer_ends']
            if offer_type == 'single':
                product = Product.objects.get(id=product_id)
                real_price = product.price
                product.offer_price = real_price
                product.price = (real_price * discount_percentage/100) 
                product.offer_percentage = discount_percentage
                product.save()
                Offer.objects.create(offer_name=offer_name,Product=product,discount_amount=discount_percentage,offer_start=offer_starts,offer_expiry=offer_ends,offer_type=offer_type,offer_image=offer_image)
            else:
                category = Category.objects.get(id=category_id)
                products = Product.objects.filter(category=category)
                for product in products:
                    real_price = product.price
                    product.offer_price = real_price
                    lprice = (real_price * discount_percentage/100)
                    product.price = real_price - lprice
                    product.offer_percentage = discount_percentage
                    product.save()
                Offer.objects.create(offer_name=offer_name,category=category,discount_amount=discount_percentage,offer_start=offer_starts,offer_expiry=offer_ends,offer_type=offer_type,offer_image=offer_image)
            return redirect(manage_offer)
        else:
            context = {'categories':categories,'products':products}
            return render(request, './vendor/CreateOffer.html',context)
    else:
        return redirect(admin_login)

def delete_offer(request,id):
    if request.user.is_authenticated:
        offers = Offer.objects.get(id=id)
        if offers.offer_type == 'single':
            product_id = offers.Product.id
            product = Product.objects.get(id=product_id)

            offer_price = product.price
            real_price = product.offer_price

            product.price = real_price
            product.offer_price = 0
            product.offer_percentage = 0
            product.save()
            offers.delete()
        else:
            category_id = offers.category
            category = Category.objects.get(id=category_id.id)
            products = Product.objects.filter(category=category)
            for product in products:
                offer_price = product.price
                real_price = product.offer_price
                product.price = real_price
                product.offer_price = 0
                product.offer_percentage = 0
                product.save()
            offers.delete()
        return redirect(manage_offer)
    else:
        return redirect(admin_login)

def manage_coupens(request):
    if request.user.is_authenticated:
        coupen = Coupens.objects.all()
        context = {'coupens':coupen}
        return render(request, './vendor/ManageCoupens.html',context)
    else:
        return redirect(admin_login)

def create_coupen(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            coupens_name = request.POST['coupens_name']
            coupen_code = request.POST['coupen_code']
            coupen_start = request.POST['coupen_start']
            coupen_ends = request.POST['coupen_ends']
            discount_price = request.POST['discount_amount']
            Coupens.objects.create(coupen_name=coupens_name,coupen_code=coupen_code,validity_starts=coupen_start,validity_expire=coupen_ends,discount_amount=discount_price)
            return redirect(manage_coupens)
        else:
            return render(request, './vendor/CreateCoupens.html')
    else:
        return redirect(admin_login)

def edit_coupen(request,id):
    if request.user.is_authenticated:
        coupen = Coupens.objects.get(id=id)
        start_date = coupen.validity_starts.strftime('%Y-%m-%d')
        exipiry_date = coupen.validity_expire.strftime('%Y-%m-%d')
        if request.method == 'POST':
            coupen.coupen_name = request.POST['coupens_name']
            coupen.coupen_code = request.POST['coupen_code']
            coupen.validity_starts = request.POST['coupen_start']
            coupen.validity_expire = request.POST['coupen_ends']
            coupen.discount_amount = request.POST['discount_amount']
            coupen.save()   
        context = {'coupens':coupen,'start_date':start_date,'exipiry_date':exipiry_date}
        return render(request, './vendor/EditCoupen.html',context)
    else:
        return redirect(admin_login)

def delete_coupen(request,id):
    if request.user.is_authenticated:
        coupen = Coupens.objects.get(id=id)
        coupen.delete()
        return redirect(manage_coupens)
    else:
        return redirect(admin_login)