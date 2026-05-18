"""MQTT Edge Adapter for BioOps Twin.

Simulates industrial connectivity by publishing telemetry to a public
MQTT broker (e.g., test.mosquitto.org). Includes a robust fallback
so the local simulation does not crash if the broker is unavailable.
"""

import json
import logging
import threading
from typing import Any

import paho.mqtt.client as mqtt

logger = logging.getLogger("bioops_twin.mqtt")

# Public broker for demo purposes
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_TELEMETRY = "bioops/factory1/centrifuge1/telemetry"
MQTT_TOPIC_ALERTS = "bioops/factory1/centrifuge1/alerts"

class MQTTEdgeClient:
    """Robust MQTT client for publishing telemetry."""
    
    def __init__(self) -> None:
        self.client = mqtt.Client(client_id="bioops_twin_edge", protocol=mqtt.MQTTv311)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.connected = False
        self._lock = threading.Lock()
        self._connect_async()

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: int) -> None:
        if rc == 0:
            with self._lock:
                self.connected = True
            logger.info(f"✅ MQTT connected to {MQTT_BROKER}:{MQTT_PORT}")
        else:
            logger.warning(f"⚠️ MQTT connection failed with code {rc}")

    def _on_disconnect(self, client: Any, userdata: Any, rc: int) -> None:
        with self._lock:
            self.connected = False
        logger.warning("⚠️ MQTT disconnected.")

    def _connect_async(self) -> None:
        """Connect in a background thread to avoid blocking Gradio."""
        def connect_task() -> None:
            try:
                self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
                self.client.loop_start()
            except Exception as exc:
                logger.error(f"❌ Failed to connect to MQTT Broker {MQTT_BROKER}: {exc}")
                # Fallback handled gracefully by self.connected being False

        t = threading.Thread(target=connect_task, daemon=True)
        t.start()

    def publish_telemetry(self, payload: dict[str, Any]) -> None:
        """Publish a telemetry reading to the broker."""
        with self._lock:
            if not self.connected:
                return
        try:
            self.client.publish(MQTT_TOPIC_TELEMETRY, json.dumps(payload), qos=0)
        except Exception as exc:
            logger.error(f"MQTT publish failed: {exc}")

    def publish_alert(self, alert_payload: dict[str, Any]) -> None:
        """Publish a sensor alert to the broker."""
        with self._lock:
            if not self.connected:
                return
        try:
            self.client.publish(MQTT_TOPIC_ALERTS, json.dumps(alert_payload), qos=1)
        except Exception as exc:
            logger.error(f"MQTT alert publish failed: {exc}")

# Singleton instance for easy import
mqtt_edge = MQTTEdgeClient()
