#!/usr/bin/env python3
"""Script test RIP timer signal emission"""
import sys
import time
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from module2_rip.RIPRouter import RIPRouter
from module4_ui.RouterSignal import RouterSignal

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')

app = QApplication(sys.argv)

# Tạo signal shared
shared_signals = RouterSignal()

# Counter cho signal received
signal_count = [0]

# Hàm callback để test signal
def on_timer_update(router_id, timers_info):
    signal_count[0] += 1
    print(f"\n✓ Signal #{signal_count[0]} from {router_id}:")
    for network, info in timers_info.items():
        print(f"  {network}: metric={info['metric']}, status={info['status']}, "
              f"invalid={info['invalid_timer']}s, flush={info['flush_timer']}s")

# Kết nối signal
shared_signals.timer_updated.connect(on_timer_update)

# Tạo router với shared signal
r1 = RIPRouter("R1", "192.168.1.1", signals=shared_signals)

# Thêm route trực tiếp
r1.add_direct_route("10.0.0.0", "eth0")
r1.add_direct_route("172.16.0.0", "eth0")

# Thêm route learned (sẽ có timer)
r1.routing_table["192.168.2.0"] = {
    'metric': 1,
    'next_hop': '10.0.0.2',
    'interface': 'eth0',
    'timestamp': time.time()
}

# Khởi động RIP engine
print("Starting RIP engine...")
r1.start_rip_engine()

# Dừng sau 5 giây
def stop_test():
    r1.running = False
    print(f"\n✓ Test completed! Received {signal_count[0]} signals")
    sys.exit(0)

timer = QTimer()
timer.timeout.connect(stop_test)
timer.start(5000)

print("Waiting 5 seconds for timer signals...")
sys.exit(app.exec())
