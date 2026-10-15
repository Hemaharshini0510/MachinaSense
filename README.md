# MachinaSense

Intelligent industrial fault detection and predictive maintenance for a 3-phase pump motor. Built solo for **Bugged Out! Round 2, PS 05: MachinaSense**.

Every alert carries its sensor evidence, a timestamp, a severity and a priority, and keeps what was measured apart from what was inferred.

## Run it

No build step, no dependencies. Open `index.html` in a browser. Everything runs client-side.

To reproduce the numbers below in a terminal (Node 16 or newer):

```
node test/evaluate.js
```

## Data and split

The telemetry is **simulated** (seeded, so every run is identical). One sample every 10 minutes for 14 days. Signals: vibration RMS, bearing-envelope vibration, winding temperature, motor current. Operating conditions: load and ambient temperature. Four fault types develop gradually (bearing wear, imbalance or misalignment, overload or winding degradation, cooling failure).

- **Training:** 16 scenarios, seeds 1 to 16. Used to fit the normal-behaviour model, choose alert thresholds and learn fault signatures.
- **Hidden test:** 24 scenarios, seeds 1001 to 1024 (6 healthy, 18 faulty). Never used for fitting or tuning. Contains noise, missing samples and a load regime change that the training data does not.

## Method

1. **Learn normal.** Each sensor is regressed on load, ambient and their lagged values, using healthy data only.
2. **Measure the gap.** Residuals are scaled to standard deviations. The scale adapts to the observed noise level, so a noisier sensor widens its own limits.
3. **Filter and persist.** Median-of-3 removes spikes, an EWMA tracks drift, missing samples are skipped, and an alert needs 4 consecutive exceedances. Alerts clear after 2 quiet hours.
4. **Rank and explain.** Severity from the worst sensor deviation: Watch from the tuned threshold, Warning from 4 sigma, Critical from 8 sigma (priorities P3, P2, P1). The pattern across sensors is matched by cosine similarity to fault signatures learned on the training set.

Baseline for comparison: static limits (mean plus c standard deviations of each raw sensor, 6 consecutive samples), with c tuned on the same training set.

## Results on the hidden test set

| Test conditions | Faults detected (static limits) | Faults detected (MachinaSense) | False alarms (static limits) | False alarms (MachinaSense) | Median time to detect (MachinaSense) | Diagnosis correct |
|---|---|---|---|---|---|---|
| Clean | 13 of 18 | 18 of 18 | 0 | 0 | 15.3 h | 18 of 18 |
| Hidden set (noise 1-2x, up to 6% missing, load change in half) | 16 of 18 | 18 of 18 | 25 | 0 | 19.5 h | 18 of 18 |
| Harsh (noise 2-3x, 5-15% missing, load change in all) | 16 of 18 | 18 of 18 | 51 | 1 | 24.5 h | 18 of 18 |

A false alarm is an alert raised before fault onset, or any alert on a healthy run. Detection time is measured from fault onset to the moment the alert is raised.

## Realistic complications handled

- **Noise and spikes:** median filter, smoothing and noise-adaptive scaling.
- **Missing samples:** random gaps and bursts are skipped, never filled with invented values.
- **Changed operating conditions:** the expected value moves with load and ambient, so a higher-duty regime does not trigger alarms. Static limits raise most of their false alarms here.

## Optional extensions included

- Explanations: per-sensor measured versus expected values, and the matched fault signature with similarity score.
- Edge footprint: about 0.5 to 1 microsecond per sample in a browser, about 64 stored values (0.25 KB as 32-bit floats), only additions and multiplications at run time.
- CSV import: run the same detector on your own file (header row, numeric sensor columns, optional `load`, `ambient` and `time` columns). The first 20 to 40 percent is treated as healthy.

## Limits

- The data is simulated and the simulator shares its structure with the detector, so these numbers show the method works on these fault models. They are not a claim about real-plant performance.
- A new operating regime far outside the healthy data needs fresh healthy data.
- Faults outside the four learned types are reported as unclassified, with the measured evidence.
- No remaining-useful-life estimate and no hardware integration.
