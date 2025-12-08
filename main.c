#include <stdio.h>
#include "CPU Module/cpu_main.h"
#include "GPU Module/gpu_main.h"

int main(void) {
	//cpu_main();
	gpu_main();

	printf("\nPress ENTER to exit...");
	getchar();
	return 0;
}