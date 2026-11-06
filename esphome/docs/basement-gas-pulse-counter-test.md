# Basement gas meter: pulse_counter migration — test guide

Test and verification steps for the `basement.yaml` change that replaced the
software gas-pulse counter with ESPHome's hardware `pulse_counter` platform.

## What changed

- Removed the `total_gas_pulses` global and the `puls` GPIO binary_sensor whose
  `on_press` lambda did `+= 0.01` per pulse (software counting, can miss pulses
  during WiFi/OTA stalls).
- Added a `pulse_counter` on the gas pin (`${binary_sensor_gas}`), counting
  falling edges in the ISR with a `100ms` `internal_filter` (hardware-level
  debounce, replacing the old `delayed_on`).
- Exposed the cumulative count via the `total:` sub-sensor
  (`sensor_gas_current_total`), with a `×0.01` filter → m³ and `restore: true`
  for reboot persistence.
- The rate sensor is `internal: true` (not published to Home Assistant; used
  only for the on/off display indicator).
- Display updated: gas-current value reads `sensor_gas_current_total`; the pulse
  activity indicator reads the rate sensor (`> 0 → "on"`).

## Behavior notes

- After flashing, the gas-current total starts at `0` (the `restore` preference
  seeds fresh; the old global value is not migrated). The absolute total in
  Home Assistant is derived from the `gas_offset` input_number via
  `sensor_template_gas`, so confirm the offset still yields the correct absolute
  reading after flashing.
- The on/off pulse indicator reflects the measured rate over a 10s window; for a
  slow meter it will usually read "off" between pulses.

## Test steps

### 1. Validate the config (no flashing)

On the Pi:

```bash
cd ~/lemonpi/docker
docker compose run --rm esphome config /config/basement.yaml
```

Expect: exits cleanly, no schema errors. In the resolved output you should see
the `pulse_counter` platform, a `total:` sensor with `unit_of_measurement: m³`
and `state_class: total_increasing`, and `project.version: 2.4.1`.

### 2. Compile (catches C++/pin errors without touching the device)

```bash
docker compose run --rm esphome compile /config/basement.yaml
```

Expect: build succeeds. Watch specifically for any "pin already in use" error.

### 3. Flash and watch logs (requires the device)

Prefer OTA since the board is deployed:

```bash
docker compose run --rm esphome run /config/basement.yaml
```

Choose OTA when prompted. After boot, watch the log stream for:

- `pulse_counter` initialization with no errors.
- The `total` sensor publishing a value every 10s.

### 4. Functional check at the meter

- Note the displayed `${gas_current}` value (and the Home Assistant entity for
  the `total` sensor).
- Let the gas meter advance, or simulate pulses by briefly shorting the sensor
  input to GND the number of times you expect.
- Confirm the total increases by `0.01 m³` per pulse. Compare against the
  physical meter reading over a known interval.

### 5. Reboot persistence check

- Note the current total, then reboot the device (power-cycle or
  `button.restart`).
- After reboot, confirm the total resumes from the saved value (not 0). This
  proves `restore: true` works.
- Note: ESPHome writes preferences periodically, so a value from the last few
  seconds before an abrupt power cut may not be saved.

### 6. Rollback if needed

```bash
cd ~/lemonpi && git checkout esphome/basement.yaml
# then re-run:
cd ~/lemonpi/docker && docker compose run --rm esphome run /config/basement.yaml
```

## Tip

Run steps 1 and 2 first. If either fails, fix the config before flashing.
