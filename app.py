import sys
import os
import time
import socket
import platform
import subprocess
import psutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QAbstractItemView, QScrollArea
)

APP = "SystemInformation"

STYLE = """
QWidget {
    background: #080e16;
    color: #dce9f5;
    font-family: "Noto Sans", sans-serif;
    font-size: 12px;
}
QMainWindow { background: #080e16; }
QTabWidget::pane {
    border: 1px solid #193345;
    border-radius: 12px;
    background: #0a131e;
    top: -1px;
}
QTabBar::tab {
    background: #0c1723;
    color: #86a5ba;
    padding: 13px 17px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected {
    background: #10372f;
    color: #45f4c1;
    border-bottom: 2px solid #00e6ae;
}
QFrame#card {
    background: #0c1723;
    border: 1px solid #1a3548;
    border-radius: 14px;
}
QLabel#brand {
    color: #35f2bc;
    font-size: 24px;
    font-weight: 800;
}
QLabel#heading {
    color: #eff9ff;
    font-size: 23px;
    font-weight: 800;
}
QLabel#section {
    color: #81dff1;
    font-size: 14px;
    font-weight: 700;
}
QLabel#metric {
    color: #38f0bd;
    font-size: 27px;
    font-weight: 800;
}
QLabel#muted, QLabel#status {
    color: #7797ac;
}
QProgressBar {
    background: #1b2b3a;
    border: none;
    border-radius: 5px;
    min-height: 9px;
    max-height: 9px;
}
QProgressBar::chunk {
    background: #18dbaa;
    border-radius: 5px;
}
QPushButton {
    background: #10352f;
    color: #49f4c2;
    border: 1px solid #1b5a4a;
    border-radius: 8px;
    padding: 9px 14px;
}
QPushButton:hover { background: #174b40; }
QLineEdit {
    background: #0c1723;
    border: 1px solid #244256;
    border-radius: 8px;
    padding: 9px;
    selection-background-color: #167d68;
}
QTableWidget {
    background: #0b1520;
    alternate-background-color: #0e1c29;
    gridline-color: #1a3040;
    border: 1px solid #1a3548;
    border-radius: 8px;
    selection-background-color: #16483e;
}
QHeaderView::section {
    background: #102332;
    color: #7edccf;
    padding: 9px;
    border: none;
}
QScrollArea { border: none; }
"""

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""

def command(args):
    try:
        p = subprocess.run(
            args, capture_output=True, text=True, timeout=3
        )
        return p.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""

def os_name():
    for line in read("/etc/os-release").splitlines():
        if line.startswith("PRETTY_NAME="):
            return line.split("=", 1)[1].strip('"')
    return platform.system()

def cpu_name():
    for line in read("/proc/cpuinfo").splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor() or "Unknown"

def fmt(n):
    n = float(n)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}"
        n /= 1024

def uptime():
    s = int(time.time() - psutil.boot_time())
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    return f"{d} days, {h} hours, {s // 60} minutes"

def card(title):
    f = QFrame()
    f.setObjectName("card")
    layout = QVBoxLayout(f)
    layout.setContentsMargins(16, 15, 16, 15)
    layout.setSpacing(9)
    label = QLabel(title)
    label.setObjectName("section")
    layout.addWidget(label)
    return f, layout

def label(text="", object_name="value"):
    w = QLabel(text)
    w.setObjectName(object_name)
    w.setWordWrap(True)
    w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return w

def progress():
    p = QProgressBar()
    p.setRange(0, 100)
    p.setTextVisible(False)
    return p

class Sparkline(QWidget):
    def __init__(self):
        super().__init__()
        self.values = []
        self.setMinimumHeight(95)

    def add(self, value):
        self.values.append(max(0, min(100, float(value))))
        self.values = self.values[-60:]
        self.update()

    def paintEvent(self, event):
        if len(self.values) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(QPen(QColor("#183447"), 1))
        for i in range(1, 4):
            y = h * i / 4
            p.drawLine(0, int(y), w, int(y))
        pen = QPen(QColor("#20e9b4"), 2)
        p.setPen(pen)
        points = []
        for i, value in enumerate(self.values):
            x = i * (w - 4) / max(1, len(self.values) - 1) + 2
            y = h - 3 - value * (h - 6) / 100
            points.append((int(x), int(y)))
        for a, b in zip(points, points[1:]):
            p.drawLine(a[0], a[1], b[0], b[1])
        p.end()

class SystemInformation(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SystemInformation")
        self.resize(1120, 780)
        self.setMinimumSize(820, 600)
        self.last_net = psutil.net_io_counters()
        self.last_time = time.monotonic()
        self.cpu_history = Sparkline()
        self.ram_history = Sparkline()

        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 18, 22, 14)
        outer.setSpacing(14)

        header = QHBoxLayout()
        brand = QLabel("◈ SystemInformation")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.host = label(socket.gethostname(), "muted")
        header.addWidget(self.host)
        refresh = QPushButton("↻  Refresh")
        refresh.clicked.connect(self.update_all)
        header.addWidget(refresh)
        outer.addLayout(header)

        self.tabs = QTabWidget()
        outer.addWidget(self.tabs, 1)
        self.build_overview()
        self.build_hardware()
        self.build_memory()
        self.build_storage()
        self.build_network()
        self.build_processes()
        self.build_system()

        self.status = label("Initializing monitor...", "status")
        outer.addWidget(self.status)
        self.setCentralWidget(root)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_all)
        self.timer.start(2000)
        self.update_all()

    def page(self, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(17, 17, 17, 17)
        layout.setSpacing(14)
        h = QLabel(title)
        h.setObjectName("heading")
        layout.addWidget(h)
        layout.addWidget(label(subtitle, "muted"))
        self.tabs.addTab(page, title)
        return page, layout

    def build_overview(self):
        page, layout = self.page(
            "Overview", "A live overview of your Linux system."
        )
        self.overview_os = label("", "heading")
        box, b = card("SYSTEM IDENTITY")
        b.addWidget(self.overview_os)
        self.overview_identity = label()
        b.addWidget(self.overview_identity)
        layout.addWidget(box)

        grid = QGridLayout()
        grid.setSpacing(12)
        layout.addLayout(grid)
        self.metrics = {}
        for col, (key, title) in enumerate([
            ("cpu", "PROCESSOR"),
            ("ram", "MEMORY"),
            ("swap", "SWAP")
        ]):
            c, cl = card(title)
            value = label("—", "metric")
            bar = progress()
            detail = label("", "muted")
            cl.addWidget(value)
            cl.addWidget(bar)
            cl.addWidget(detail)
            grid.addWidget(c, 0, col)
            self.metrics[key] = (value, bar, detail)

        c, cl = card("CPU ACTIVITY · LAST 2 MINUTES")
        cl.addWidget(self.cpu_history)
        layout.addWidget(c)
        c, cl = card("MEMORY ACTIVITY · LAST 2 MINUTES")
        cl.addWidget(self.ram_history)
        layout.addWidget(c)
        layout.addStretch()

    def build_hardware(self):
        page, layout = self.page(
            "Hardware", "Processor, graphics devices and available sensors."
        )
        c, cl = card("PROCESSOR")
        self.hw_cpu = label()
        self.hw_cores = label()
        self.hw_freq = label()
        cl.addWidget(self.hw_cpu)
        cl.addWidget(self.hw_cores)
        cl.addWidget(self.hw_freq)
        layout.addWidget(c)

        c, cl = card("GRAPHICS DEVICES")
        self.hw_gpu = label()
        cl.addWidget(self.hw_gpu)
        layout.addWidget(c)

        c, cl = card("TEMPERATURE SENSORS")
        self.hw_temp = label()
        cl.addWidget(self.hw_temp)
        layout.addWidget(c)
        layout.addStretch()

    def build_memory(self):
        page, layout = self.page(
            "Memory", "Physical memory and swap usage."
        )
        self.mem_labels = label()
        layout.addWidget(self.mem_labels)
        c, cl = card("MEMORY USAGE HISTORY")
        cl.addWidget(self.ram_history)
        layout.addWidget(c)
        layout.addStretch()

    def build_storage(self):
        page, layout = self.page(
            "Storage", "Mounted filesystems and disk capacity."
        )
        self.disk_table = QTableWidget(0, 5)
        self.disk_table.setHorizontalHeaderLabels(
            ["Device", "Mount point", "Filesystem", "Used", "Free"]
        )
        self.disk_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.disk_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.disk_table)
        layout.addStretch()

    def build_network(self):
        page, layout = self.page(
            "Network", "Interfaces and traffic counters."
        )
        self.net_speed = label("Download: —   Upload: —", "heading")
        layout.addWidget(self.net_speed)
        self.net_table = QTableWidget(0, 4)
        self.net_table.setHorizontalHeaderLabels(
            ["Interface", "IP address", "Sent", "Received"]
        )
        self.net_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.net_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.net_table)
        layout.addStretch()

    def build_processes(self):
        page, layout = self.page(
            "Processes", "Running processes sorted by CPU usage."
        )
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search process name or PID...")
        self.search.textChanged.connect(self.fill_processes)
        layout.addWidget(self.search)
        self.proc_table = QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels(
            ["PID", "Process", "CPU %", "RAM"]
        )
        self.proc_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.proc_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.proc_table.setSortingEnabled(True)
        layout.addWidget(self.proc_table)
        layout.addWidget(label(
            "Read-only process list. No processes are terminated.",
            "muted"
        ))

    def build_system(self):
        page, layout = self.page(
            "System", "Operating system, kernel and runtime information."
        )
        c, cl = card("SYSTEM INFORMATION")
        self.sys_details = label()
        cl.addWidget(self.sys_details)
        layout.addWidget(c)
        layout.addStretch()

    def set_table(self, table, rows):
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for col, value in enumerate(row):
                table.setItem(r, col, QTableWidgetItem(str(value)))
        table.setSortingEnabled(True)

    def fill_processes(self):
        query = self.search.text().lower()
        rows = []
        for p in psutil.process_iter(
            ["pid", "name", "memory_info"]
        ):
            try:
                info = p.info
                name = info.get("name") or "?"
                if query and query not in name.lower() and query not in str(info["pid"]):
                    continue
                mem = info.get("memory_info")
                rows.append((
                    info["pid"], name,
                    p.cpu_percent(None),
                    fmt(mem.rss) if mem else "N/A"
                ))
            except (psutil.Error, OSError):
                continue
        rows.sort(key=lambda row: row[2], reverse=True)
        self.set_table(self.proc_table, rows[:250])

    def update_all(self):
        try:
            cpu = psutil.cpu_percent(None)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            freq = psutil.cpu_freq()
            self.cpu_history.add(cpu)
            self.ram_history.add(mem.percent)

            values = {
                "cpu": (cpu, f"{psutil.cpu_count()} logical CPUs"),
                "ram": (mem.percent,
                        f"{fmt(mem.used)} used / {fmt(mem.total)} total"),
                "swap": (swap.percent,
                         f"{fmt(swap.used)} used / {fmt(swap.total)} total")
            }
            for key, (percent, detail) in values.items():
                value, bar, desc = self.metrics[key]
                value.setText(f"{percent:.1f}%")
                bar.setValue(round(percent))
                desc.setText(detail)

            self.overview_os.setText(os_name())
            self.overview_identity.setText(
                f"Host: {socket.gethostname()}    "
                f"Kernel: {platform.release()}    "
                f"Uptime: {uptime()}"
            )

            self.hw_cpu.setText(f"Model: {cpu_name()}")
            self.hw_cores.setText(
                f"Cores: {psutil.cpu_count(logical=False)} physical / "
                f"{psutil.cpu_count(logical=True)} logical"
            )
            self.hw_freq.setText(
                f"Frequency: {freq.current:.0f} MHz"
                if freq else "Frequency: unavailable"
            )
            self.hw_gpu.setText(
                command(["lspci"]) or "Install pciutils to inspect GPUs."
            )
            temps = psutil.sensors_temperatures()
            temp_lines = []
            for chip, entries in temps.items():
                for entry in entries:
                    if entry.current is not None:
                        temp_lines.append(
                            f"{chip} / {entry.label or 'Sensor'}: "
                            f"{entry.current:.1f} °C"
                        )
            self.hw_temp.setText(
                "\n".join(temp_lines) if temp_lines
                else "No readable temperature sensors detected."
            )

            self.mem_labels.setText(
                f"RAM total: {fmt(mem.total)}\n"
                f"Used: {fmt(mem.used)}\n"
                f"Available: {fmt(mem.available)}\n"
                f"Cached: {fmt(getattr(mem, 'cached', 0))}\n"
                f"Swap total: {fmt(swap.total)}\n"
                f"Swap used: {fmt(swap.used)}"
            )

            disks = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append((
                        part.device, part.mountpoint, part.fstype,
                        f"{usage.percent:.1f}% ({fmt(usage.used)})",
                        fmt(usage.free)
                    ))
                except (OSError, PermissionError):
                    continue
            self.set_table(self.disk_table, disks)

            now = time.monotonic()
            net = psutil.net_io_counters()
            elapsed = max(now - self.last_time, 0.001)
            down = max(0, net.bytes_recv - self.last_net.bytes_recv) / elapsed
            up = max(0, net.bytes_sent - self.last_net.bytes_sent) / elapsed
            self.net_speed.setText(
                f"↓ {fmt(down)}/s     ↑ {fmt(up)}/s"
            )
            self.last_net, self.last_time = net, now

            interfaces = psutil.net_if_addrs()
            counters = psutil.net_io_counters(pernic=True)
            net_rows = []
            for name, addresses in interfaces.items():
                ips = ", ".join(
                    a.address for a in addresses
                    if a.family == socket.AF_INET
                ) or "—"
                count = counters.get(name)
                sent = fmt(count.bytes_sent) if count else "—"
                recv = fmt(count.bytes_recv) if count else "—"
                net_rows.append((name, ips, sent, recv))
            self.set_table(self.net_table, net_rows)

            self.fill_processes()

            self.sys_details.setText(
                f"Distribution: {os_name()}\n"
                f"Kernel: {platform.release()}\n"
                f"Architecture: {platform.machine()}\n"
                f"Python: {platform.python_version()}\n"
                f"Hostname: {socket.gethostname()}\n"
                f"Boot time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(psutil.boot_time()))}\n"
                f"Uptime: {uptime()}\n"
                f"PID of this application: {os.getpid()}"
            )
            self.status.setText(
                f"● LIVE   Updated {time.strftime('%H:%M:%S')}   "
                "Refresh interval: 2 seconds"
            )
        except Exception as exc:
            self.status.setText(f"Update error: {exc}")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = SystemInformation()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
