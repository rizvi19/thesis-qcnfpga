# Latency Plot Specification — FIG02

## Figure title
Decision latency comparison across hardware and software routing modes

## Plot type
Horizontal bar chart

## X-axis
Decision latency

## Unit
Choose one final unit only:
- ns
- us
- ms

If raw sources differ, convert before plotting.

## Bars
Required:
- QFlow hardware
- Distance
- Key-aware
- Software PMO-GA

Optional:
- normalized QFlow speedup annotation
- separate marker for measured vs derived if helpful

## Styling
- compact journal-friendly layout
- short labels
- no chart junk
- use annotation only where it helps

## Main-paper goal
Visually establish the latency advantage of the hardware decision engine.
