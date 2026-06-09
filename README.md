# MQTT-Logger

Firmware debugging log collection infrastructure — Fluent Bit + Loki + Grafana

## Architecture

| Layer | Engine | Role |
|-------|--------|------|
| MQTT Listener & Collector | Fluent Bit | Receives MQTT publishes directly, filesystem-buffered delivery to Loki |
| Log Storage | Loki | Indexes only metadata labels, minimal disk overhead |
| Visualization | Grafana | Real-time log timeline, keyword filtering |

## Quick Start

```bash
docker compose up -d
```

Grafana: http://localhost:3000 (anonymous login)

See `docker-compose.yml` for service configuration.

## Testing

Send a test log through the whole pipeline:

```bash
echo "Firmware boot OK, heap=1024" | python3 slave/slave.py --s=localhost:1883 --p=stdin --n=test1
```

Then query Grafana at http://localhost:3000 → Explore → Loki with `{job="fw_debugging"}`.

## Fluent Bit Configuration

`fluent-bit/fluent-bit.conf` — uses `Storage.type filesystem` to buffer logs to disk when Loki is unavailable, preventing data loss.

```ini
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info
    Storage.path /fluent-bit/buffer
    Storage.sync normal
    Storage.checksum off
    Storage.backlog.mem_limit 10M

[INPUT]
    Name          mqtt
    Listen        0.0.0.0
    Port          1883
    Tag           fw.logs
    Storage.type  filesystem

[OUTPUT]
    Name          loki
    Match         fw.logs
    Host          loki
    Port          3100
    Labels        job=fw_debugging
    Label_Keys    $topic
    Line_Format   json
```

## Topic Design

```
fw/{device_id}/{task_id}/{log_level}
```

Example: `fw/device_01/network_task/error`

Device reset is triggered via the `command/{device_id}/reboot` topic.

## Components

### slave (Raspberry Pi)

Reads logs from serial port and forwards them to MQTT.

```bash
python slave.py --s=server:1883 --p=/dev/ttyUSB0 --n=id1
```

For testing without a physical device, use stdin mode:

```bash
echo "test message" | python3 slave.py --s=localhost:1883 --p=stdin --n=test1
```


