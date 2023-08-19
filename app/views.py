from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser 
from django.contrib import messages
from datetime import datetime
from .forms import RegisterUserForm, BuyOrderForm, SellOrderForm
from .utils import createProfile, createOrder, getIpAddress
from app.models import Profile, Order

def login_user(request):
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			profile = get_object_or_404(Profile, user=user)
			ip = getIpAddress(request=request)
			profile.ips.append(ip)
			profile.save()
			return render(request, 'exchange/home.html', {'balance': profile.btc_balance})
		else:
			messages.error(request, ("There Was An Error Logging In, Try Again..."))	
			return redirect('login')	
	else:
		return render(request, 'exchange/login.html', {})


def logout_user(request):
	logout(request)
	messages.success(request, ("You Were Logged Out!"))
	return redirect('home')


def register_user(request):
	if request.method == "POST":
		form = RegisterUserForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data['username']
			password = form.cleaned_data['password1']
			user = authenticate(username=username, password=password)
			profile = createProfile(request, user)
			profile.save()
			login(request, user)
			messages.success(request, ("Registration Successful!"))
			return render(request, 'exchange/home.html', {'balance': profile.btc_balance})
	else:
		form = RegisterUserForm()

	return render(request, 'exchange/register_user.html', {
		'form': form,
		})

def home(request):
	if request.method == 'GET':
		if not isinstance(request.user, AnonymousUser):
			profile = get_object_or_404(Profile, user=request.user)
			return render(request, 
				'exchange/home.html', {
				"balance": profile.btc_balance,
				})
		
		return render(request, 
			'exchange/home.html')


def buy_order(request):
	if request.method == 'POST':
		form = BuyOrderForm(request.POST)
		if form.is_valid():
			qty = form.cleaned_data.get('quantity')
			price = form.cleaned_data.get('price')
			buy_order = createOrder(
				get_object_or_404(Profile, user=request.user), 
				qty,
				price,
				Order.Types.BUY.value,
				Order.Status.PUB.value)
			# Check sell orders to buy
			sell_order = Order.objects.get(quantity=qty, price=price)
			if sell_order is not None:
				buy_order.status = Order.Status.EX.value
				sell_order.status = Order.Status.EX.value
				sell_order.save()
			buy_order.save()
			messages.success(request, ("Buy order successfully submitted!"))
			return redirect('home')
	else:
		form = BuyOrderForm()

	return render(request, 'exchange/buy_order.html', {
		'form': form,
		})
	
def sell_order(request):
	if request.method == 'POST':
		form = SellOrderForm(request.POST)
		if form.is_valid():
			# TODO: add check qty < balance
			sell_order = createOrder(
				get_object_or_404(Profile, user=request.user), 
				form.cleaned_data.get('quantity'),
				form.cleaned_data.get('price'),
				Order.Types.SELL.value,
				Order.Status.PUB.value)
			# TODO: check buy orders to buy (not requested by project requirements)
			sell_order.save()
			messages.success(request, ("Sell order successfully submitted!"))
			return redirect('home')
	else:
		form = SellOrderForm()

	return render(request, 'exchange/sell_order.html', {
		'form': form,
		})


def get_all_active_orders(request):
	if request.method == 'GET':
		active_orders = Order.objects.filter(status=Order.Status.PUB.value).values_list()
		orders = [order for order in active_orders]
		return render(
			request, 
			'exchange/active_orders.html', 
			{'orders': orders})


# this is not a balance! Calculate the profit/loss of all the operation of the user
# it is understood that there is a sell operation for each buy
# (if a balance is needed, add or subtract the total from the profile balance)
def get_user_total_profit_loss(request):
	if request.method == 'GET':
		profile = get_object_or_404(Profile, user=request.user)
		# get only the executed orders to calculate the profit/loss
		user_executed_orders = Order.objects.filter(
			profile= profile,
			status=Order.Status.EX.value)
		total = 0
		for order in user_executed_orders:
			if order.type == Order.Types.BUY.value:
				# subtract each buy order price
				total -= order.price * order.quantity
			else:
				# add each sell order price
				total += order.price * order.quantity

	return render(
			request, 
			'exchange/profit_loss.html', 
			{'total': total})