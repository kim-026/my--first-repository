marks = list(map(int, input().split()))
new_mark = int(input("Enter mark: "))

marks.append(new_mark)

marks.remove(min(marks))

for mark in marks:
    print(mark, end=" ")

print()
average = sum(marks) / len(marks)
print("Average:", average)
