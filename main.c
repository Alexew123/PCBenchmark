#include <stdio.h>
#include "CPU Module/cpu_main.h"
#include "GPU Module/gpu_main.h"
#include "RAM Module/ram_main.h"

int main(int argc, char *argv[]) {

	setvbuf(stdout, NULL, _IONBF, 0);

	int iterations = 10;

	if (argc > 1) {
		iterations = atoi(argv[1]);
		if (iterations < 1) iterations = 1;
	}

	cpu_main();
	gpu_main(iterations);
	ram_main();

	return 0;
}