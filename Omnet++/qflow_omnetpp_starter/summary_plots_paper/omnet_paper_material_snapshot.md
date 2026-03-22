# OMNeT++ Paper Material Snapshot

## First 20 aggregated rows

| topology   | algorithm       |   rate |   blocking_probability |   blocking_ci95 |   mean_bottleneck_fidelity |   fidelity_ci95 |   mean_max_utilization |   util_ci95 |   mean_decision_latency_ms |   latency_ci95 |   mean_hops |   mean_distance_km |   total_runs |
|:-----------|:----------------|-------:|-----------------------:|----------------:|---------------------------:|----------------:|-----------------------:|------------:|---------------------------:|---------------:|------------:|-------------------:|-------------:|
| mesh9      | distance        |     20 |                 0.6855 |     1.53869e-16 |                   0.96113  |     0           |            0.0549112   | 9.61682e-18 |                       0.02 |    0           |      0.646  |            13.533  |            3 |
| mesh9      | keyaware        |     20 |                 0.6855 |     1.53869e-16 |                   0.962376 |     0           |            0.0550642   | 9.61682e-18 |                       0.05 |    9.61682e-18 |      0.646  |            13.533  |            3 |
| mesh9      | random          |     20 |                 0.69   |     0           |                   0.958742 |     0           |            0.0956272   | 0           |                       0.01 |    0           |      1.35   |            28.321  |            3 |
| mesh9      | ga_tcheby_proxy |     20 |                 0.682  |     0           |                   0.961091 |     1.53869e-16 |            0.055187    | 0           |                       0.5  |    0           |      0.658  |            13.796  |            3 |
| mesh9      | distance        |     50 |                 0.938  |     1.53869e-16 |                   0.948816 |     1.53869e-16 |            0.00276691  | 0           |                       0.02 |    0           |      0.1195 |             2.505  |            3 |
| mesh9      | keyaware        |     50 |                 0.938  |     1.53869e-16 |                   0.950703 |     0           |            0.00287674  | 0           |                       0.05 |    9.61682e-18 |      0.1195 |             2.505  |            3 |
| mesh9      | random          |     50 |                 0.939  |     0           |                   0.941943 |     1.53869e-16 |            0.00528836  | 1.2021e-18  |                       0.01 |    0           |      0.239  |             5.005  |            3 |
| mesh9      | ga_tcheby_proxy |     50 |                 0.949  |     0           |                   0.949916 |     1.53869e-16 |            0.00195954  | 0           |                       0.5  |    0           |      0.111  |             2.329  |            3 |
| mesh9      | distance        |    100 |                 0.9915 |     1.53869e-16 |                   0.927635 |     0           |            5.12837e-05 | 9.39142e-21 |                       0.02 |    0           |      0.0135 |             0.285  |            3 |
| mesh9      | keyaware        |    100 |                 0.9915 |     1.53869e-16 |                   0.928361 |     0           |            6.29557e-05 | 0           |                       0.05 |    9.61682e-18 |      0.0135 |             0.285  |            3 |
| mesh9      | random          |    100 |                 0.9935 |     0           |                   0.92378  |     0           |            6.93981e-05 | 0           |                       0.01 |    0           |      0.018  |             0.376  |            3 |
| mesh9      | ga_tcheby_proxy |    100 |                 0.9955 |     1.53869e-16 |                   0.9273   |     1.53869e-16 |            1.05603e-05 | 2.34786e-21 |                       0.5  |    0           |      0.007  |             0.148  |            3 |
| mesh16     | distance        |     20 |                 0.715  |     0           |                   0.958404 |     0           |            0.0385482   | 0           |                       0.02 |    0           |      0.793  |            18.5395 |            3 |
| mesh16     | keyaware        |     20 |                 0.715  |     0           |                   0.960257 |     0           |            0.0474773   | 0           |                       0.05 |    9.61682e-18 |      0.793  |            18.5395 |            3 |
| mesh16     | random          |     20 |                 0.7205 |     0           |                   0.954103 |     1.53869e-16 |            0.0630023   | 0           |                       0.01 |    0           |      1.4585 |            34.22   |            3 |
| mesh16     | ga_tcheby_proxy |     20 |                 0.7265 |     0           |                   0.960827 |     0           |            0.031701    | 0           |                       0.5  |    0           |      0.7435 |            17.4055 |            3 |
| mesh16     | distance        |     50 |                 0.9445 |     0           |                   0.935815 |     0           |            0.00206085  | 0           |                       0.02 |    0           |      0.156  |             3.6705 |            3 |
| mesh16     | keyaware        |     50 |                 0.9445 |     0           |                   0.939517 |     0           |            0.00215866  | 0           |                       0.05 |    9.61682e-18 |      0.156  |             3.6705 |            3 |
| mesh16     | random          |     50 |                 0.9465 |     0           |                   0.928822 |     1.53869e-16 |            0.00351514  | 6.01051e-19 |                       0.01 |    0           |      0.258  |             6.063  |            3 |
| mesh16     | ga_tcheby_proxy |     50 |                 0.9395 |     1.53869e-16 |                   0.94331  |     0           |            0.00236226  | 0           |                       0.5  |    0           |      0.162  |             3.8175 |            3 |

## Highlights JSON

```json
{
  "topology_highlights": [
    {
      "topology": "irregular12",
      "highest_rate": 100,
      "blocking_delta_ga_minus_keyaware": 0.0024999999999999467,
      "fidelity_delta_ga_minus_keyaware": 0.011371726190476217,
      "utilization_delta_ga_minus_keyaware": -7.159476500000001e-05,
      "latency_delta_ga_minus_keyaware_ms": 0.45
    },
    {
      "topology": "mesh16",
      "highest_rate": 100,
      "blocking_delta_ga_minus_keyaware": -0.0019999999999998908,
      "fidelity_delta_ga_minus_keyaware": -0.0003015333333333814,
      "utilization_delta_ga_minus_keyaware": 1.1140785000000002e-05,
      "latency_delta_ga_minus_keyaware_ms": 0.45
    },
    {
      "topology": "mesh9",
      "highest_rate": 100,
      "blocking_delta_ga_minus_keyaware": 0.004000000000000226,
      "fidelity_delta_ga_minus_keyaware": -0.0010606732026146037,
      "utilization_delta_ga_minus_keyaware": -5.239531999999999e-05,
      "latency_delta_ga_minus_keyaware_ms": 0.45
    }
  ]
}
```
