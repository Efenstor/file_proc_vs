import vapoursynth as vs
from vapoursynth import core
import functions as f

# Source
clip = core.lsmas.LWLibavSource(filename, repeat=1)

# Process
clip = core.vivtc.VFM(clip, order=0)
clip = f.fixfieldjitter(clip)
clip = core.lghost.LGhost(clip, 3, -2, 50)
clip = core.lghost.LGhost(clip, 4, 2, -50)
clip = f.denoise(clip, 8, 8, 2, 300, 400)
clip = core.asharp.ASharp(clip, 2, 16, 4)

# Output
clip.set_output()
