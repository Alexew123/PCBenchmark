#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>
#include <time.h>
#include "ram_main.h"

#define BLOCK_SIZE_MB 512
#define BLOCK_SIZE_BYTES ((size_t)BLOCK_SIZE_MB * 1024 * 1024)
#define BW_ITERATIONS 50
#define LATENCY_STEPS 10000000 

static double get_time_sec() {
    LARGE_INTEGER frequency;
    LARGE_INTEGER start;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start);
    return (double)start.QuadPart / frequency.QuadPart;
}

void shuffle(int* array, size_t n) {
    if (n > 1) {
        for (size_t i = 0; i < n - 1; i++) {
            size_t j = i + rand() / (RAND_MAX / (n - i) + 1);
            int t = array[j];
            array[j] = array[i];
            array[i] = t;
        }
    }
}

void print_ram_specs() {
    MEMORYSTATUSEX statex;
    statex.dwLength = sizeof(statex);
    GlobalMemoryStatusEx(&statex);
    printf("Total Installed RAM: %.2f GB\n", (double)statex.ullTotalPhys / (1024 * 1024 * 1024));

    printf("RAM Frequency: ");
    FILE* fp = _popen("wmic memorychip get speed", "r");
    if (fp) {
        char buffer[128];
        int speed = 0;
        int last_speed = 0;
        int found = 0;

        while (fgets(buffer, sizeof(buffer), fp) != NULL) {
            if (sscanf_s(buffer, "%d", &speed) == 1) {

                if (speed != last_speed) {
                    if (found > 0) printf(", ");
                    printf("%d MHz", speed);
                    last_speed = speed;
                    found = 1;
                }
            }
        }
        if (!found) printf("Unknown");
        _pclose(fp);
    }
    else {
        printf("Could not retrieve");
    }
    printf("\n");
}

void ram_main(void) {

    print_ram_specs();

    char* buffer = (char*)malloc(BLOCK_SIZE_BYTES);
    if (!buffer) {
        printf(" Failed!\n");
        return;
    }

    double start, end, duration;
    double speed_mb, speed_gb;

    start = get_time_sec();
    for (int i = 0; i < BW_ITERATIONS; i++) {
        memset(buffer, 0xFF, BLOCK_SIZE_BYTES);
    }
    end = get_time_sec();

    duration = end - start;
    speed_mb = ((double)BLOCK_SIZE_MB * BW_ITERATIONS) / duration;
    speed_gb = speed_mb / 1024.0;

    printf("Write Bandwidth: %.2f GB/s\n",speed_gb);


    char* dest_buffer = (char*)malloc(BLOCK_SIZE_BYTES);
    if (dest_buffer) {
        start = get_time_sec();
        for (int i = 0; i < BW_ITERATIONS; i++) {
            memcpy(dest_buffer, buffer, BLOCK_SIZE_BYTES);
        }
        end = get_time_sec();
        free(dest_buffer);

        duration = end - start;
        speed_mb = ((double)BLOCK_SIZE_MB * BW_ITERATIONS) / duration;
        speed_gb = speed_mb / 1024.0;

        printf("Copy Bandwidth: %.2f GB/s\n", speed_gb);
    }
    else {
        printf("Copy Bandwidth: Skipped (Out of memory)\n");
    }

    int num_elements = BLOCK_SIZE_BYTES / sizeof(int);
    int* list_buffer = (int*)buffer;

    for (int i = 0; i < num_elements; i++) {
        list_buffer[i] = i;
    }

    srand((unsigned int)time(NULL));
    shuffle(list_buffer, num_elements);

    volatile int current_idx = 0;

    start = get_time_sec();
    for (int i = 0; i < LATENCY_STEPS; i++) {
        current_idx = list_buffer[current_idx];
    }
    end = get_time_sec();

    duration = end - start;
    double latency_ns = (duration / LATENCY_STEPS) * 1e9;

    printf("Latency: %.2f ns\n", latency_ns);

    free(buffer);
}