import socket
from celery import shared_task
from django.utils import timezone
from .models import Device, DeviceLog
from accounts.tasks import log_to_elastic_task


def check_port(ip, port, timeout=3):
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True
    except:
        return False


@shared_task
def check_devices_status():

    devices = Device.objects.all()

    for device in devices:
        is_online = check_port(device.ip_address, device.port)

        new_status = "online" if is_online else "offline"

        if new_status == device.status:
            continue

        old_status = device.status
        device.status = new_status

        if is_online:
            device.last_seen = timezone.now()

        device.save()

        # ساخت لاگ
        log = DeviceLog.objects.create(
            device=device,
            status=new_status,
            ip_address=device.ip_address,
            port=device.port,
            message=f"Device went {new_status.upper()}",
        )

        # ارسال لاگ به Elastic
        log_payload = {
            "device": device.serial_number,
            "status": new_status,
            "timestamp": timezone.now().isoformat(),
            "ip": device.ip_address,
            "port": device.port,
            "old_status": old_status,
        }

        log_to_elastic_task.delay(log_payload)

    return "Device status scan completed."
