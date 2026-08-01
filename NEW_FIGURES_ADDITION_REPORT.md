# New Figures Addition Report

## Scope and outcome

Exactly five professional figures were added to the final QFlow thesis. The thesis
now contains 13 figures in total, and the existing Figures 1.1, 3.1--3.3, and
4.1--4.4 retain their original automatic numbers. The complete thesis builds to 99
pages, compared with the 92-page baseline, for a net increase of seven pages.

## Added figures

### Figure 2.1 -- Trusted-relay candidate eligibility

- Placement: Chapter 2, Section 2.4.1, immediately after Table 2.1.
- Purpose: show link-local pools, the two supplied routes, the four-unit hard check,
  the C-to-D bottleneck, and the transition from hard eligibility to soft preference.
- Source: Table 2.1 and Equations 2.3--2.4 in the thesis.
- Implementation: standalone TikZ vector PDF with solid/dashed route encoding and a
  diamond bottleneck marker.

### Figure 3.4 -- Offline training to FPGA deployment

- Placement: referenced from the full-action discussion in Section 3.5 and the
  policy-ROM inference discussion in Section 3.10; its numbered declaration is at
  the end of Section 3.17, immediately after existing Figure 3.3. This is the first
  numbering-safe location that preserves Figures 3.2 and 3.3 without manual counter
  manipulation.
- Purpose: distinguish the complete software-training action from the ratio-only
  FPGA deployment projection and show the frozen ROM/dwell artifacts.
- Source: the profile-dependent path-cost equation, fixed-point score equation,
  profile codebook, policy-ROM population, and minimum-dwell contract in Chapter 3.
- Implementation: standalone TikZ vector workflow with three bounded regions.

### Figure 3.5 -- Ring-6 experimental environment

- Placement: referenced from Section 3.12 beside the Ring-6 and trace-phase
  description; its numbered declaration follows Figure 3.4 at the end of Section
  3.17 to preserve all existing figure numbers automatically.
- Purpose: connect the 12 directed edges, normal and alternate requests, candidate
  slots, repeating phases, and registered transition order.
- Source: Sections 3.12.1--3.12.2 and the registered trace-ranges table.
- Implementation: standalone two-panel TikZ vector figure.

### Figure 3.6 -- Physical replay and exact-comparison setup

- Placement: Chapter 3, Section 3.18, immediately before Pseudocode 3.3.
- Purpose: identify the host/FPGA paths, the accepted-request-to-done measurement
  boundary, excluded latency components, and exact-comparison scale.
- Source: the physical result protocol, Section 3.18, and the retained Nexys 3
  photograph supplied in `figures/nexys_img.HEIC`.
- Implementation: standalone two-panel TikZ technical schematic with a large
  uncropped documentary photograph in panel (b). The HEIC-to-JPEG conversion preserves the full
  3751-by-3509 frame and performs no crop, recoloring, resampling, or enhancement.

### Figure 4.5 -- FPGA resource utilization across H0--H4

- Placement: referenced in Chapter 4, Section 4.9 after the resource tables; its
  numbered declaration follows existing Figure 4.4 at the end of Section 4.16 so
  Figures 4.2--4.4 remain unchanged without hard-coded numbering.
- Purpose: compare registers, LUTs, and occupied slices on separate zero-based axes
  and expose the H3-versus-H4 mapping trade-off.
- Source: exact post-route counts in Table 4.5, retained in
  `figures/new/resource_utilization_h0_h4.csv`.
- Implementation: standalone PGFPlots vector PDF with three aligned panels and
  exact labels read from the retained CSV.

## Editable and generated artifacts

The editable sources, common styling, deterministic build script, resource CSV, and
generated PDFs are stored under `figures/new/`. The five generated figure PDFs are:

- `trusted_relay_candidate_example.pdf`
- `training_to_fpga_deployment.pdf`
- `ring6_environment.pdf`
- `physical_replay_setup.pdf`
- `resource_utilization_h0_h4.pdf`

## Quality and integrity checks

- Built all standalone figures with XeLaTeX and rebuilt the complete thesis through
  the existing XeLaTeX--BibTeX--XeLaTeX--XeLaTeX sequence.
- Inspected each standalone vector PDF and each integrated thesis page at 144--180
  dpi, including a grayscale rendering of all five new figures.
- Verified readable labels, aligned arrows, page margins, caption placement, and the
  absence of overlap, clipping, or unnecessary blank pages.
- Verified that the List of Figures contains exactly Figure 2.1, Figures 3.4--3.6,
  and Figure 4.5 in addition to the eight existing entries.
- Verified 13 unique figure labels, no undefined references, no duplicate labels,
  and no overfull boxes in the final LaTeX log.
- Confirmed that no existing figure source or image was edited, replaced, cropped,
  recolored, or removed by this task.
- Confirmed that no existing equation or table was changed.
- Confirmed that no numerical result, experimental claim, or scientific scope was
  changed; only figure captions and the minimum reference prose were added.

## Final totals

- Added figures: 5
- Final figure count: 13
- Baseline PDF page count: 92
- Final PDF page count: 99
- Page-count change: +7
