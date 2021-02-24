from django.shortcuts import render,redirect,HttpResponse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from vendor.models import Product,Order,OrderItem,ShippingAddress,Category,WishList,Product_Images,Coupens,Wallet,Offer
from . models import CustomerDetails
from django.http import JsonResponse
import json
import requests
import razorpay
from datetime import date,timedelta
from django.utils import timezone
import random
import string
import binascii
import uuid
from django.core.files import File
from django.core.files.storage import FileSystemStorage
import base64
from django.core.files.base import ContentFile
from django.core import serializers
import datetime

# Create your views here.

def user_signup(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email_address']
        mobile = request.POST['phone_number']
        password = request.POST['password']
        verify_password = request.POST['verify_password']
        credentials = {"firstname":first_name, "lastname":last_name, "email":email, "username":username,'mobile':mobile}

        if password==verify_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'username taken',credentials)
                return redirect(user_signup)

            elif User.objects.filter(email=email).exists():
                messages.info(request, 'email taken',credentials)
                return redirect(user_signup)
            elif CustomerDetails.objects.filter(mobile_number=mobile).exists():
                messages.info(request, 'email taken',credentials)
                return redirect(user_signup)
            else:
                letter = string.ascii_letters
                result = ''.join(random.choice(letter) for i in range(8))
                user = User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
                CustomerDetails.objects.create(user=user,mobile_number=mobile,refferal_code=result)
                messages.info(request,'User Created') 
                return redirect(user_signin)
        else:
            return render(request,'users/User_Signup.html')
    else:
        return render(request, 'users/User_Signup.html')

def user_signin(request):
    if request.user.is_authenticated:
        return redirect(user_homepage)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username,password=password)

        if user:
            auth.login(request,user)
            return redirect(user_homepage)
        else:
            messages.info(request, 'invalid Credentials')
            return redirect(user_signin)
    else:
        return render(request, 'users/User_Signin.html')

def user_logout(request):
    auth.logout(request)
    return redirect(user_signin)

def mobile_login(request):
    if request.method == 'POST':
        phones = request.POST['phone']
        if CustomerDetails.objects.filter(mobile_number=phones).exists():
            url = "https://d7networks.com/api/verifier/send"

            payload = {'mobile': str(+91)+phones,
            'sender_id': 'SMSINFO',
            'message': 'Your otp code is {code}',
            'expiry': '9000'}
            files = [

            ]
            headers = {
            'Authorization': 'Token fcdf198d8c96dc240b9edc2401f5a8a65389def3'
            }

            response = requests.request("POST", url, headers=headers, data = payload, files = files)
            data = response.text.encode('utf8')
            dict = json.loads(data.decode('utf8'))
            otp_id = dict['otp_id']
            request.session['otp_id'] = otp_id
            request.session['phone'] = phones
            return redirect(otp_verify)
        else:
            messages.error(request, 'Number Not Registered')
            return render(request, 'users/Mobile_Login.html')
    else:
        return render(request, 'users/Mobile_Login.html')

def otp_verify(request):
    if request.method == 'POST':
        otp = request.POST['otp']
        otp_id = request.session['otp_id']
        phones = request.session['phone']
        
        url = "https://d7networks.com/api/verifier/verify"

        payload = {'otp_id': otp_id,
        'otp_code': otp}
        files = [

        ]
        headers = {
        'Authorization': 'Token fcdf198d8c96dc240b9edc2401f5a8a65389def3'
        }

        response = requests.request("POST", url, headers=headers, data = payload, files = files)

        data = response.text.encode('utf8')
        dict = json.loads(data.decode('utf8'))
        status = dict['status']
        if status == 'success':
            user = CustomerDetails.objects.filter(mobile_number=phones).first()
            if user:
                if user.is_active == False:
                    messages.info(request, 'User Is Blocked')
                    return redirect(mobile_login)
                else:
                    auth.login(request, user)
                    return redirect(user_homepage)
            else:
                messages.info(request, 'User Not Available')
                return redirect(mobile_login)
        else:
            messages.info(request, 'Otp Invalid')
            return render(request, 'users/Otp_Verify.html')
    else:
        return render(request, 'users/Otp_Verify.html')

#coreStuffs

def user_homepage(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        items = 0
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        user_profile = []
        items_count = 0
        wishlist_items = '0'
        wishlist_count = '0'

    data={}
    category = Category.objects.all()
    c=0
    for i in category:
        if c==2:
            break
        data[i.category_name] = Product.objects.filter(category=i)
        c+=1
    offers = Offer.objects.filter(offer_status='Valid')

    context = {'offers':offers,'cartitems':cartitems,'categories':category,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count,'datas':data}
    return render(request, 'users/HomePage.html',context)

def view_cart(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        user_profile = []
        items_count = 0
        wishlist_items = 0
        wishlist_count = 0
    context = {'items':items,'order':order,'user_profile':user_profile,'cartitems':cartitems,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Cart.html',context)

def checkout(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        ship = ShippingAddress.objects.filter(customer=request.user).distinct('address')
        client = razorpay.Client(auth=("rzp_test_P9QI5lhnHOuMk7", "42Vsw0omw3ZbXYbROCoF7SYt"))
        if not request.session.get('discount'):
            order_amount =  float(order.get_cart_total(discount=0))
        else:
            discounted_percentage = request.session.get('discount')
            order_amount = float(order.get_cart_total(discount=discounted_percentage))
        order_amount *= 100
        order_currency = 'INR'
        order_receipt = 'order_rcptid_11'
        notes = {'Shipping address':'kattekaden' 'kearla'}
        response = client.order.create(dict(amount=order_amount,currency=order_currency,receipt=order_receipt,notes=notes,payment_capture='0'))
        order_id = response['id']
        order_status = response['status']
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []


        customer_details = CustomerDetails.objects.get(user_id=request.user)
        reffered_user = customer_details.reffered_user
        refferd_user = CustomerDetails.objects.get(user_id=reffered_user)
        if CustomerDetails.objects.filter(user_type='Refferal') and Order.objects.filter(customer=request.user, complete=True).count() < 1 :
            myuuid = uuid.uuid4().hex[:8]
            total_credit,total_debit = 0,0
            transaction_id = 'ORDER' + str(myuuid)
            current_customer = CustomerDetails.objects.get(user=request.user)
            cashback_amount = float(order.get_cart_total(discount=0)) * 30/100
            Wallet.objects.create(customer=refferd_user.user,transaction_name='Cashback',trasaction_type='Credit',credit_amount=cashback_amount,transaction_id=transaction_id,cashback_amount=cashback_amount)
            if Wallet.objects.filter(customer=refferd_user.user).exists():
                items = Wallet.objects.filter(customer=refferd_user.user)
                for i in items:
                    total_credit += i.credit_amount 
                    total_debit += i.debit_amount        
                net_amount = total_credit - total_debit
                i.net_amount = net_amount
                i.save()
        
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        user_profile = []
        ship = []
        order_id = []

    context = {'items':items,'order':order,'cartitems':cartitems,'user_profile':user_profile,'ship':ship,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count,'order_id':order_id}
    return render(request, 'users/Checkout.html',context)

def update_item(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=request.user, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    #wishlist
    wishlist_item,wishlist_created = WishList.objects.get_or_create(customer=request.user,product=product)

    cartitems = order.get_cart_items
    items = order.orderitem_set.all()
    items_count = items.count()

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
        
    elif action == 'delete':
        orderItem.quantity = (orderItem.quantity - 1000)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)
    elif action == 'add_wishlist':
        wishlist_item.customer =  request.user
        wishlist_item.product = product
        wishlist_item.save()
    elif action == 'wishlist_delete':
        wishlist_item.customer =  request.user
        wishlist_item.product = product
        wishlist_item.delete()
    elif action == 'wishlist_add':
        orderItem.quantity = (orderItem.quantity + 1)
        wishlist_item.customer =  request.user
        wishlist_item.product = product
        wishlist_item.delete()

    orderItem.save()


    if orderItem.quantity <= 0 :
        orderItem.delete()

    return JsonResponse('item Was Added', safe=False)

def process_order(request):
    transaction_id = datetime.datetime.now().timestamp()
    if request.user.is_authenticated:
        if request.method == 'POST':
            address = request.POST['address']
            city = request.POST['city']
            state = request.POST['state']
            zipcode = request.POST['zipcode']
            country = request.POST['mobilenumber']
            mobilenumber = request.POST['country']
            payment_mode = request.POST['paymentmode']
            total = float(request.POST['total'])

        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        order.transaction_id = transaction_id

        if payment_mode == 'wallet':
            # paymentmode2 = request.POST['paymentmode2']
            if Wallet.objects.filter(customer=request.user).exists():
                current_wallet_amount = Wallet.objects.filter(customer=request.user).latest('time')
                if current_wallet_amount.net_amount <= total:
                    return JsonResponse('insufficiant_balance',safe=False)
                else:
                    myuuid = uuid.uuid4().hex[:8]
                    transaction_id = 'ORDER' + str(myuuid)
                    total_credit,total_debit = 0,0
                    Wallet.objects.create(customer=request.user,order=order,transaction_name='Purchase',trasaction_type='Debit',transaction_id=transaction_id,debit_amount=total)
                    transactions = Wallet.objects.filter(customer=request.user)
                    for transaction in transactions:
                        total_credit += transaction.credit_amount 
                        total_debit += transaction.debit_amount        
                        net_amount = total_credit - total_debit
                    transaction.net_amount = net_amount
                    transaction.save()
            else:
                return JsonResponse('active_wallet',safe=False)
        else:
            if request.session.has_key('discount'):
                discounted_percentage = request.session.get('discount')
                if total-total*discounted_percentage/100 == order.get_cart_total(discount=discounted_percentage):
                    order.grand_total = total-total*discounted_percentage/100
                    order.discounted = total*discounted_percentage/100
                    order.complete = True
                    del request.session['discount']
                order.save()
            else:
                if total == order.get_cart_total(discount=0):
                    order.grand_total = total
                    order.complete = True
                order.save()



        ShippingAddress.objects.create(customer=request.user,order=order,address=address,city=city,state=state,zipcode=zipcode,country=country,mobilenumber=mobilenumber,payment_status=payment_mode)
        add = 'itemsaved'
    else:
        print('user not logged in')
    return JsonResponse(add, safe=False)

def coupen_process(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            order, created = Order.objects.get_or_create(customer=request.user,complete=False)
            coupen_codes = request.POST['coupenCode']
            if Coupens.objects.filter(coupen_code=coupen_codes).exists():
                coupen = Coupens.objects.get(coupen_code=coupen_codes)
                discounts = request.session['discount'] = coupen.discount_amount
                new_price = order.get_cart_total(discount=discounts)
                context = {'discount': discounts,'new_price':new_price,'validcoupen':'validcoupen'}
                return JsonResponse(context)
            else:
                return JsonResponse('notvalidcoupen',safe=False)
        else:
            return JsonResponse('wow',safe=False)
    else:
        print('user not loginned')

def order_placed(request,id):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []

        orders = Order.objects.get(id=id)
        order_items = OrderItem.objects.filter(order=orders)
        shipping_address = ShippingAddress.objects.filter(order=orders)
        context = {'order':order,'order_items':order_items,'shipping_address':shipping_address,'cartitems':cartitems,'user_profile':user_profile,'items_count':items_count,'wishlist_count':wishlist_count,'orders':orders}
        return render(request, './users/Order_Placed.html',context)
    else:
        return redirect(user_signin)

def dashboard_overview(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        order_overview = Order.objects.filter(complete=False)
        orders_count = Order.objects.filter(complete=False).count()        
        item_count = items.count()
        
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
            transaction = Wallet.objects.filter(customer=request.user).latest('time')
            wallet_amount = transaction.net_amount
        except:
            user_profile = []
            wallet_amount = 0
    else:
        return redirect(user_signin)
    
    context = {'orders_count':orders_count,'item_count':item_count,'wallet_amount':wallet_amount,'refferd_users_count':refferd_users_count,'customer_details':customer_details,'items':items,'order':order,'cartitems':cartitems,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_Overview.html',context)

def user_profile(request,id):
    if request.user.is_authenticated:
        customers_data = User.objects.get(id=id)
        additional_customer_data = CustomerDetails.objects.get(user=customers_data)
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []

        context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'customers_data':customers_data,'additional_customer_data':additional_customer_data,'items_count':items_count,'wishlist_count':wishlist_count,'user_profile':user_profile}

        if request.method == 'POST':
            customers_data.first_name = request.POST['first_name']
            customers_data.last_name = request.POST['last_name']
            customers_data.username = request.POST['username']
            customers_data.email = request.POST['email']
            additional_customer_data.mobile_number = request.POST['mobile_number']
            profile_picture = request.POST['image64data']

            if profile_picture is not '':
                format, imgstr = profile_picture.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=request.user.first_name + '.' + ext)
                additional_customer_data.profile_picture = data

            additional_customer_data.save()
            customers_data.save()
            return redirect(dashboard_overview)
        else:
            return render(request, 'users/profile.html',context)
    else:
        return redirect(user_signin)

def latest_offers(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []

    else:
        items = 0
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        user_profile = []
        items_count = 0
        wishlist_items = '0'
        wishlist_count = '0'

    products = Product.objects.all()
    category = Category.objects.all()
    offers = Offer.objects.all()

    context = {'offers':offers,'products':products,'cartitems':cartitems,'categories':category,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Latest_Offers.html',context)

def dashboard_my_wishlist(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'user_profile':user_profile,'items':items,'order':order,'cartitems':cartitems,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_My_Wishlist.html',context)

def dashboard_my_wallet(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []

        active_offers = Coupens.objects.filter(coupen_status=False)
        print(active_offers)

        #wallet starts here
        if request.method == 'POST':
            myuuid = uuid.uuid4().hex[:8]
            total_credit,total_debit = 0,0
            transaction_id = 'ORDER' + str(myuuid)
            addbalance = request.POST['addbalance']
            Wallet.objects.create(customer=request.user,transaction_name='Add Balance',trasaction_type='Credit',credit_amount=addbalance,transaction_id=transaction_id)

            if Wallet.objects.filter(customer=request.user).exists():
                items = Wallet.objects.filter(customer=request.user)

            for i in items:
                total_credit += i.credit_amount 
                total_debit += i.debit_amount        
                net_amount = total_credit - total_debit
                i.net_amount = net_amount
                i.save()
            return redirect(dashboard_my_wallet)

        customer=request.user
        transactions = Wallet.objects.filter(customer=request.user)
        try:
            transaction = Wallet.objects.filter(customer=request.user).latest('time')
            wallet_amount = transaction.net_amount
            cashback_amount = transaction.cashback_amount
        except:
            wallet_amount = 0
            cashback_amount = 0
    else:
        return redirect(user_signin)

    context = {'active_offers':active_offers,'refferd_users_count':refferd_users_count,'customer_details':customer_details,'user_profile':user_profile,'cashback_amount':cashback_amount,'wallet_amount':wallet_amount,'transactions':transactions,'items':items,'order':order,'cartitems':cartitems,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_My_Wallet.html',context)

def dashboard_my_rewards(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'user_profile':user_profile,'items':items,'order':order,'cartitems':cartitems,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_My_Rewards.html',context)

def dashboard_my_orders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(customer=request.user, complete=True,user_cancelled='NO').order_by('-time_ordered')
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'items':items,'order':order,'cartitems':cartitems,'orders':orders,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_My_Orders.html',context)

def dashboard_my_order_items(request,id):
    if request.user.is_authenticated:
        orders = Order.objects.get(id=id)
        order_items = OrderItem.objects.filter(order=orders)
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'items':items,'order':order,'cartitems':cartitems,'orders':orders,'order_items':order_items,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/OrderItems.html',context)

def dashboard_myorder_cancell(request,id):
    orders = Order.objects.get(id=id)
    orders.user_cancelled = 'YES'
    orders.status = 'cancelled'
    orders.save()
    return redirect(dashboard_my_orders)

def dashboard_my_cancelled_items(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user_cancelled='YES')
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'items':items,'orders':order,'cartitems':cartitems,'orders':orders,'user_profile':user_profile,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/CancelledOrders.html',context)

def order_bill(request,id):
    if request.user.is_authenticated:
        orders = Order.objects.get(id=id)
        order_items = OrderItem.objects.filter(order=orders)
        order_items_count = len(order_items)
        shipping_address = ShippingAddress.objects.filter(order=orders)
        context = {'orders':orders,'order_items':order_items,'shipping_address':shipping_address,'order_items_count':order_items_count}
        return render(request, './users/bill.html',context)
    else:
        return redirect(user_signin)

def dashboard_my_address(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        shipping_address = ShippingAddress.objects.filter(customer=request.user).distinct('address')
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        return redirect(user_signin)

    context = {'refferd_users_count':refferd_users_count,'customer_details':customer_details,'user_profile':user_profile,'items':items,'order':order,'cartitems':cartitems,'items_count':items_count,'shipping_address':shipping_address,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Dashboard_My_Addresses.html',context)

def dashboard_add_address(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            address = request.POST['address']
            city = request.POST['city']
            state = request.POST['state']
            zipcode = request.POST['zipcode']
            country = request.POST['country']
            mobile_number = request.POST['mobilenumber']
            ShippingAddress.objects.create(customer=request.user,address=address,city=city,state=state,zipcode=zipcode,country=country,mobilenumber=mobile_number)
            return redirect(dashboard_my_address)
        else:
            customer_details = CustomerDetails.objects.get(user_id=request.user)
            try:
                user_profile = CustomerDetails.objects.get(user_id=request.user)
            except:
                user_profile = []
            refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
            refferd_users_count = refferd_users.count() 
            context = {'user_profile':user_profile,'customer_details':customer_details,'refferd_users_count':refferd_users_count}
            return render(request, 'users/Add_Address.html',context)
    else:
        return redirect(user_signin)

def dashboard_update_address(request,id):
    if request.user.is_authenticated:
        address = ShippingAddress.objects.get(id=id)
        customer_details = CustomerDetails.objects.get(user_id=request.user)
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
        refferd_users = CustomerDetails.objects.filter(reffered_user=request.user.id)
        refferd_users_count = refferd_users.count()
        context = {'address':address,'user_profile':user_profile,'customer_details':customer_details,'refferd_users_count':refferd_users_count}
        if request.method == 'POST':
            address.customer = request.user
            address.address = request.POST['address']
            address.city = request.POST['city']
            address.state = request.POST['state']
            address.zipcode = request.POST['zipcode']
            address.country = request.POST['country']
            address.mobile_number = request.POST['mobilenumber']
            address.save()
            return redirect(dashboard_my_address)
        else:
            return render(request, 'users/Edit_Address.html',context)
    else:
        return redirect(user_signin)

def dashboard_my_address_delete(request,id):
    if request.user.is_authenticated:
        shipping_address = ShippingAddress.objects.get(id=id)
        shipping_address.delete()
        return redirect(dashboard_my_address)
    else:
        return redirect(user_signin)

def shop_grid(request):
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        items = []
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        items_count = 0
        wishlist_items = 0
        wishlist_count = 0
        user_profile = []
    product = Product.objects.all()
    
    data={}
    category = Category.objects.all()
    for i in category:
        data[i.category_name] = Product.objects.filter(category=i)
    context = {'datas':data,'user_profile':user_profile,'products':product,'items':items,'order':order,'cartitems':cartitems,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Shop_Grid.html',context)

def single_product_view(request,id):
    if request.user.is_authenticated:
        products = Product.objects.get(id=id)
        extra_images = Product_Images.objects.filter(product=products)
        order, created = Order.objects.get_or_create(customer=request.user,complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        products = Product.objects.get(id=id)
        items = 0
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        items_count = 0
        wishlist_items = 0
        wishlist_count = 0
        user_profile = []
        extra_images = Product_Images.objects.filter(product=products)
    context = {'user_profile':user_profile,'items':items,'order':order,'cartitems':cartitems,'products':products,'extra_images':extra_images,'items_count':items_count,'wishlist_items':wishlist_items,'wishlist_count':wishlist_count}
    return render(request, 'users/Single_Product_View.html',context)

def category(request, id):
    if request.user.is_authenticated:
        product = Product.objects.filter(category=id)
        category = Category.objects.get(id=id)
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        items = order.orderitem_set.all()
        cartitems = order.get_cart_items
        items_count = items.count()
        wishlist_items = WishList.objects.filter(customer=request.user)
        wishlist_count = wishlist_items.count()
        try:
            user_profile = CustomerDetails.objects.get(user_id=request.user)
        except:
            user_profile = []
    else:
        category = Category.objects.all()
        product = Product.objects.filter(category=id)
        order = {'get_cart_total':0, 'get_cart_items':0}
        cartitems = order['get_cart_items']
        items_count = 0
        wishlist_items = 0
        wishlist_count = 0
        user_profile = []
    context = {'user_profile':user_profile,'product':product,'category':category,'cartitems':cartitems,'items_count':items_count,'wishlist_count':wishlist_count,'wishlist_items':wishlist_items}
    return render(request,'users/View_Category.html',context)

def refferal_signup(request,refferal_code):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email_address']
        mobile = request.POST['phone_number']
        password = request.POST['password']
        verify_password = request.POST['verify_password']
        credentials = {"firstname":first_name, "lastname":last_name, "email":email, "username":username,'mobile':mobile}

        if password==verify_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'username taken',credentials)
                return redirect(user_signup)

            elif User.objects.filter(email=email).exists():
                messages.info(request, 'email taken',credentials)
                return redirect(user_signup)
            elif CustomerDetails.objects.filter(mobile_number=mobile).exists():
                messages.info(request, 'email taken',credentials)
                return redirect(user_signup)
            else:
                letter = string.ascii_letters
                result = ''.join(random.choice(letter) for i in range(8))
                if CustomerDetails.objects.filter(refferal_code=refferal_code).exists():
                    user = User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
                    refferd_user = CustomerDetails.objects.get(refferal_code=refferal_code)
                    CustomerDetails.objects.create(user=user,mobile_number=mobile,refferal_code=result,reffered_user=refferd_user.user.id,user_type='Refferal')
                    myuuid = uuid.uuid4().hex[:8]
                    total_credit,total_debit = 0,0
                    transaction_id = 'ORDER' + str(myuuid)
                    Wallet.objects.create(customer=refferd_user.user,transaction_name='Reffaral Bonus',trasaction_type='Credit',credit_amount=10,transaction_id=transaction_id)
                    if Wallet.objects.filter(customer=refferd_user.user).exists():
                        items = Wallet.objects.filter(customer=refferd_user.user)
                    for i in items:
                        total_credit += i.credit_amount 
                        total_debit += i.debit_amount        
                    net_amount = total_credit - total_debit
                    i.net_amount = net_amount
                    i.save()
                    messages.info(request,'User Created') 
                    return redirect(user_signin)
                else:
                    messages.info(request,'Wrong refferel code ')
                    return render(request, 'users/Reffeal_Signup.html',credentials)  
        else:
            return render(request,'users/Reffeal_Signup.html')
    else:
        return render(request, 'users/Reffeal_Signup.html')