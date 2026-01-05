import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import math

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

POSSIBLE_PATHS = [
    "x64/Release/PCBenchmark.exe",
]

MAX_COREMARK  = 25000.0
MAX_WHETSTONE = 20.0

MAX_GPU_BW    = 200.0
MAX_GPU_FLOPS = 2000.0

MAX_RAM_BW    = 30.0
MAX_RAM_SIZE  = 64.0

SCORE_CAP_COREMARK = 4000
SCORE_CAP_WHET     = 1000
SCORE_CAP_GPU      = 2500
SCORE_CAP_RAM      = 2500

class ModernGraph(tk.Canvas):
    def __init__(self, parent, title, unit_suffix, height=100, bg="#fafafa", line_color="#0078D7"):
        super().__init__(parent, bg=bg, height=height, highlightthickness=1, highlightbackground="#e0e0e0")
        self.pack(fill=tk.X, padx=20, pady=10)
        
        self.title = title
        self.unit = unit_suffix
        self.line_color = line_color
        self.fill_color = "#D6EAF8"
        self.data = []
        
        self.pad_left = 50   
        self.pad_bottom = 25 
        self.pad_top = 30    
        self.pad_right = 10
        
        self.draw_chrome()

    def add_point(self, value):
        self.data.append(value)
        self.redraw()

    def clear(self):
        self.data = []
        self.delete("data")
        self.delete("stats")
        self.redraw()

    def draw_chrome(self):
        self.create_text(10, 10, text=self.title, anchor="nw", font=("Segoe UI", 9, "bold"), fill="#333")

    def redraw(self):
        self.delete("all")
        self.draw_chrome() 
        
        w = self.winfo_width()
        h = self.winfo_height()
        
        if w < 10: return

        graph_w = w - self.pad_left - self.pad_right
        graph_h = h - self.pad_top - self.pad_bottom
        
        if not self.data:
            max_val = 100
            min_val = 0
        else:
            max_val = max(self.data) * 1.15 
            if max_val == 0: max_val = 10
            min_val = 0

        if self.data:
            avg_val = sum(self.data) / len(self.data)
            cur_val = self.data[-1]
            stats_text = f"Current: {cur_val:.1f} | Avg: {avg_val:.1f} | Max: {max(self.data):.1f} {self.unit}"
        else:
            stats_text = "Waiting..."
        
        self.create_text(w - 10, 10, text=stats_text, anchor="ne", font=("Segoe UI", 8), fill="#666")

        steps = 4
        for i in range(steps + 1):
            y_ratio = i / steps
            y_pos = (h - self.pad_bottom) - (y_ratio * graph_h)
            val = min_val + (y_ratio * (max_val - min_val))
            
            self.create_line(self.pad_left, y_pos, w - self.pad_right, y_pos, fill="#e0e0e0", dash=(2, 2))
            self.create_text(self.pad_left - 5, y_pos, text=f"{val:.1f}", anchor="e", font=("Segoe UI", 7), fill="#888")

        self.create_line(self.pad_left, h - self.pad_bottom, w - self.pad_right, h - self.pad_bottom, fill="#ccc")

        if len(self.data) > 1:
            points = []
            points.append(self.pad_left)
            points.append(h - self.pad_bottom)

            step_x = graph_w / (len(self.data) - 1)
            
            for i, val in enumerate(self.data):
                x = self.pad_left + (i * step_x)
                y = (h - self.pad_bottom) - ((val / max_val) * graph_h)
                points.append(x)
                points.append(y)
            
            points.append(self.pad_left + ((len(self.data)-1) * step_x))
            points.append(h - self.pad_bottom)

            self.create_polygon(points, fill=self.fill_color, outline="", tags="data")

            line_points = points[2:-2] 
            self.create_line(line_points, fill=self.line_color, width=2, smooth=True, tags="data")

class BenchmarkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PC Benchmark Suite")
        self.root.geometry("1000x800") 
        self.root.resizable(True, True)
        
        self.results = {
            "cpu_coremark": 0.0, 
            "cpu_whetstone": 0.0,
            "gpu_bw": 0.0,
            "gpu_flops": 0.0,
            "ram_copy": 0.0, 
            "ram_total_gb": 0.0,
            "ram_latency": 1.0
        }
        
        self.graph_data = {"CPU": [], "GPU": [], "RAM": []}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", font=("Segoe UI", 10), background="#f0f0f0")
        self.root.configure(bg="#f0f0f0")
        
        header = tk.Frame(root, bg="#0078D7", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="PC Benchmark", font=("Segoe UI", 14, "bold"), 
                 bg="#0078D7", fg="white").pack(expand=True)

        self.main_split = tk.Frame(root, bg="#f0f0f0")
        self.main_split.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.left_col = tk.Frame(self.main_split, bg="#f0f0f0", width=480)
        self.left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        self.left_col.pack_propagate(False)

        self.details_canvas = tk.Canvas(self.left_col, bg="#f0f0f0", highlightthickness=0)
        self.details_scroll = ttk.Scrollbar(self.left_col, orient="vertical", command=self.details_canvas.yview)
        self.details_frame = tk.Frame(self.details_canvas, bg="#f0f0f0")

        self.details_frame.bind("<Configure>", lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all")))
        self.details_canvas.create_window((0, 0), window=self.details_frame, anchor="nw", width=460)
        self.details_canvas.configure(yscrollcommand=self.details_scroll.set)

        self.details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.details_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_detail_group(self.details_frame, "PROCESSOR (CPU) - 1 Core", [
            ("cpu_brand",      "CPU Brand:"),
            ("cpu_procs",      "Nr. of Processors:"),
            ("cpu_cores",      "Nr. of Cores:"),
            ("cpu_threads",    "Nr. of Threads:"),
            ("cpu_base_freq",  "Base Frequency:"),
            ("cpu_max_freq",   "Max Frequency:"),
            ("cpu_coremark",   "CoreMark Score:"),
            ("cpu_whetstone",  "Whetstone Score:")
        ])
        
        self.create_detail_group(self.details_frame, "GRAPHICS (GPU)", [
            ("gpu_brand",    "GPU Brand:"),
            ("gpu_mem",      "GPU Memory:"),
            ("gpu_clock",    "Max Clock:"),
            ("gpu_flops",    "GFLOPS (Raw):"), 
            ("gpu_write",    "Write Bandwidth:"),
            ("gpu_read",     "Read Bandwidth:"),
            ("gpu_rw",       "Read+Write BW:")
        ])

        self.create_detail_group(self.details_frame, "MEMORY (RAM)", [
            ("ram_total",    "Total RAM:"),
            ("ram_freq",     "RAM Frequency:"),
            ("ram_write",    "Write Bandwidth:"),
            ("ram_copy",     "Copy Bandwidth:"),
            ("ram_latency",  "Latency:")
        ])

        self.right_col = tk.Frame(self.main_split, bg="white", relief="flat")
        self.right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        self.graph_cpu = ModernGraph(self.right_col, "CPU Performance", "Pts", line_color="#E67E22")
        self.graph_cpu.fill_color = "#FAD7A0"
        
        self.graph_gpu = ModernGraph(self.right_col, "GPU Bandwidth", "GB/s", line_color="#27AE60")
        self.graph_gpu.fill_color = "#A9DFBF"
        
        self.graph_ram = ModernGraph(self.right_col, "RAM Bandwidth", "GB/s", line_color="#8E44AD")
        self.graph_ram.fill_color = "#D2B4DE"

        self.breakdown_frame = tk.Frame(self.right_col, bg="white")
        self.breakdown_frame.pack(side=tk.TOP, fill=tk.X, padx=30, pady=(10, 30))

        def create_score_row(parent, label):
            f = tk.Frame(parent, bg="white")
            f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=label, font=("Segoe UI", 9), bg="white", fg="#666").pack(side=tk.LEFT)
            lbl = tk.Label(f, text="---", font=("Segoe UI", 9, "bold"), bg="white", fg="#333")
            lbl.pack(side=tk.RIGHT)
            return lbl

        self.lbl_sub_coremark = create_score_row(self.breakdown_frame, "CoreMark (0-4000):")
        self.lbl_sub_whet     = create_score_row(self.breakdown_frame, "Whetstone (0-1000):")
        self.lbl_sub_gpu      = create_score_row(self.breakdown_frame, "GPU Score (0-2500):")
        self.lbl_sub_ram      = create_score_row(self.breakdown_frame, "RAM Score (0-2500):")

        tk.Frame(self.breakdown_frame, height=2, bg="#eee").pack(fill=tk.X, pady=10)

        tk.Label(self.breakdown_frame, text="TOTAL SCORE", font=("Segoe UI", 12, "bold"), 
                 bg="white", fg="#0078D7").pack(anchor="e")
        
        self.lbl_score = tk.Label(self.breakdown_frame, text="---", font=("Segoe UI", 36, "bold"), 
                                  bg="white", fg="#0078D7")
        self.lbl_score.pack(anchor="e")

        self.btn_run = tk.Button(self.breakdown_frame, text="START BENCHMARK", command=self.start_benchmark, 
                                 bg="#28a745", fg="white", font=("Segoe UI", 11, "bold"),
                                 relief="flat", cursor="hand2", padx=30, pady=5)
        self.btn_run.pack(anchor="e", pady=(10, 0))

        self.parsing_context = "none" 

    def create_detail_group(self, parent, title, items):
        frame = tk.Frame(parent, bg="white", relief="groove", bd=1)
        frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(frame, text=title, font=("Segoe UI", 9, "bold"), bg="#f5f5f5", fg="#555", anchor="w", padx=10).pack(fill=tk.X, ipady=5)
        for key, label_text in items:
            row = tk.Frame(frame, bg="white")
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=label_text, width=18, anchor="w", bg="white", fg="#666", font=("Segoe UI", 9)).pack(side=tk.LEFT)
            val = tk.Label(row, text="-", font=("Segoe UI", 9, "bold"), bg="white", fg="#333")
            val.pack(side=tk.RIGHT)
            setattr(self, key, val)


    def animate_score(self, current, target):
        if current < target:
            step = max(1, int((target - current) / 10))
            new_val = current + step
            self.lbl_score.config(text=str(new_val))
            self.root.after(20, self.animate_score, new_val, target)
        else:
            self.lbl_score.config(text=str(target))

    def get_executable_path(self):
        bundled_path = resource_path("PCBenchmark.exe")
        if os.path.exists(bundled_path):
            return bundled_path

        for path in POSSIBLE_PATHS:
            if os.path.exists(path):
                return path
        
        return None

    def start_benchmark(self):
        exe = self.get_executable_path()
        if not exe:
            err_msg = f"PCBenchmark.exe not found!\nChecked bundled path: {resource_path('PCBenchmark.exe')}"
            messagebox.showerror("Error", err_msg)
            return

        self.btn_run.config(state=tk.DISABLED, bg="#cccccc", text="RUNNING...")
        self.lbl_score.config(text="---")
        for lbl in [self.lbl_sub_coremark, self.lbl_sub_whet, self.lbl_sub_gpu, self.lbl_sub_ram]:
            lbl.config(text="---")
        
        self.results = {k: 0.0 for k in self.results}
        self.results["ram_latency"] = 1.0
        
        self.graph_cpu.clear()
        self.graph_gpu.clear()
        self.graph_ram.clear()

        for attr in self.__dict__:
            if isinstance(getattr(self, attr), tk.Label) and attr.startswith(("cpu_", "gpu_", "ram_")):
                getattr(self, attr).config(text="-")

        threading.Thread(target=self.run_process, args=(exe, "20")).start()

    def run_process(self, exe_path, iterations):
        try:
            startupinfo = None
            creation_flags = 0
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE 
                creation_flags = 0x08000000 

            process = subprocess.Popen(
                [exe_path, iterations],
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                startupinfo=startupinfo,
                creationflags=creation_flags,
                bufsize=1
            )

            for line in process.stdout:
                line = line.strip()
                if line: self.root.after(0, self.parse_line, line)

            process.wait()
            self.root.after(0, self.finish_benchmark)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.finish_benchmark)
    
    def calculate_score(self, value, max_ref, cap):
        
        ratio = value / max_ref
        
        curved_ratio = math.pow(ratio, 0.6)
        
        score = curved_ratio * cap
        return min(score, cap)


    def finish_benchmark(self):
        self.btn_run.config(state=tk.NORMAL, bg="#28a745", text="START BENCHMARK")
        
        s_core = self.calculate_score(self.results["cpu_coremark"], MAX_COREMARK, SCORE_CAP_COREMARK)
        s_whet = self.calculate_score(self.results["cpu_whetstone"], MAX_WHETSTONE, SCORE_CAP_WHET)

        bw_val = self.results["gpu_bw"]
        flops_val = self.results["gpu_flops"]
        
        s_gpu_bw = self.calculate_score(bw_val, MAX_GPU_BW, SCORE_CAP_GPU * 0.5)
        s_gpu_flops = self.calculate_score(flops_val, MAX_GPU_FLOPS, SCORE_CAP_GPU * 0.5)
        s_gpu = s_gpu_bw + s_gpu_flops

        s_ram_bw = self.calculate_score(self.results["ram_copy"], MAX_RAM_BW, SCORE_CAP_RAM * 0.7)
        s_ram_size = self.calculate_score(self.results["ram_total_gb"], MAX_RAM_SIZE, SCORE_CAP_RAM * 0.3)
        s_ram = s_ram_bw + s_ram_size

        self.lbl_sub_coremark.config(text=f"{int(s_core)}")
        self.lbl_sub_whet.config(text=f"{int(s_whet)}")
        self.lbl_sub_gpu.config(text=f"{int(s_gpu)}")
        self.lbl_sub_ram.config(text=f"{int(s_ram)}")

        total_score = int(s_core + s_whet + s_gpu + s_ram)
        self.animate_score(0, total_score)
        
        messagebox.showinfo("Done", "Benchmark Finished!")

    def parse_line(self, line):
        try:
            if line.startswith("PLOT:"):
                parts = line.split(":")
                if len(parts) >= 4:
                    comp, val = parts[1], float(parts[3])
                    if comp == "CPU": self.graph_cpu.add_point(val)
                    elif comp == "GPU": self.graph_gpu.add_point(val)
                    elif comp == "RAM": self.graph_ram.add_point(val)
                return 

            if "GPU FLOPS Benchmark" in line or "GPU:" in line: self.parsing_context = "gpu"
            elif "Total Installed RAM" in line: self.parsing_context = "ram"

            if "CPU Brand:" in line: self.cpu_brand.config(text=line.split(":", 1)[1].strip())
            if "Number of processors:" in line: self.cpu_procs.config(text=line.split(":")[1].strip())
            if "Number of cores:" in line: self.cpu_cores.config(text=line.split(":")[1].strip())
            if "Number of threads:" in line: self.cpu_threads.config(text=line.split(":")[1].strip())
            if "Processor Base Frequency:" in line: self.cpu_base_freq.config(text=line.split(":", 1)[1].strip())
            if "Maximum Frequency:" in line: self.cpu_max_freq.config(text=line.split(":", 1)[1].strip())
            
            if "Iterations/Sec" in line and "PLOT" not in line:
                val = float(line.split(":", 1)[1].strip())
                self.results["cpu_coremark"] = val
                self.cpu_coremark.config(text=f"{val:,.0f}")
                
            if "C Converted Double Precision Whetstones:" in line:
                val = float(line.split(":")[1].strip().split(" ")[0])
                self.results["cpu_whetstone"] = val
                self.cpu_whetstone.config(text=f"{val} GIPS")

            if line.startswith("GPU:"): self.gpu_brand.config(text=line.split(":", 1)[1].strip())
            if "Memory:" in line and "MB" in line and self.parsing_context == "gpu": self.gpu_mem.config(text=line.split(":", 1)[1].strip())
            if "Max Clock:" in line: self.gpu_clock.config(text=line.split(":", 1)[1].strip())
            
            if "Performance:" in line and "GFLOPS" in line:
                val = float(line.split(":")[1].strip().split(" ")[0])
                self.results["gpu_flops"] = val
                self.gpu_flops.config(text=f"{val} GFLOPS")

            if "Write bandwidth:" in line and self.parsing_context == "gpu": self.gpu_write.config(text=line.split(":", 1)[1].strip())
            if "Read bandwidth:" in line: self.gpu_read.config(text=line.split(":", 1)[1].strip())
            
            if "Read+Write bandwidth:" in line:
                val_str = line.split(":")[1].strip()
                val = float(val_str.split(" ")[0])
                self.gpu_rw.config(text=val_str)
                self.results["gpu_bw"] = val 

            if "Total Installed RAM:" in line: 
                val_str = line.split(":")[1].strip()
                self.ram_total.config(text=val_str)
                try:
                    if "GB" in val_str:
                        self.results["ram_total_gb"] = float(val_str.split(" ")[0])
                    elif "MB" in val_str:
                        self.results["ram_total_gb"] = float(val_str.split(" ")[0]) / 1024.0
                except: pass

            if "RAM Frequency:" in line: self.ram_freq.config(text=line.split(":")[1].strip())
            if "Write Bandwidth:" in line: self.ram_write.config(text=line.split(":", 1)[1].strip())
            
            if "Copy Bandwidth:" in line:
                val = float(line.split(":")[1].strip().split(" ")[0])
                self.results["ram_copy"] = val
                self.ram_copy.config(text=f"{val} GB/s")

            if "Latency:" in line:
                val = float(line.split(":")[1].strip().split(" ")[0])
                self.results["ram_latency"] = val
                self.ram_latency.config(text=f"{val} ns")

        except Exception:
            pass

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BenchmarkGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"CRASH: {e}")
        input("Press Enter...")