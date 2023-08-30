# exchange
BTC exchange with basic buy, sell operations and a random initial balance between 1 and 10 BTC at registration.
Buy order business logic: a buy order for x amount of BTC at a price y is matched with all sell orders with a price equal or less than y, sorted by price, until the total amount of x BTC is reached. If there are not enough sell orders, the buy order remains active for the reamaining quantity.
Sell order business logic: the same of buy orders, but reversed.
