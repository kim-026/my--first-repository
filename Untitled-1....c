#include <stdio.h>

int main()
 {
    char name[20];
    int age;

    printf("Enter your name: ");
    scanf("%s", name);

    printf("Enter your age: ");
    scanf("%d", &age);

    printf("Name: %s\n", name);
    printf("Age: %d", age);

    return 0;
}