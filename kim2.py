customer_name = input("enter customer name:")
item_name = input("enter item name")
price = float(input("enter price:"))
quantity = int(input("enter quantity:"))

total = price * quantity

print(f"{name} bought {quantity} x {item} for Rs. {total}")
