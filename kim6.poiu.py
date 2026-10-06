while true:
    guess=int(input("enter num:"))
    if guess>secrect:
        print("too high ")
    elif guess <secrect:
            print("too low")
    else:
                print("correct!")
                break
