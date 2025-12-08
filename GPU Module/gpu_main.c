#include <stdio.h>
#include <stdlib.h>
#include <CL/cl.h>
#include "GPU Module/gpu_main.h"

void gpu_main(void) {
    cl_uint num_platforms;
    cl_int status;

    status = clGetPlatformIDs(0, NULL, &num_platforms);
    if (status != CL_SUCCESS) { printf("Error getting platforms: %d\n", status); return 1; }
    printf("Number of OpenCL platforms: %u\n", num_platforms);
    if (num_platforms == 0) return 0;

    // Allocate dynamically
    cl_platform_id* platforms = (cl_platform_id*)malloc(sizeof(cl_platform_id) * num_platforms);
    clGetPlatformIDs(num_platforms, platforms, NULL);

    for (cl_uint i = 0; i < num_platforms; i++) {
        char name[128];
        clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, sizeof(name), name, NULL);
        printf("Platform %u: %s\n", i, name);
    }

    cl_uint num_devices;
    clGetDeviceIDs(platforms[0], CL_DEVICE_TYPE_ALL, 0, NULL, &num_devices);
    printf("Number of devices on platform 0: %u\n", num_devices);

    cl_device_id* devices = (cl_device_id*)malloc(sizeof(cl_device_id) * num_devices);
    clGetDeviceIDs(platforms[0], CL_DEVICE_TYPE_ALL, num_devices, devices, NULL);

    for (cl_uint i = 0; i < num_devices; i++) {
        char dev_name[128];
        clGetDeviceInfo(devices[i], CL_DEVICE_NAME, sizeof(dev_name), dev_name, NULL);
        printf("Device %u: %s\n", i, dev_name);
    }

    free(platforms);
    free(devices);
    return 0;
}
