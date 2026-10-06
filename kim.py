name = input()
item = input()
price = float(input())
quantity = int(input())

total = price * quantity

print(f"{name} bought {quantity} x {item} for Rs. {total}")