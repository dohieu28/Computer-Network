# import sys

# from PyQt5.QtWidgets import QApplication
# from module4_ui.MainWindow import MainWindow


# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     window = MainWindow()
#     window.show()

#     sys.exit(app.exec())


from module1_core import Interface, Link
from module2_rip import RIPRouter
from module4_ui import MainWindow, PacketSniffer, RouterSignal
import time

# 1. UI tạo ra Router và Cổng (Mạng ảo)
# rA = RIPRouter.RIPRouter(router_id="Router_A", ip="10.0.0.1")
# rB = RIPRouter.RIPRouter(router_id="Router_B", ip="10.0.0.2")

# intf_A = Interface.Interface(
#     name="eth0", ip="10.0.0.1", mac="AA:AA", owner_router=rA)
# intf_B = Interface.Interface(
#     name="eth0", ip="10.0.0.2", mac="BB:BB", owner_router=rB)

# rA.interfaces.append(intf_A)
# rB.interfaces.append(intf_B)

# # 2. UI nối cáp
# link_AB = Link.Link(intf_A, intf_B)

# # 3. UI bật công cụ Sniffer lên dây cáp AB
# sniffer = PacketSniffer.PacketSniffer(None)
# sniffer.start_capture(link_AB)

# # 4. Bật công tắc cho Router chạy ngầm (Bắt đầu đếm Timer)
# rA.start_rip_engine()
# rB.start_rip_engine()

# --- LUỒNG CHẠY BÊN DƯỚI SẼ TỰ ĐỘNG DIỄN RA NHƯ SAU ---
# -> rA hết giờ 30s, gọi intf_A.send(bytes_RIP)
# -> link_AB nhận được bytes_RIP
# -> link_AB gọi sniffer.analyze_bytes() (UI in ra: Đã bắt được RIPv2)
# -> link_AB gọi intf_B.receive_from_link(bytes_RIP)
# -> intf_B gọi rB.receive_bytes_from_module1()
# -> rB chạy Bellman-Ford, cập nhật Routing Table của rB
# -> rB.signals.route_updated.emit() -> UI tự động vẽ lại bảng định tuyến của rB!
# ==========================================
# 1. KHỞI TẠO HẠ TẦNG
# ==========================================
rA = RIPRouter.RIPRouter(router_id="Router_A", ip="10.0.0.1")
rB = RIPRouter.RIPRouter(router_id="Router_B", ip="10.0.0.2")

intf_A = Interface.Interface(
    name="eth0", ip="10.0.0.1", mac="AA:AA", owner_router=rA)
intf_B = Interface.Interface(
    name="eth0", ip="10.0.0.2", mac="BB:BB", owner_router=rB)

rA.interfaces.append(intf_A)
rB.interfaces.append(intf_B)

link_AB = Link.Link(intf_A, intf_B)

# Bật Sniffer
# (Lưu ý: Truyền None hoặc tham số giả nếu bạn chưa ráp UI vào theo cấu trúc đã hướng dẫn)


class MockSignalHub:
    class MockSignal:
        def emit(self, data):
            pass  # Chặn lỗi UI khi chạy console
    packet_captured = MockSignal()


sniffer = PacketSniffer.PacketSniffer(MockSignalHub())
link_AB.sniffer_callback = sniffer.analyze_bytes

# ==========================================
# 2. BƠM DỮ LIỆU BAN ĐẦU (Sửa Nguyên nhân 2)
# ==========================================
# Cấp cho Router A mạng LAN 192.168.1.0
rA.add_direct_route("192.168.1.0", "eth0")
# Cấp cho Router B mạng LAN 192.168.2.0
rB.add_direct_route("192.168.2.0", "eth0")

# ==========================================
# 3. KHỞI ĐỘNG CÁC LUỒNG
# ==========================================
rA.start_rip_engine()
rB.start_rip_engine()

# ==========================================
# 4. GIỮ CHƯƠNG TRÌNH SỐNG (Sửa Nguyên nhân 1)
# ==========================================
print("\n[HỆ THỐNG] Đang chạy mô phỏng mạng... Bấm Ctrl+C để thoát.\n")
try:
    while True:
        # Giữ luồng chính không bị tắt, mỗi giây check 1 lần
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[HỆ THỐNG] Đã tắt mô phỏng!")
