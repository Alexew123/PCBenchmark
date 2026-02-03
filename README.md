# 🖥️ PC Benchmark Tool

![Project Status](https://img.shields.io/badge/Status-Finished-success)
![Built With](https://img.shields.io/badge/Built%20With-C%20%26%20Python-blue)

**A custom-built system analysis tool that pushes hardware to its limits to see what it can actually do.**

Hi! 👋 This is my semester project for **System Structure & Performance**. I wanted to build something that doesn't just show you a static score, but actually shows you how your computer is behaving in real-time from thermal throttling to memory bus saturation.

---

## 👀 What it looks like

![Dashboard Screenshot](https://github.com/user-attachments/assets/80a3dad9-6f47-44eb-b6c3-7e3b80a33f82)

---

## 💡 Why I built this
We have plenty of tools like CPU-Z or Cinebench, but I wanted to understand how they work under the hood.
My goal was to create a "Hybrid" application:
1.  **Low-Level C:** To get as close to the hardware as possible for raw accuracy.
2.  **High-Level Python:** To create a modern, responsive GUI without the headache of C graphics libraries.

## 🔥 The Cool Technical Stuff
Here are a few things I implemented that I'm proud of:

* **It knows your CPU Cores:**
    Modern CPUs are weird. They have fast "P-Cores" and efficient "E-Cores." My benchmark can actually tell the difference. In my testing, I could see the frequency jump from **3.5GHz (E-Core)** to **4.7GHz (P-Core)** depending on where the thread was scheduled.

* **Real RAM Bandwidth:**
    I discovered that "Copying" memory is way slower than just "Writing" it.
    * *Write Speed:* ~20 GB/s (One-way traffic)
    * *Copy Speed:* ~10 GB/s (Two-way traffic)
    The tool measures both to show you the physical limits of your memory bus.

* **No "Flat Line" Graphs:**
    Standard system timers aren't precise enough for fast CPUs. I implemented **Windows High-Resolution Timers** (`QueryPerformanceCounter`) so the graphs capture every microsecond of performance instead of just flat-lining.

* **GPU Compute:**
    I used **OpenCL** to bypass the graphics drivers and test raw floating-point math (FLOPS) on the graphics card.

---

## 🛠️ How it works (The Architecture)

It uses a **Controller-Module-GUI** pattern:

1.  **The Backend (C):**
    * `cpu_main.c`: Runs CoreMark (Integer) and Whetstone (Float) algorithms.
    * `ram_main.c`: Does pointer chasing to beat CPU pre-fetching and measure true latency.
    * `gpu_main.c`: Fires up OpenCL kernels to stress test FLOPS and VRAM.

2.  **The Bridge:**
    The C program prints raw data to `stdout` (like `PLOT:CPU:20500`).

3.  **The Frontend (Python):**
    The Python script launches the C executable and listens to that output pipe. It grabs the numbers and paints the graphs live using `tkinter`.

---

## 🚀 How to run it

### The Easy Way
1.  Go to the **dist** tab.
2.  Download `PCBenchmarkSuite.exe`.
3.  Run it and hit **START BENCHMARK**.

### The Dev Way (Build it yourself)
If you want to tweak the C code:

1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/Alexew123/PCBenchmark.git](https://github.com/Alexew123/PCBenchmark.git)
    ```
2.  **Compile the C code** (You need GCC + OpenCL SDK):
    ```bash
    gcc -o PCBenchmark.exe main.c -O3 -lOpenCL
    ```
3.  **Run the Python Launcher:**
    ```bash
    python launcher.py
    ```

---

## 📊 My Findings
During my tests, I compared a generic **Laptop (i7-1255U)** vs a **Desktop PC**.
* The Desktop GPU was nearly **4x faster** in memory bandwidth and with **3x more** FLOPS.
* The Laptop CPU started strong but quickly throttled due to heat, while the Desktop stayed flat and stable.\]
* The Laptop CPU has much more parallelism potential even though a single core is about the same as an older desktop CPU.
* You can read more about this in my [Documentation](Proiect.pdf).

---

**Author:** Cantemir Alexandru
