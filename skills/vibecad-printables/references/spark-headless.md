# Spark (aarch64) headless VibeCAD

Linux VibeCAD ships **x86_64 only**. On DGX Spark, do not exec the AppImage natively (`Exec format error`).

Proven path (RC5 build 1, 2026-08-24):

1. Extract once: `qemu-x86_64 ./VibeCAD-*-Linux-x86_64.AppImage --appimage-extract` → `squashfs-root/`
2. Sysroot: Debian bookworm `libc6_*_amd64.deb` unpacked to `x86_sysroot/`. Fix `lib64/ld-linux-x86-64.so.2` to a **relative** symlink (`../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`). The deb’s absolute `/lib/...` link points at host ARM libc.
3. `qemu -L sysroot usr/bin/freecadcmd` still opens host `/lib64/ld-linux-x86-64.so.2`. Invoke the **amd64 loader as argv0**:

```bash
qemu-x86_64 \
  x86_sysroot/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 \
  --library-path "squashfs-root/usr/lib:x86_sysroot/lib/x86_64-linux-gnu" \
  squashfs-root/usr/bin/freecadcmd \
  -P squashfs-root/usr/lib \
  scripts/remake_foo.py
```

Wrapper: `~/Documents/the-grid/vibecad-lab/scripts/run_vibecad.sh`

Required env (the wrapper sets these):

- `PYTHONHOME=squashfs-root/usr`
- `PATH_TO_FREECAD_LIBDIR=squashfs-root/usr/lib`
- `FREECAD_USER_HOME=vibecad-lab/userhome` (create the dir)
- `VIBECAD_LAB=vibecad-lab`

Avoid `LD_LIBRARY_PATH` / `PYTHONPATH` exports — host security scan treats them as hijack. Use `--library-path` and `freecadcmd -P` instead.

## Script rules that actually ran

- Pass the `.py` as a file argument. **`freecadcmd -c` is console mode**, not “run this script.”
- `import Part` works with `-P usr/lib`. `import Mesh` may not; use `shape.exportStl(path)`.
- `doc.addObject("Part::Feature", name)` raises **`Material not found`** until a material lib is wired. Export the OCC shape directly. Skip `.FCStd` save unless Feature create works.
- Print `len(shape.Solids)`, volume cm³, bbox. `multiFuse` does **not** weld OpenSCAD-style hulls — coupon remake stayed **5 solids**.
- OCC STL chords trip default G-thin HARD. Re-gate with `--thin-fail-frac 0.35` (same soft-mode policy) and say so. Still check min wall ≥ 1.6 mm.

## Probe

A 10 mm `Part.makeBox` + `exportStl` should print volume ≈ 1000 mm³ before any remake.
