secret = 42

while True:
    guess = int(input("Enter num: "))

    if guess > secret:
        print("Too High")
    elif guess < secret:
        print("Too Low")
    else:
        print("Correct!")
        break
