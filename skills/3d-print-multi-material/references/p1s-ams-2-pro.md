# P1S with one AMS 2 Pro

Checked against Bambu primary sources on 2026-11-04. Recheck model/firmware,
exact filament and installed Studio profile before a new material combination.

- One AMS 2 Pro selects four 1.75 mm spools. The P1S retains its single nozzle;
  changes require unloading/loading and appropriate flushing. Same-polymer
  colors are the simplest initial route. Four feedable filaments need not be
  mutually printable or bondable.
- The P1S connection needs the appropriate filament buffer or AMS hub, 4-pin and
  6-pin cables and PTFE route. The official switching adapter powers drying on
  P1/X1. Do not assume an ordered bare unit included the P1 upgrade accessories.
- The dryer reaches at most 65 C and provides sealed storage and moisture
  discharge. Feeding a material does not mean the dryer can fully dry it.
  Drying applies to the shared chamber: choose a cycle suitable for every
  loaded spool and material, or remove incompatible spools. Follow the exact
  filament's instructions. Air humidity is not proof of filament dryness.
- Drying during printing is printer/AMS/Studio firmware dependent. Bambu's
  release notes enable it separately for different models. Verify the P1S
  capability instead of transferring H2/P2 behavior. No automatic firmware
  update or dryer control is part of part design.
- Generic TPU, TPE, wet PVA/BVOH and unsupported fiber composites are excluded
  from the automatic feeder. `TPU for AMS` is a specific supported product,
  rated 68D; do not promise ordinary soft-TPU behavior. An external-spool soft
  component can be printed separately and assembled when appropriate.
- Bambu lists its PLA-CF, PAHT-CF and PETG-CF as specific supported composites;
  this does not approve generic CF/GF brands. This adapter requires a declared
  hardened steel nozzle and extruder gears for these abrasive materials, and
  at least a 0.4 mm nozzle. Confirm the exact filament's nozzle recommendation.
- Usable spool dimensions in the specification are 50–68 mm wide and
  197–202 mm diameter. Verify spool rigidity, edge condition and drying rating;
  a spool adapter is not automatic proof of reliable feeding.

Sources:

- [AMS 2 Pro product and P1 connection FAQ](https://bambulab-eu.myshopify.com/products/ams-2-pro)
- [Official specifications: feeder exclusions, spool sizes and drying limits](https://csm.bblcdn.com/hub/default/5802624bcf8644fe809a6541818d884f.pdf)
- [P1/X1 upgrade kit and adapter requirements](https://bambulab-eu.myshopify.com/products/ams-2-pro-upgrade-kit)
- [P1S hardware and fiber-reinforced filament guidance](https://bambulab-eu.myshopify.com/products/p1s)
- [Dedicated PLA/PETG support-interface instructions](https://bambulab-eu.myshopify.com/es-es/products/support-for-pla-petg)
- [TPU for AMS product properties](https://bambulab-eu.myshopify.com/products/tpu-for-ams)
- [Studio's model-specific dry-while-printing release notes](https://github.com/bambulab/BambuStudio/releases/tag/v02.05.03.62)
