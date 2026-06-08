from PyQt5.QtCore import pyqtSignal, QObject


class RouterSignal(QObject):
    """
    RouterSignal là một QObject dùng để định nghĩa các signal mà Router sẽ phát ra.
    Các signal này sẽ được MainWindow (Module 4) kết nối để cập nhật giao diện người dùng.
    """
    router_updated = pyqtSignal(str, dict)  # router_name, routing_table

    packet_captured = pyqtSignal(dict)  # packet_info

    # # Signal khi có gói tin mới được nhận từ Module 1 (Interface)
    # # (interface_name, neighbor_ip, raw_bytes)
    # packet_received = pyqtSignal(str, str, bytes)

    # # Signal khi bảng định tuyến được cập nhật
    # routing_table_updated = pyqtSignal(dict)  # routing_table

    # # Signal khi có sự kiện quan trọng khác (ví dụ: lỗi, trạng thái thay đổi)
    # event_occurred = pyqtSignal(str)  # event_description
