from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser 
from django.contrib import messages
from datetime import datetime
from .forms import RegisterUserForm, BuyOrderForm, SellOrderForm
from .utils import createProfile, createOrder, getIpAddress
from app.models import Profile, Order
from pprint import pprint

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

""" Un ordine di acquisto di una quantità x di BTC ad un prezzo y viene matchato con tutti gli ordini di vendita con un prezzo uguale o inferiore a y, ordinati per prezzo, fino a raggiungere la quantità totale di x BTC. Se gli ordini di vendita non bastano, l'ordine di acquisto rimane attivo per la quantità rimanente. """
def buy_order(request):
	if request.method == 'POST':
		form = BuyOrderForm(request.POST)
		if form.is_valid():
			buy_order = createOrder(
				get_object_or_404(Profile, user=request.user), 
				form.cleaned_data.get('quantity'),
				form.cleaned_data.get('price'),
				Order.Types.BUY.value,
				Order.Status.PUB.value)
			
			# Check sell orders to buy
			sell_orders = Order.objects.all().filter(type=Order.Types.SELL.value).filter(status=Order.Status.PUB.value).filter(price__lte=buy_order.price).order_by('-price')
			print('--- sell orders: ---')
			pprint(sell_orders)
			profile = get_object_or_404(Profile, user=request.user)
			buy_qty = buy_order.quantity
			for sell_order in sell_orders:
				if sell_order.quantity == buy_order.quantity:
					sell_order.status = Order.Status.EX.value
					sell_order.save()
					buy_qty -= sell_order.quantity
					buy_order.status = Order.Status.EX.value
					buy_order.save()
					profile.btc_balance += buy_order.quantity
					profile.save()
				elif sell_order.quantity < buy_order.quantity:
					buy_qty -= sell_order.quantity
					buy_order.quantity -= sell_order.quantity
					sell_order.status = Order.Status.EX.value
					sell_order.save()
					# save later the buy order if not totally filled
				else: # sell_order.quantity > buy_qty
					sell_order.quantity -= buy_order.quantity
					sell_order.save()
					buy_qty = 0
					buy_order.status = Order.Status.EX.value
					buy_order.save()
					profile.btc_balance += buy_order.quantity
					profile.save()
			
			# if buy order is not totally filled, save it as "published" for the remaining quantity
			print("--- buy_qty: " + str(buy_qty) + " ---")
			if buy_qty > 0:
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
			
			# Check buy orders to buy
			buy_orders = Order.objects.all().filter(type=Order.Types.BUY.value).filter(status=Order.Status.PUB.value).filter(price__gte=sell_order.price).order_by('price')
			print('--- buy orders: ---')
			pprint(buy_orders)
			profile = get_object_or_404(Profile, user=request.user)
			sell_qty = sell_order.quantity
			for buy_order in buy_orders:
				if buy_order.quantity == sell_order.quantity:
					buy_order.status = Order.Status.EX.value
					buy_order.save()
					sell_qty -= buy_order.quantity
					sell_order.status = Order.Status.EX.value
					sell_order.save()
					profile.btc_balance -= sell_order.quantity
					profile.save()
					break
				elif buy_order.quantity < sell_order.quantity:
					sell_qty -= buy_order.quantity
					sell_order.quantity -= buy_order.quantity
					buy_order.status = Order.Status.EX.value
					buy_order.save()
					# save later the sell order if not totally filled
				else: # buy_order.quantity > sell_qty
					buy_order.quantity -= sell_order.quantity
					buy_order.save()
					sell_qty = 0
					sell_order.status = Order.Status.EX.value
					sell_order.save()
					profile.btc_balance -= buy_order.quantity
					profile.save()
					break
			
			# if sell order is not totally filled, save it as "published" for the remaining quantity
			print("--- sell_qty: " + str(sell_qty) + " ---")
			if sell_qty > 0:
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