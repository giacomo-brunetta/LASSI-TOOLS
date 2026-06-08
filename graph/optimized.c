#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
  int a = 8;
  int b = 6;
  int c = 8;

  if (argc == 4) {
    a = atoi(argv[1]);
    b = atoi(argv[2]);
    c = atoi(argv[3]);
  } else if (argc != 1) {
    printf("Usage: %s <a> <b> <c>\n", argv[0]);
    return 1;
  }

  for (int i = 0; i < a; ++i) {
    for (int j = 0; j < c; ++j) {
      printf("%d ", (i == j && i < b) ? 1 : 0);
    }
    printf("\n");
  }

  return 0;
}
