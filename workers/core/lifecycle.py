import asyncio
import signal
import platform
import structlog


logger = structlog.get_logger()

shutdown_event = asyncio.Event()

def setup_signal_handlers():
    def handle_shutdown(signum, frame):
        logger.info("Shutdown signal received, finishing current job...", signal=signum)
        shutdown_event.set()
    signal.signal(signal.SIGINT, handle_shutdown)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, handle_shutdown)

    return shutdown_event