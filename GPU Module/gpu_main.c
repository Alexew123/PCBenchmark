#include <stdio.h>
#include <CL/cl.h>
#include "gpu_main.h"

double run_and_time(cl_command_queue queue, cl_kernel kernel, size_t global, size_t local);

void gpu_main(int gui_iterations) {
    cl_platform_id platform;
    cl_device_id device;
    cl_uint num_devices;
    cl_int status;

    // Get first platform
    status = clGetPlatformIDs(1, &platform, NULL);
    if (status != CL_SUCCESS) {
        printf("No OpenCL platforms found.\n");
        return;
    }

    // Get GPU
    status = clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &device, &num_devices);
    if (status != CL_SUCCESS || num_devices == 0) {
        printf("No GPU device found.\n");
        return;
    }

    // Get GPU info
    char name[128];
    clGetDeviceInfo(device, CL_DEVICE_NAME, sizeof(name), name, NULL);

    cl_ulong mem_size;
    clGetDeviceInfo(device, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(mem_size), &mem_size, NULL);

    cl_uint compute_units;
    clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(compute_units), &compute_units, NULL);

    cl_uint clock_freq;
    clGetDeviceInfo(device, CL_DEVICE_MAX_CLOCK_FREQUENCY, sizeof(clock_freq), &clock_freq, NULL);

    printf("GPU: %s\n", name);
    printf("Memory: %.2f MB\n", mem_size / (1024.0 * 1024.0));
    printf("Compute Units: %u\n", compute_units);
    printf("Max Clock: %u MHz\n", clock_freq);



    const char* flops_kernel_src =
        "__kernel void flops_kernel(__global float* out, int iters) {\n"
        "    int id = get_global_id(0);\n"
        "    float a = 1.0f, b = 1.000001f, c = 0.000001f;\n"
        "    float sum = 0.0f;\n"
        "    for (int i = 0; i < iters; i++) {\n"
        "        a = a * b;\n"
        "        a = a + c;\n"
        "        sum += a;\n"
        "        b = b + c;\n"
        "    }\n"
        "    out[id] = sum;\n"
        "}\n";


    // FLOPS benchmark

    size_t max_local_size;
    clGetDeviceInfo(device, CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(max_local_size), &max_local_size, NULL);
    size_t local_size = max_local_size;
    if (local_size > 256) local_size = 256;
    if (local_size < 32)  local_size = 32;

    size_t workgroups_per_cu = 32;  // safe number
    size_t num_workgroups = compute_units * workgroups_per_cu;
    size_t global_size = num_workgroups * local_size;
        
    int iterations = 5000000;

    // Create context and queue
    cl_context context = clCreateContext(NULL, 1, &device, NULL, NULL, NULL);
    cl_command_queue queue = clCreateCommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE, NULL);

    // Compile kernel
    cl_program program = clCreateProgramWithSource(context, 1, &flops_kernel_src, NULL, NULL);
    clBuildProgram(program, 0, NULL, NULL, NULL, NULL);

    cl_kernel kernel = clCreateKernel(program, "flops_kernel", NULL);

    // Output buffer
    cl_mem out_buf = clCreateBuffer(context, CL_MEM_WRITE_ONLY, global_size * sizeof(float), NULL, NULL);

    // Set args
    clSetKernelArg(kernel, 0, sizeof(cl_mem), &out_buf);
    clSetKernelArg(kernel, 1, sizeof(int), &iterations);

    // Run kernel
    cl_event event;
    clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global_size, &local_size, 0, NULL, &event);
    clFinish(queue);

    // Timing
    cl_ulong start, end;
    clGetEventProfilingInfo(event, CL_PROFILING_COMMAND_START, sizeof(start), &start, NULL);
    clGetEventProfilingInfo(event, CL_PROFILING_COMMAND_END, sizeof(end), &end, NULL);

    double time_sec = (double)(end - start) / 1e9; // ns -> s

    // Compute FLOPS
    double total_flops = (double)global_size * (double)iterations * 2.0;
    double gflops = total_flops / 1e9 / time_sec;

    printf("\nGPU FLOPS Benchmark\n");
    printf("Work-items: %zu\n", global_size);
    printf("Iterations per item: %d\n", iterations);
    printf("Time: %.3f sec\n", time_sec);
    printf("Performance: %.2f GFLOPS\n", gflops);

    // Cleanup
    clReleaseMemObject(out_buf);
    clReleaseKernel(kernel);
    clReleaseProgram(program);
    clReleaseCommandQueue(queue);
    clReleaseContext(context);

    const char* mem_kernel_src =
        "__kernel void write_test(__global float* out) {\n"
        "    int id = get_global_id(0);\n"
        "    out[id] = (float)id;\n"
        "}\n"
        "__kernel void read_test(__global float* in, __global float* out) {\n"
        "    int id = get_global_id(0);\n"
        "    float v = in[id];\n"
        "    out[id] = v;\n"
        "}\n"
        "__kernel void read_write_test(__global float* in, __global float* out) {\n"
        "    int id = get_global_id(0);\n"
        "    float v = in[id];\n"
        "    out[id] = v + 1.0f;\n"
        "}\n";

    // Choose buffer size (¼ of VRAM, max 1GB, min 256MB)
    size_t buffer_bytes = mem_size / 4;
    if (buffer_bytes > (size_t)1 * 1024 * 1024 * 1024)
        buffer_bytes = (size_t)1 * 1024 * 1024 * 1024;
    if (buffer_bytes < (size_t)256 * 1024 * 1024)
        buffer_bytes = (size_t)256 * 1024 * 1024;

    size_t num_floats = buffer_bytes / sizeof(float);
    printf("Buffer size: %.2f MB\n", buffer_bytes / (1024.0 * 1024.0));

    cl_context context2 = clCreateContext(NULL, 1, &device, NULL, NULL, NULL);
    cl_command_queue queue2 =
        clCreateCommandQueue(context2, device, CL_QUEUE_PROFILING_ENABLE, NULL);

    // Build memory test kernels
    cl_program program2 =
        clCreateProgramWithSource(context2, 1, &mem_kernel_src, NULL, NULL);
    clBuildProgram(program2, 0, NULL, NULL, NULL, NULL);

    cl_kernel k_write = clCreateKernel(program2, "write_test", NULL);
    cl_kernel k_read = clCreateKernel(program2, "read_test", NULL);
    cl_kernel k_rw = clCreateKernel(program2, "read_write_test", NULL);

    // Allocate buffers
    cl_mem buf_in =
        clCreateBuffer(context2, CL_MEM_READ_WRITE, buffer_bytes, NULL, NULL);
    cl_mem buf_out =
        clCreateBuffer(context2, CL_MEM_READ_WRITE, buffer_bytes, NULL, NULL);

    // Set arguments
    clSetKernelArg(k_write, 0, sizeof(cl_mem), &buf_out);
    clSetKernelArg(k_read, 0, sizeof(cl_mem), &buf_in);
    clSetKernelArg(k_read, 1, sizeof(cl_mem), &buf_out);
    clSetKernelArg(k_rw, 0, sizeof(cl_mem), &buf_in);
    clSetKernelArg(k_rw, 1, sizeof(cl_mem), &buf_out);

    size_t global = num_floats;
    size_t local = 256;


    // --- Run tests ----
    double t_write = run_and_time(queue2, k_write, global, local);
    double t_read = run_and_time(queue2, k_read, global, local);
    double t_rw = run_and_time(queue2, k_rw, global, local);


    // Bandwidth
    double bw_write = buffer_bytes / t_write / 1e9;
    double bw_read = buffer_bytes / t_read / 1e9;
    //double bw_rw = (2.0 * buffer_bytes) / t_rw / 1e9;
    double bw_rw = 0;


    for (int i = 0; i < gui_iterations; i++) {
        double t_rw = run_and_time(queue2, k_rw, global, local);
        bw_rw = (2.0 * buffer_bytes) / t_rw / 1e9;

        printf("PLOT:GPU:%d:%.2f\n", i, bw_rw);
    }

    printf("Write bandwidth: %.2f GB/s\n", bw_write);
    printf("Read bandwidth: %.2f GB/s\n", bw_read);
    printf("Read+Write bandwidth: %.2f GB/s\n", bw_rw);
    printf("\n");

    // Cleanup
    clReleaseMemObject(buf_in);
    clReleaseMemObject(buf_out);
    clReleaseKernel(k_write);
    clReleaseKernel(k_read);
    clReleaseKernel(k_rw);
    clReleaseProgram(program2);
    clReleaseCommandQueue(queue2);
    clReleaseContext(context2);

}

double run_and_time(cl_command_queue queue,
    cl_kernel kernel,
    size_t global,
    size_t local)
{
    cl_event evt;

    clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global, &local,
        0, NULL, &evt);
    clFinish(queue);

    cl_ulong start, end;
    clGetEventProfilingInfo(evt, CL_PROFILING_COMMAND_START,
        sizeof(start), &start, NULL);
    clGetEventProfilingInfo(evt, CL_PROFILING_COMMAND_END,
        sizeof(end), &end, NULL);

    clReleaseEvent(evt);

    return (double)(end - start) / 1e9; // seconds
}

