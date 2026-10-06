while True:
    guess=int(input("enter num:"))
    if guess>secrect:
        print("too high ")
    elif guess <secret:
            print("too low")
    else:
                print("correct!")
                break
