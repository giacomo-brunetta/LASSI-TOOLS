#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

int main(int argc, char** argv){
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

  int matA[a][b];
  int matB[b][c]; 

 for(int i = 0; i < a; i++){
    for(int j = 0; j < b; j++){
      matA[i][j] = i==j?1:0;
    }
 } 

  for(int i = 0; i < b; i++){
    for(int j = 0; j < c; j++){
      matB[i][j] = i==j?1:0;
    }
 }
  
  int matC[a][c];

  for(int i = 0; i < a; i++){
    for(int j = 0; j < c; j++){
      matC[i][j] = 0;
      for(int k = 0; k < b; k++){
        matC[i][j] += matA[i][k] * matB[k][j];
      }
      printf("%d ", matC[i][j]);
    }
    printf("\n");
  }
	return 0;

}
