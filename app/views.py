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

""" Un ordine di acquisto di una quantità x di BTC a ad un prezzo y viene matchato con tutti gli ordini di vendita con un prezzo uguale o inferiore a y, ordinati per prezzo, fino a raggiungere la quantità totale di x BTC. Se gli ordini di vendita non bastano, l'ordine di acquisto rimane attivo per la quantità rimanente. """
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
			profile = get_object_or_404(Profile, user=request.user)
			# Check sell orders to buy
			# query di tutti i sell order con price <= buy price e ordinarli in maniera discendente
			# ciclare, uno alla volta, i sell orders con price <= buy price fino a totalizzare la quantity indicata dal buy order. 2 casistiche:
			# 1) Se la quantity del buy order non è azzerata dopo aver preso tutti i sell order, creare buy order in stato published per la quantity rimanente
			# 2) Se trovo un sell order per una quantity > buy quantity, scalare la qty dal sell order che rimane published e contrassegnare buy order executed
			# se buy order viene eseguito, scalare il balance per la quantity eseguita
			sell_orders = Order.objects.all().filter(type=Order.Types.SELL.value).filter(status=Order.Status.PUB.value).filter(price__lte=buy_order.price).order_by('-price')
			print('--- sell orders: ---')
			pprint(sell_orders)
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

			""" if sell_order is not None:
				buy_order.status = Order.Status.EX.value
				sell_order.status = Order.Status.EX.value
				sell_order.save()
			buy_order.save() """
			
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