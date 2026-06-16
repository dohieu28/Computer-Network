from PyQt5.QtCore import pyqtSignal, QObject


class RouterSignal(QObject):
    """
    RouterSignal là một QObject dùng để định nghĩa các signal mà Router sẽ phát ra.
    Các signal này sẽ được MainWindow (Module 4) kết nối để cập nhật giao diện người dùng.
    """
    router_updated = pyqtSignal(str, dict)  # router_name, routing_table

    packet_captured = pyqtSignal(dict)  # packet_info

    # router_name, {network: {state, time_remaining}}
    timer_updated = pyqtSignal(str, dict)

    # router_name - emit mỗi 1s để refresh UI
    update_timer_tick = pyqtSignal(str)

    packet_sent = pyqtSignal(str, str)  # src_router, dst_router
