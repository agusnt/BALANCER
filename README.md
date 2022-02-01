# BALANCER

##  Metrics calculation from hardware counters

| Metric | Formula | Scope |
|-|-|-|
| CPI | PMCx076 / PMCx0C0 | Core |
| DMPKI | PMCx043 / (PMCx0C0 / 1000) | Core |
| MPKI | L3PMCx06 / (PMCx0C0 / 1000) | Core |
| HPKI | (PMCx043 + PMCx071 + PMCx05A) / (PMCx0C0 / 1000) | Core | 
| L3Lat | (L3PMCx90 * 16) / L3PMCx9A | CCX |
| L3Occ | QOS L3 Occupancy | Core |
| rBW | ((L3PMCx06 * 64) / 2<sup>30</sup>) / Time | Core |
