"""Background loops: auto-sync printer status and stream camera frames."""
import asyncio
import base64
import logging
import os
import tempfile
import threading

logger = logging.getLogger("printer_live")

STATUS_INTERVAL = 10     # seconds between DB status polls
CAMERA_RECONNECT = 15    # seconds before reconnecting after a camera failure


async def _status_loop(db_maker):
    from printer_sync import sync_all
    while True:
        await asyncio.sleep(STATUS_INTERVAL)
        try:
            async with db_maker() as db:
                await sync_all(db)
        except Exception as e:
            logger.warning("auto-sync error: %s", e)


def _camera_thread(printer_id: int, ip: str, access_code: str, serial: str, name: str):
    """Persistent camera connection — writes frames to static/cam{id}.jpg."""
    import time
    try:
        import bambulabs_api as _bl
    except ImportError:
        logger.info("bambulabs_api not available; camera thread exiting")
        return

    out_path = f"/app/static/cam{printer_id}.jpg"
    out_dir = os.path.dirname(out_path)

    while True:
        p = None
        try:
            p = _bl.Printer(ip, access_code, serial)
            p.mqtt_start()
            p.camera_start()
            time.sleep(6)           # warmup: wait for first frame
            logger.info("camera live: %s", name)
            while True:
                frame = p.get_camera_frame()
                if frame:
                    data = bytes(frame) if isinstance(frame, (bytes, bytearray)) else None
                    if data is None:
                        try:
                            data = base64.b64decode(frame)
                        except Exception:
                            data = None
                    if data:
                        # atomic write: replace prevents partial reads by the web server
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg", dir=out_dir) as tf:
                            tf.write(data)
                        os.replace(tf.name, out_path)
                time.sleep(1.0)     # ~1 FPS
        except Exception as e:
            logger.warning("camera error (%s): %s", name, e)
        finally:
            if p is not None:
                try:
                    p.camera_stop()
                except Exception:
                    pass
                try:
                    p.mqtt_stop()
                except Exception:
                    pass
        time.sleep(CAMERA_RECONNECT)


async def start_background_tasks(db_maker):
    """Called from lifespan after DB is ready. Starts sync loop + camera threads."""
    from sqlalchemy import select
    from models import Printer

    asyncio.create_task(_status_loop(db_maker))

    async with db_maker() as db:
        result = await db.execute(select(Printer).order_by(Printer.id))
        printers = result.scalars().all()

    for p in printers:
        if not (p.ip and p.access_code and p.serial):
            continue
        t = threading.Thread(
            target=_camera_thread,
            args=(p.id, p.ip, p.access_code, p.serial, p.name),
            daemon=True,
            name=f"cam-{p.id}",
        )
        t.start()
        logger.info("camera thread started: %s", p.name)
