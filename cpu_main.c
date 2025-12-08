#include <stdio.h>
#include <windows.h>
#include <intrin.h>
#include "CPU Module/coremark.h"
#include "CPU Module/cpu_main.h"
#include "CPU Module/whetstone.h"

#define WHETSTONE_LOOPCOUNT 5000000



void cpu_main(void) {

    // Get CPU Info
    int cpuInfo[4] = { 0 };
    char brand[0x40] = { 0 };

    __cpuid(cpuInfo, 0x80000002);
    memcpy(brand, cpuInfo, sizeof(cpuInfo));

    __cpuid(cpuInfo, 0x80000003);
    memcpy(brand + 16, cpuInfo, sizeof(cpuInfo));

    __cpuid(cpuInfo, 0x80000004);
    memcpy(brand + 32, cpuInfo, sizeof(cpuInfo));

    printf("CPU Brand: %s\n", brand);


    // Get nr. of processors
    SYSTEM_INFO sysinfo;
    GetSystemInfo(&sysinfo);

    printf("Number of processors: %u\n", sysinfo.dwNumberOfProcessors);

    // Get Cores/Threads
    DWORD len = 0;
    GetLogicalProcessorInformationEx(RelationProcessorCore, NULL, &len);
    PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX buffer = (PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)malloc(len);
    if (!GetLogicalProcessorInformationEx(RelationProcessorCore, buffer, &len)) {
        printf("Error getting processor information\n");
        free(buffer);
        return 1;
    }

    DWORD cores = 0;
    DWORD threads = 0;

    BYTE* ptr = (BYTE*)buffer;
    while (ptr < (BYTE*)buffer + len) {
        PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX info = (PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX)ptr;
        if (info->Relationship == RelationProcessorCore) {
            cores++;
            KAFFINITY mask = info->Processor.GroupMask[0].Mask;
            for (int i = 0; i < sizeof(KAFFINITY) * 8; i++) {
                if (mask & ((KAFFINITY)1 << i)) {
                    threads++;
                }
            }
            ptr += info->Size;
        }

    }   
    free(buffer);
    printf("Number of cores: %u\n", cores);
    printf("Number of threads: %u\n", threads);

	// Get CPU Frequencies
    __cpuid(cpuInfo, 0);
    if (cpuInfo[0] >= 0x16) {
        __cpuid(cpuInfo, 0x16);
        printf("Processor Base Frequency:  %0.2f GHz\r\n", cpuInfo[0]/1e3);
        printf("Maximum Frequency:         %0.2f GHz\r\n", cpuInfo[1]/1e3);
    }
    else {
        printf("CPUID level 16h unsupported\r\n");
    }

	printf("Starting integer benchmark...\n");
    coremark_main();

	printf("Starting floating-point benchmark...\n");
	whetstone_main(WHETSTONE_LOOPCOUNT);



}