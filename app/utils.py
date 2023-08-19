from app.models import Profile, Order

def getIpAddress(request):
    user_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if user_ip:
        ip = user_ip.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def createProfile(request, user):
    ip = getIpAddress(request)
    profile = Profile()
    profile.user = user
    profile.ips = [ip]
    print("profile: ")
    print(profile.user)
    print(profile.ips)
    print(profile.subprofiles)
    return profile

def createOrder(profile, qty, price, type, status):
    order = Order()
    order.profile = profile
    order.quantity = qty
    order.price = price
    order.type = type
    order.status = status
    return order