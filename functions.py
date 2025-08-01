# FUNCTIONS.PY by Efenstor
# Modified in July 2025

import vapoursynth as vs
from vapoursynth import core
import functools

#-------------
# TVRange
#-------------
# Requirements: none

def tvrange(clip):

	clip = core.std.Levels(clip, min_in=0, max_in=255, min_out=16, max_out=235,
			planes=0)
	clip = core.std.Levels(clip, min_in=0, max_in=255, min_out=16, max_out=240,
			planes=[1,2])

	return clip

#-------------
# FullRange
#-------------
# Requirements: none

def fullrange(clip):

	clip = core.std.Levels(clip, min_in=16, max_in=235, min_out=0, max_out=255,
			planes=0)
	clip = core.std.Levels(clip, min_in=16, max_in=240, min_out=0, max_out=255,
			planes=[1,2])

	return clip

#------
# IVTC
#------
# Requirements: vivtc

def ivtc(clip):

	clip = core.vivtc.VFM(clip=clip, order=1, mode=0, micmatch=0)
	clip = core.vivtc.VDecimate(clip=clip)

	return clip


#---------
# Denoise
#---------
# recalc: number of recalculations (>0; e.g. for blksize=32 and recalc=3 block
#         sizes will be 32,16,8,4 (the last three are the recalculations); for
#         blksize=64 and recalc=1 those will be 32 and 16; etc.)
# Requirements: MVTools or MVTools-Float

def denoise(clip, blksizeX=8, blksizeY=8, overlap=2, thsad=200, thsadc=400,
		ext_super=None, recalc=0):

	if blksizeX>2: overlapX = int(blksizeX/overlap)
	else: overlapX=0
	if blksizeY>2: overlapY = int(blksizeY/overlap)
	else: overlapY=0

	if ext_super==None:
		sup = core.mv.Super(clip)
	else:
		sup = ext_super

	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
	mvbw2 = core.mv.Analyse(sup, isb=True, delta=2, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
	mvfw2 = core.mv.Analyse(sup, isb=False, delta=2, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
	mvbw3 = core.mv.Analyse(sup, isb=True, delta=3, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
	mvfw3 = core.mv.Analyse(sup, isb=False, delta=3, overlap=overlapX,
			overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)

	# do recalculations
	for r in range(0, recalc):
		blksizeX = blksizeX>>1
		if blksizeX<4: break
		blksizeY = blksizeY>>1
		if blksizeY<4: break
		overlapX = int(blksizeX/overlap)
		overlapY = int(blksizeY/overlap)
		mvbw1 = core.mv.Recalculate(sup, mvbw1, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
		mvfw1 = core.mv.Recalculate(sup, mvfw1, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
		mvbw2 = core.mv.Recalculate(sup, mvbw2, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
		mvfw2 = core.mv.Recalculate(sup, mvfw2, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
		mvbw3 = core.mv.Recalculate(sup, mvbw3, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)
		mvfw3 = core.mv.Recalculate(sup, mvfw3, overlap=overlapX,
				overlapv=overlapY, blksize=blksizeX, blksizev=blksizeY)

	# which planes are to process
	if thsad==0:
		plane = 3
	elif thsadc==0:
		plane = 0
	else:
		plane = 4

	# process
	clip = core.mv.Degrain3(clip, sup, mvbw1, mvfw1, mvbw2, mvfw2, mvbw3, mvfw3,
			thsad=thsad, thsadc=thsadc, plane=plane)

	return clip


#---------
# FlowFPS
#---------
# Requirements: MVTools or MVTools-Float

def flowfps(clip, num=60000, den=1001, blksize=8, keepfps=False):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	overlap = int(blksize/2)

	sup = core.mv.Super(clip, pel=2)
	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=overlap,
			blksize=blksize)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=overlap,
			blksize=blksize)
	clip = core.mv.FlowFPS(clip, sup, mvbw1, mvfw1, num=num, den=den)

	if keepfps:
		clip = core.std.AssumeFPS(clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#----------
# FlowFPS2
#----------
# Requirements: MVTools or MVTools-Float

def flowfps2(clip, num=60000, den=1001, blksizeX=32, blksizeY=32, recalc=3, overlap=2, keepfps=False):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	# analyze
	bsX = blksizeX
	bsY = blksizeY
	if bsX>2: olX = int(bsX/overlap)
	else: olX = 0
	if bsY>2: olY = int(bsY/overlap)
	else: olY = 0
	sup = core.mv.Super(clip)
	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	# do recalculations
	for r in range(0, recalc):
		bsX = bsX>>1
		if bsX<4: break
		bsY = bsY>>1
		if bsY<4: break
		olX = int(bsX/overlap)
		olY = int(bsY/overlap)
		mvbw1 = core.mv.Recalculate(sup, mvbw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvfw1 = core.mv.Recalculate(sup, mvfw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)

	# process
	clip = core.mv.FlowFPS(clip, sup, mvbw1, mvfw1, num=num, den=den)

	if keepfps:
		clip = core.std.AssumeFPS(clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#---------
# AddBlur
#---------
# Requirements: MVTools or MVTools-Float

def addblur2(clip, amount, blksize):

	overlap = int(blksize/2)

	sup = core.mv.Super(clip, pel=2)

	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=overlap,
			blksize=blksize)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=overlap,
			blksize=blksize)
	clip = core.mv.FlowBlur(clip, sup, mvbw1, mvfw1, blur=amount)

	return clip


#----------
# AddBlur2
#----------
# Requirements: MVTools or MVTools-Float

def addblur2(clip, amount=50, blksizeX=32, blksizeY=32, recalc=3, overlap=2):

	# analyze
	bsX = blksizeX
	bsY = blksizeY
	if bsX>2: olX = int(bsX/overlap)
	else: olX = 0
	if bsY>2: olY = int(bsY/overlap)
	else: olY = 0
	sup = core.mv.Super(clip)
	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	# do recalculations
	for r in range(0, recalc):
		bsX = bsX>>1
		if bsX<4: break
		bsY = bsY>>1
		if bsY<4: break
		olX = int(bsX/overlap)
		olY = int(bsY/overlap)
		mvbw1 = core.mv.Recalculate(sup, mvbw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvfw1 = core.mv.Recalculate(sup, mvfw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)

	# process
	clip = core.mv.FlowBlur(clip, sup, mvbw1, mvfw1, blur=amount)

	return clip


#-------------
# SRMDSharpen
#-------------
# Requirements: SRMD

def srmdsharpen(clip, amount=.25, noise_level=3, range=1):

	# Convert format to RGBS and downscale
	orig_format = clip.format
	orig_width = clip.width
	orig_height = clip.height
	new_width = int(clip.width/(1+amount)+.5)
	new_height = int(clip.height/(1+amount)+.5)
	clip = core.resize.Spline36(clip, format=vs.RGBS, matrix_in_s="709",
			range=range, width=new_width, height=new_height)

	# Upscale
	clip = core.srmdnv.SRMD(clip, scale=2, noise=noise_level)

	# Back to original size
	clip = core.resize.Spline36(clip, format=orig_format, matrix_s="709",
			width=orig_width, height=orig_height)

	return clip


#--------------------
# NeuralUpscale
# method: 0 = SRMD
#		 1 = waifu
#		 2 = RealSR
# models for waifu:
#	0 = upconv_7_anime_style_art_rgb
#	1 = upconv_7_photo
#	2 = cunet (For 2D artwork. Slow, but better quality.)
# models for RealSR:
#	0 = models-DF2K
#	1 = models-DF2K_JPEG
# noise:
#	SRMD = -1..10
#	waifu = -1..3
#--------------------
# Requirements: SRMD, Waifu2x NCNN Vulkan, RealSR

def neuralupscale(clip, method=0, model=1, noise=-1):

	orig_format = clip.format
	clip = core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709")

	if method==0:
		clip = core.srmdnv.SRMD(clip, noise=noise)
	elif method==1:
		clip = core.w2xnvk.Waifu2x(clip, model=model, noise=noise)
	elif method==2:
		clip = core.rsnv.RealSR(clip, model=model)

	clip = core.resize.Bicubic(clip, format=orig_format, matrix_s="709")
	return clip


#----------
# RIFE
# keepfps=True with factornum=2 produces the x2 slowmo effect
# model:
#  0 = rife
#  1 = rife-HD
#  2 = rife-UHD
#  3 = rife-anime
#  4 = rife-v2
#  5 = rife-v2.3
#  6 = rife-v2.4
#  7 = rife-v3.0
#  8 = rife-v3.1
#  9 = rife-v3.9 (ensemble=False / fast=True)
#  10 = rife-v3.9 (ensemble=True / fast=False)
#  11 = rife-v4 (ensemble=False / fast=True)
#  12 = rife-v4 (ensemble=True / fast=False)
#  13 = [rife-v4.1](https://github.com/mirrorsysu/rife-ncnn-vulkan/tree/model_4_1) (ensemble=False / fast=True)
#  14 = rife-v4.1 (ensemble=True / fast=False)
#  15 = rife-v4.2 (ensemble=False / fast=True)
#  16 = rife-v4.2 (ensemble=True / fast=False)
#  17 = rife-v4.3 (ensemble=False / fast=True)
#  18 = rife-v4.3 (ensemble=True / fast=False)
#  19 = rife-v4.4 (ensemble=False / fast=True)
#  20 = rife-v4.4 (ensemble=True / fast=False)
#  21 = rife-v4.5 (ensemble=False)
#  22 = rife-v4.5 (ensemble=True)
#  23 = rife-v4.6 (ensemble=False)
#  24 = rife-v4.6 (ensemble=True)
#  25 = rife-v4.7 (ensemble=False)
#  26 = rife-v4.7 (ensemble=True)
#  27 = rife-v4.8 (ensemble=False)
#  28 = rife-v4.8 (ensemble=True)
#  29 = rife-v4.9 (ensemble=False)
#  30 = rife-v4.9 (ensemble=True)
#  31 = rife-v4.10 (ensemble=False)
#  32 = rife-v4.10 (ensemble=True)
#  33 = rife-v4.11 (ensemble=False)
#  34 = rife-v4.11 (ensemble=True)
#  35 = rife-v4.12 (ensemble=False)
#  36 = rife-v4.12 (ensemble=True)
#  37 = rife-v4.12-lite (ensemble=False)
#  38 = rife-v4.12-lite (ensemble=True)
#  39 = rife-v4.13 (ensemble=False)
#  40 = rife-v4.13 (ensemble=True)
#  41 = rife-v4.13-lite (ensemble=False)
#  42 = rife-v4.13-lite (ensemble=True)
#  43 = rife-v4.14 (ensemble=False)
#  44 = rife-v4.14 (ensemble=True)
#  45 = rife-v4.14-lite (ensemble=False)
#  46 = rife-v4.14-lite (ensemble=True)
#  47 = rife-v4.15 (ensemble=False)
#  48 = rife-v4.15 (ensemble=True)
#  49 = rife-v4.15-lite (ensemble=False)
#  50 = rife-v4.15-lite (ensemble=True)
#  51 = rife-v4.16-lite (ensemble=False)
#  52 = rife-v4.16-lite (ensemble=True)
#  53 = rife-v4.17 (ensemble=False)
#  54 = rife-v4.17 (ensemble=True)
#  55 = rife-v4.17-lite (ensemble=False)
#  56 = rife-v4.17-lite (ensemble=True)
#  57 = rife-v4.18 (ensemble=False)
#  58 = rife-v4.18 (ensemble=True)
#  59 = rife-v4.19-beta (ensemble=False)
#  60 = rife-v4.19-beta (ensemble=True)
#  61 = rife-v4.20 (ensemble=False)
#  62 = rife-v4.20 (ensemble=True)
#  63 = rife-v4.21 (ensemble=False)
#  64 = rife-v4.22 (ensemble=False)
#  65 = rife-v4.22-lite (ensemble=False)
#  66 = rife-v4.23-beta (ensemble=False)
#  67 = rife-v4.24 (ensemble=False)
#  68 = rife-v4.24 (ensemble=True)
#  69 = rife-v4.25 (ensemble=False)
#  70 = rife-v4.25-lite (ensemble=False)
#  71 = rife-v4.25-heavy (ensemble=False)
#  72 = rife-v4.26 (ensemble=False)
#  73 = rife-v4.26-large (ensemble=False)
# sudo's experimental custom models (only works with 2x)
#  74 = sudo_rife4 (ensemble=False / fast=True)
#  75 = sudo_rife4 (ensemble=True / fast=False)
#  76 = sudo_rife4 (ensemble=True / fast=True)
#----------
# Requirements: RIFE

def rife(clip, model=73, factornum=2, factorden=1, fpsnum=60000, fpsden=1001,
		usefactor=True, keepfps=False, uhd=False):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den
	orig_fmt = clip.format
	if orig_fmt!=vs.RGBS:
			clip = core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709")
	if usefactor==True:
		clip = core.rife.RIFE(clip, model=model, factor_num=factornum,
				factor_den=factorden, uhd=uhd)
	else:
	  clip = core.rife.RIFE(clip, model=model, fps_num=fpsnum, fps_den=fpsden,
	  		uhd=uhd)
	if orig_fmt!=vs.RGBS:
			clip = core.resize.Bicubic(clip, format=orig_fmt, matrix_s="709")
	if keepfps==True:
			clip = core.std.AssumeFPS(clip=clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#-----------------
# FixFieldJitter
#-----------------
# Requirements: znedi3, MVTools or MVTools-Float

def fixfieldjitter(clip, blksize=4, overlap=2, thsad=300, tff=True,
		deinterlace=False):

	# Separate fields (bob)
	if tff==True:
		nnf = 3
	else:
		nnf = 2
	clip = core.znedi3.nnedi3(clip, field=nnf)

	# Analyse
	sup = core.mv.Super(clip, pel=2)
	vec = core.mv.Analyse(sup, isb=False, delta=1, blksize=blksize,
			overlap=overlap)

	# Compensate
	clip = core.mv.Compensate(clip=clip, super=sup, vectors=vec, thsad=thsad)

	# Restore the interlaced frame
	#separated = core.std.SeparateFields(clip, tff=tff)
	woven = core.std.DoubleWeave(clip, tff=tff)
	woven = core.resize.Bilinear(woven, width=woven.width, height=woven.height/2)
	woven = core.std.SelectEvery(woven, 2, 0)

	# Deinterlace
	if deinterlace==True:
		clip = core.znedi3.nnedi3(woven, field=0)
	else:
		clip = woven

	return clip


#----------------
# RestoreDetails
#----------------
# Requirements: MVTools or MVTools-Float

def restoredetails(clip, blksize=8, thsad=200, skip_upscale=False):

	# Upscale
	if skip_upscale==False:
		clip = core.resize.Spline36(clip=clip, width=int(clip.width*2),
			height=int(clip.height*2))

	# Analyze
	overlap = int(blksize/2)
	sup = core.mv.Super(clip, pel=2)
	mvbw4 = core.mv.Analyse(sup, isb=True, delta=4, blksize=blksize,
			overlap=overlap)
	mvbw3 = core.mv.Analyse(sup, isb=True, delta=3, blksize=blksize,
			overlap=overlap)
	mvbw2 = core.mv.Analyse(sup, isb=True, delta=2, blksize=blksize,
			overlap=overlap)
	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, blksize=blksize,
			overlap=overlap)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, blksize=blksize,
			overlap=overlap)
	mvfw2 = core.mv.Analyse(sup, isb=False, delta=2, blksize=blksize,
			overlap=overlap)
	mvfw3 = core.mv.Analyse(sup, isb=False, delta=3, blksize=blksize,
			overlap=overlap)
	mvfw4 = core.mv.Analyse(sup, isb=False, delta=4, blksize=blksize,
			overlap=overlap)

	# Compensate
	mvcbw4 = core.mv.Compensate(clip=clip, super=sup, vectors=mvbw4,
			thsad=thsad)
	mvcbw3 = core.mv.Compensate(clip=clip, super=sup, vectors=mvbw3,
			thsad=thsad)
	mvcbw2 = core.mv.Compensate(clip=clip, super=sup, vectors=mvbw2,
			thsad=thsad)
	mvcbw1 = core.mv.Compensate(clip=clip, super=sup, vectors=mvbw1,
			thsad=thsad)
	mvcfw1 = core.mv.Compensate(clip=clip, super=sup, vectors=mvfw1,
			thsad=thsad)
	mvcfw2 = core.mv.Compensate(clip=clip, super=sup, vectors=mvfw2,
			thsad=thsad)
	mvcfw3 = core.mv.Compensate(clip=clip, super=sup, vectors=mvfw3,
			thsad=thsad)
	mvcfw4 = core.mv.Compensate(clip=clip, super=sup, vectors=mvfw4,
			thsad=thsad)

	# Merge frames
	mrg1 = core.std.Merge(mvcbw4, mvcbw3, 0.5)
	mrg2 = core.std.Merge(mvcbw2, mvcbw1, 0.5)
	mrg3 = core.std.Merge(mvcfw1, mvcfw2, 0.5)
	mrg4 = core.std.Merge(mvcfw3, mvcfw4, 0.5)
	mrgf1 = core.std.Merge(mrg1, mrg2, 0.5)
	mrgf2 = core.std.Merge(mrg3, mrg4, 0.5)
	clip = core.std.Merge(mrgf1, mrgf2, 0.5)

	return clip


#----------
# Slowdown
#----------
# Requirements: none

def slowdown(clip, transition):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	frameA = clip
	frameB = core.std.DeleteFrames(clip, 0)
	if transition==0:
		frameT = frameA
	else:
		frameT = core.std.Merge(frameA, frameB, transition)
	clip = core.std.Interleave(clips=[frameA,frameT])
	clip = core.std.AssumeFPS(clip=clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#----------
# SpeedUp
#----------
# Requirements: none

def speedup(clip, transition):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	frameA = core.std.SelectEvery(clip, 2, 0)
	frameB = core.std.SelectEvery(clip, 2, 1)
	if transition==0:
		clip = frameA
	elif transition==1:
		clip = frameB
	else:
		clip = core.std.Merge(frameA, frameB, transition)
	clip = core.std.AssumeFPS(clip=clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#--------
# Strobe
#--------
# Requirements: none

def strobe(clip, every=4, transition=0):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	frameA = core.std.SelectEvery(clip, every, 0)
	if transition>0:
		frameB = core.std.SelectEvery(clip, every, 1)
		clip = core.std.Merge(frameA, frameB, transition)
	else: clip = frameA
	clip = core.std.Interleave(clips=[clip for _ in range(every)])
	clip = core.std.AssumeFPS(clip=clip, fpsnum=src_fpsnum, fpsden=src_fpsden)

	return clip


#-----------
# FrameBlur
#-----------
# Requirements: none

def frameblur(clip, transition):

	frameA = clip
	frameB = core.std.DeleteFrames(clip, 0)
	clip = core.std.Merge(frameA, frameB, transition)

	return clip


#----------
# Debarrel
#----------
# Requirements: vcmove

def debarrel(clip):

	# Canon HF100 with Raynox x0.3 on with the 37mm-37mm ring
	clip = core.vcmove.DeBarrel(clip=clip, a=0.005, b=0.009, c=0.085)

	# Crop debarrel border leftovers
	new_height = 1073	# just as much as needed
	old_width = clip.width
	old_height = clip.height
	aspect = old_width/old_height
	new_width = int(new_height*aspect+.5)
	new_left = int((old_width-new_width)/2+.5)
	new_top = int((old_height-new_height)/2+.5)
	clip = core.std.CropAbs(clip, new_width, new_height, new_left, new_top)
	clip = core.resize.Spline36(clip, old_width, old_height)

	return clip


#---------
# DeCanon
#---------
# Removes residual interlacing and block artifacts after IVTC, was made
# specifically for 24p video produced by the old Canon Vixia camcorders

# Requirements: MVTools or MVTools-Float, Deblock

def decanon(clip, ml=40, quant=40, skip_decomb=False):

	overlap = 2

	if skip_decomb==False:
	    clip = core.vinverse.Vinverse(clip=clip)
	sup = core.mv.Super(clip)
	mvfw = core.mv.Analyse(sup, isb=False, overlap=overlap)
	mask = core.mv.Mask(clip=clip, vectors=mvfw, kind=1, ml=ml, gamma=2.0)
	deblock = core.deblock.Deblock(clip=clip, quant=quant)
	clip = core.std.MaskedMerge(clip, deblock, mask)

	return clip


#---------
# Deblock
# method: motion masking method
#   0 = MVTools Mask
#   1 = MotionMask
#   2 = DCT difference
# blksize, ml, thscd1, thscd2: parameters for method 0
# th1, th2, width, softness: parameters for methods >0
# tht: only for method 1
#---------
# Requirements: DeblockPP7, MVTools or MVTools-Float, MotionMask

def deblock(clip, qp=8.0, mode=0, method=0, blksize=8, ml=16.0,
		thscd1=500, thscd2=200, th1=63, th2=127, tht=127, width=4, softness=4,
		show_mask=False):

	# Deblock
	deblock = core.pp7.DeblockPP7(clip, qp=qp, mode=mode)

	# Create mask
	if method==0:
		# MVTools Mask
		overlap = int(blksize/2)
		sup = core.mv.Super(clip)
		mvfw = core.mv.Analyse(sup, isb=False, blksize=blksize, overlap=overlap)
		mask = core.mv.Mask(clip=clip, vectors=mvfw, kind=1, ml=ml, gamma=1.0,
				thscd1=thscd1, thscd2=thscd2)
	elif method==1:
		# MotionMask
		mask = core.motionmask.MotionMask(clip=clip, th1=[th1,th1,th1],
				th2=[th2,th2,th2], tht=tht, sc_value=255)
	elif method==2:
		# DCT difference
		dct = core.dctf.DCTFilter(clip=clip, factors=[1,1,0,0,0,0,0,0], planes=[0])
		mask = core.std.MakeDiff(clipa=clip, clipb=dct, planes=[0])
		mask = core.std.Levels(mask, min_in=th1, max_in=th2, min_out=0,
				max_out=255, planes=[0])

	# Process mask
	if method>0:
		for i in range(0, width):
			mask = core.std.Maximum(mask)
		if softness>0:
			mask = core.std.BoxBlur(mask, hradius=softness, hpasses=2,
					vradius=softness, vpasses=2)

	# Show mask
	if show_mask==True:
		return mask

	# Merge
	clip = core.std.MaskedMerge(clip, deblock, mask)
	return clip


#--------------
# Deaberration
#--------------
# For Olympus OM-D Mark III (F7.0-9.0) + Olympus M.Zuiko 17mm F1.8 +
# Raynox x0.66 HD + 46-52mm ring: r_size=1.000, g_size=1.002, b_size=1.004

# For Canon HF100 with Raynox x0.3 with the 37mm-37mm ring:
# r_size=1.002, g_size=1.002, b_size=1.000

# Requirements: none

def deaberration(clip, r_size=1.000, g_size=1.002, b_size=1.004):

	# Convert to RGB
	orig_fmt = clip.format
	if orig_fmt != vs.RGBS:
		clip = core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709")

	# Extract planes
	r = core.std.ShufflePlanes(clips=clip, planes=0, colorfamily=vs.GRAY)
	g = core.std.ShufflePlanes(clips=clip, planes=1, colorfamily=vs.GRAY)
	b = core.std.ShufflePlanes(clips=clip, planes=2, colorfamily=vs.GRAY)

	# Enlarge certain planes
	if r_size > 1:
		new_width = int(clip.width*r_size+.5)
		new_height = int(clip.height*r_size+.5)
		r = core.resize.Spline36(clip=r, width=new_width, height=new_height)
		r = core.std.CropAbs(clip=r, width=clip.width, height=clip.height,
				left=int((new_width-clip.width)/2+.5),
				top=int((new_height-clip.height)/2+.5))
	if g_size > 1:
		new_width = int(clip.width*g_size+.5)
		new_height = int(clip.height*g_size+.5)
		g = core.resize.Spline36(clip=g, width=new_width, height=new_height)
		g = core.std.CropAbs(clip=g, width=clip.width, height=clip.height,
				left=int((new_width-clip.width)/2+.5),
				top=int((new_height-clip.height)/2+.5))
	if b_size > 1:
		new_width = int(clip.width*b_size+.5)
		new_height = int(clip.height*b_size+.5)
		b = core.resize.Spline36(clip=b, width=new_width, height=new_height)
		b = core.std.CropAbs(clip=b, width=clip.width, height=clip.height,
				left=int((new_width-clip.width)/2+.5),
				top=int((new_height-clip.height)/2+.5))

	# Combine planes
	clip = core.std.ShufflePlanes(clips=[r,g,b], planes=[0,0,0],
			colorfamily=vs.RGB)

	# Convert back
	if orig_fmt != vs.RGBS:
		clip = core.resize.Bicubic(clip, format=orig_fmt, matrix_s="709")

	return clip


#-------------
# UnsharpMask
#-------------
# Requirements: none

def unsharpmask(clip, strength=1, hradius=1, vradius=1, passes=2, planes=[0]):

	blur = core.std.BoxBlur(clip, planes=planes, hradius=hradius,
		vradius=vradius, hpasses=passes, vpasses=passes)
	diff = core.std.MakeDiff(clip, blur, planes=planes)
	sharp = core.std.MergeDiff(clip, diff, planes=planes)
	if strength<1: clip = core.std.Merge(clip, sharp, strength)
	else: clip = sharp

	return clip


#---------
# Sharpen
#---------
# strength: 0..1
# Requirements: none

def sharpen(clip, strength=1, planes=[0]):

	sh = core.std.Convolution(clip, matrix=[0, -1, 0, -1, 5, -1, 0, -1, 0], planes=planes)
	clip = core.std.Merge(clip, sh, strength)

	return clip


#--------
# DeHalo
#--------
# You can use show_mask to extract mask, then do some additional processing on
# the filtered areas, then use ext_mask to reuse it

# Requirements: TBilateral, AddGrain

def dehalo(clip, edge_gamma=0.7, hl_th=63, offset=1, halo_width=12,
		softness=8, diameter=5, sdev=2, idev=6, planes=[0], grain_l=0,
		grain_c=0, grain_hcorr=0, grain_vcorr=0, show_mask=False,
		show_hl=False, show_filtered=False, ext_mask=None):

	if ext_mask==None:

		# detect edges
		mask = core.std.Sobel(clip, planes)
		mask = core.std.Levels(mask, gamma=edge_gamma, planes=planes)

		# produce the halo mask
		hmask = mask
		for i in range(0, halo_width):
			hmask = core.std.Maximum(hmask, planes=planes)

		# subtract the safe areas
		smask = mask
		if offset!=0:
			if offset>0:
				for i in range(0, offset):
					smask = core.std.Maximum(smask, planes=planes)
			else:
				for i in range(0, -offset):
					smask = core.std.Minimum(smask, planes=planes)
		mask = core.std.Expr([hmask, smask], "x y -")

		# subtract the hightlight areas from the halo areas
		hlmask = core.std.BinarizeMask(clip, threshold=hl_th, planes=planes)
		if show_hl==True: return hlmask
		mask = core.std.Expr([mask, hlmask], "x y -")

		# soften the mask
		if softness>0:
			mask = core.std.BoxBlur(mask, planes, softness, 2, softness, 2)

		# show mask
		if show_mask==True: return mask

	else:
		# use external mask
		mask = ext_mask

	# filter
	if show_filtered==False:
		filtered = core.tbilateral.TBilateral(clip, diameter=diameter,
				sdev=sdev, idev=idev, planes=planes)
	else:
		filtered = core.std.BlankClip(clip, color=[255, 0, 0])

	# add grain
	if grain_l > 0 or grain_c > 0:
		filtered = core.grain.Add(filtered, var=grain_l, uvar=grain_c,
			hcorr=grain_hcorr, vcorr=grain_vcorr)

	# merge
	clip = core.std.MaskedMerge(clip, filtered, mask, planes=planes)

	return clip


#----------
# Denoise2
#----------
def denoise2(clip, blksizeX=8, blksizeY=8, overlap=2, thsad=300, thsadc=300,
			edges_thsad=1500, edges_thsadc=1500, edges_threshold=63,
			edges_width=3, edges_softness=3, show_mask=False):

	mask = core.std.Sobel(clip)
	mask = core.std.BinarizeMask(mask, threshold=edges_threshold)

	hmask = mask
	for i in range(0, edges_width):
		hmask = core.std.Maximum(hmask)
	if edges_softness>0:
		mask = core.std.BoxBlur(hmask, hradius=edges_softness, hpasses=2,
				vradius=edges_softness, vpasses=2)
	else:
		mask = hmask

	if show_mask==True: return mask

	sup = core.mv.Super(clip)
	normal = denoise(clip, blksizeX, blksizeY, overlap, thsad, thsadc,
		ext_super=sup)
	edges = denoise(clip, blksizeX, blksizeY, overlap, edges_thsad,
			edges_thsadc, ext_super=sup)
	clip = core.std.MaskedMerge(normal, edges, mask)

	return clip


#----------
# Denoise3
#----------
# Parameters:
# blksizeX, blksizeY: block size for normal areas of the image, also the
#   starting (largest) block size if there will be block recalculations to
#   improve quality (supported block sizes: 4x4, 8x4, 8x8, 16x2, 16x8, 16x16,
#   32x16, 32x32, 64x32, 64x64, 128x64, 128x128)
# recalc: number of recalculations (>0; e.g. for blksize=32 3 means 16,8,4)
# overlap: overlap size, also used for edges (block size div factor, e.g. for
#   blksize=16 2 means 8)
# thsad, thsadc: motion detection thresholds (luma, chroma)
# edges_proc: enable processing of edges
# edges_params[]:
#   [0,1]: blksizeX, blksizeY; 0 to re-use analysis for normal areas (faster)
#   [2,3]: thsad, thsadc
# edges_threshold: edge detection threshold
# edges_width: width of the edge areas
# edges_softness: softness of the edge areas
# edges_rotate: process edges at 90 deg; can be useful for certain scenarios,
#   e.g. to reduce horizontal jitter or dot crawl
# edges_showmask: display the edge mask (use for tweaking)
# mov_proc - enable additional processing of motion areas
# mov_method - filtering method for motion areas:
#    1: TBilateral (good)
#    2: BoxBlur (fast)
#    3: FlowBlur (weird)
#    4: neo_fft3d (best)
# mov_params[] - filtering parameters for motion areas:
#   for mov_method=1:
#     [0]: luma size (odd numbers, >3, 0=disabled)
#     [1]: chroma size (odd numbers, >3, 0=disabled)
#     [2,3]: spatial deviations (luma, chroma; >0)
#     [4,5]: intensity deviations (luma, chroma; >0)
#   for mov_method=2:
#     [0]: luma size (odd numbers, >3, 0=disabled)
#     [1]: chroma size (odd numbers, >3, 0=disabled)
#   for mov_method=3:
#     [0]: block size (>4, powers of 4)
#     [1]: overlap (>0)
#     [2]: % of vector length(0..100)
#   for mov_method=4:
#     [0,1]: bt (luma, chroma; -1..5, -2=disabled)
#     [2,3]: sigma (luma, chroma; >0, 0=disabled)
#     [4]: block size (bw and bh)
#     [5]: sharpen (>0, 0=disabled)
#     [6]: dehalo (>0, 0=disabled)
# mov_blksize: block size for motion estimation
# mov_overlap: block overlap for motion estimation (block size div factor)
# mov_ml: vector length for motion estimation for motion areas (>0)
# mov_th: mask threshold for motion areas
# mov_softness: softness of mask for motion areas
# mov_amount: transparency for motion areas (0..1)
# mov_thscd1, mov_thscd2: scene change detection thresholds
# mov_antialias: additional light blur for motion areas (0..1, useful for
#   mov_method=1, performed even if mov_proc=False)
# mov_deblock_enable: pre-deblock motion areas (performed even if
#   mov_proc=False)
# mov_deblock_qp: deblock quantizer (1..63)
# mov_deblock_mode: deblock mode (0=hard, 1=soft, 2=medium)
# mov_showmask: show the detected motion areas (use for tweaking)
#----------
# Filters out noise using different approaches for static areas and edges, with
# optional additional filtering for motion areas

# Requirements: MVTools or MVTools-Float, TBilateral, neo_fft3d, DeblockPP7

def denoise3(clip, blksizeX=32, blksizeY=32, recalc=3, overlap=2, thsad=300,
			thsadc=300, edges_proc=True, edges_params=[0, 0, 1000, 1000],
			edges_threshold=63, edges_width=3, edges_softness=3,
			edges_rotate=False, edges_showmask=False, mov_proc=False,
			mov_method=4, mov_params=[2, 2, 2.0, 0, 64, 0, 0], mov_blksize=16,
			mov_overlap=2, mov_ml=20.0, mov_th=127, mov_softness=5,
			mov_amount=1.0, mov_thscd1=500, mov_thscd2=200, mov_antialias=0,
			mov_deblock_enable=False, mov_deblock_qp=8.0, mov_deblock_mode=0,
			mov_showmask=False):

	# prepare some vars
	if thsad==0: plane = 3
	elif thsadc==0: plane = 0
	else: plane = 4

	# create edge mask
	edgemask = core.std.Sobel(clip)
	edgemask = core.std.BinarizeMask(edgemask, threshold=edges_threshold)
	for i in range(0, edges_width):
		edgemask = core.std.Maximum(edgemask)
	if edges_softness>0:
		edgemask = core.std.BoxBlur(edgemask, hradius=edges_softness, hpasses=2,
				vradius=edges_softness, vpasses=2)
	if edges_showmask==True: return edgemask

	# denoise picture
	bsX = blksizeX
	bsY = blksizeY
	if bsX>2: olX = int(bsX/overlap)
	else: olX = 0
	if bsY>2: olY = int(bsY/overlap)
	else: olY = 0
	sup = core.mv.Super(clip)
	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvbw2 = core.mv.Analyse(sup, isb=True, delta=2, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvfw2 = core.mv.Analyse(sup, isb=False, delta=2, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvbw3 = core.mv.Analyse(sup, isb=True, delta=3, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	mvfw3 = core.mv.Analyse(sup, isb=False, delta=3, overlap=olX,
			overlapv=olY, blksize=bsX, blksizev=bsY)
	# do recalculations
	for r in range(0, recalc):
		bsX = bsX>>1
		if bsX<4: break
		bsY = bsY>>1
		if bsY<4: break
		olX = int(bsX/overlap)
		olY = int(bsY/overlap)
		mvbw1 = core.mv.Recalculate(sup, mvbw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvfw1 = core.mv.Recalculate(sup, mvfw1, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvbw2 = core.mv.Recalculate(sup, mvbw2, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvfw2 = core.mv.Recalculate(sup, mvfw2, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvbw3 = core.mv.Recalculate(sup, mvbw3, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
		mvfw3 = core.mv.Recalculate(sup, mvfw3, overlap=olX, overlapv=olY,
				blksize=bsX, blksizev=bsY)
	# process
	normal = core.mv.Degrain3(clip, sup, mvbw1, mvfw1, mvbw2, mvfw2,
			mvbw3, mvfw3, thsad=thsad, thsadc=thsadc, plane=plane)

	# process edges
	if edges_proc==True:
		if edges_params[0]>0 and edges_params[1]>0:
			# do new analysis
			if edges_params[0]>2: eolX = int(edges_params[0]/overlap)
			else: eolX = 0
			if edges_params[1]>2: eolY = int(edges_params[1]/overlap)
			else: eolY = 0
			if edges_rotate==True:
				eclip = core.std.Transpose(clip)
				esup = core.mv.Super(eclip)
			else:
				eclip = clip
				esup = sup
			emvbw1 = core.mv.Analyse(esup, isb=True, delta=1, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			emvfw1 = core.mv.Analyse(esup, isb=False, delta=1, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			emvbw2 = core.mv.Analyse(esup, isb=True, delta=2, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			emvfw2 = core.mv.Analyse(esup, isb=False, delta=2, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			emvbw3 = core.mv.Analyse(esup, isb=True, delta=3, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			emvfw3 = core.mv.Analyse(esup, isb=False, delta=3, overlap=eolX,
					overlapv=eolY, blksize=edges_params[0], blksizev=edges_params[1])
			edges = core.mv.Degrain3(eclip, esup, emvbw1, emvfw1, emvbw2,
					emvfw2, emvbw3, emvfw3, thsad=edges_params[2],
					thsadc=edges_params[3], plane=plane)
			if edges_rotate==True:
				edges = core.std.Transpose(edges)
		else:
			# re-use analysis
			edges = core.mv.Degrain3(clip, sup, mvbw1, mvfw1, mvbw2,
					mvfw2, mvbw3, mvfw3, thsad=edges_params[2],
					thsadc=edges_params[3], plane=plane)
		# merge
		clip = core.std.MaskedMerge(normal, edges, edgemask)
	else:
		clip = normal

	# process motion areas
	if mov_proc==True or mov_deblock_enable==True or mov_antialias>0:
		# analyse
		ol = int(mov_blksize/mov_overlap)
		sup = core.mv.Super(clip)
		mvfw = core.mv.Analyse(sup, isb=False, delta=1, overlap=ol,
				blksize=mov_blksize)

		# create motion mask
		movmask = core.mv.Mask(clip=clip, vectors=mvfw, kind=1, ml=mov_ml,
			gamma=1.0, thscd1=mov_thscd1, thscd2=mov_thscd2, ysc=255)
		movmask = core.std.BinarizeMask(movmask, threshold=mov_th)
		if mov_softness>0:
			movmask = core.std.BoxBlur(movmask, hradius=mov_softness, hpasses=2,
					vradius=mov_softness, vpasses=2)
		if mov_showmask==True: return movmask

		# deblock before processing
		if mov_deblock_enable==True:
			pre = core.pp7.DeblockPP7(clip, qp=mov_deblock_qp,
				mode=mov_deblock_mode)
		else:
			pre = clip

		# denoise areas with motion
		if mov_proc==True:
			if mov_method==1:
				# TBilateral
				if mov_params[0]>0:
					mov = core.tbilateral.TBilateral(pre, planes=[0],
						diameter=mov_params[0], sdev=mov_params[2],
						idev=mov_params[4])
				if mov_params[1]>0:
					mov = core.tbilateral.TBilateral(mov, planes=[1,2],
						diameter=mov_params[1], sdev=mov_params[3],
						idev=mov_params[5])
			elif mov_method==2:
				# BoxBlur
				radius = int(mov_params[0]/2)
				radiusc = int(mov_params[1]/2)
				if radius>0:
					mov = core.std.BoxBlur(pre, planes=[0], hradius=radius,
						vradius=radius)
				if radiusc>0:
					mov = core.std.BoxBlur(mov, planes=[1,2], hradius=radiusc,
						vradius=radiusc)
			elif mov_method==3:
				# FlowBlur
				olFB = int(mov_params[0]/mov_params[1])
				mvfw = core.mv.Analyse(sup, isb=False, delta=1, overlap=olFB,
					blksize=mov_params[0])
				mvbw = core.mv.Analyse(sup, isb=True, delta=1, overlap=olFB,
					blksize=mov_params[0])
				mov = core.mv.FlowBlur(pre, sup, mvbw, mvfw, blur=mov_params[2])
			elif mov_method==4:
				# neo_fft3d
				if mov_params[0]>-2:
					mov = core.neo_fft3d.FFT3D(pre, planes=[0], bt=mov_params[0],
						sigma=mov_params[2], bw=mov_params[4], bh=mov_params[4],
						ow=mov_params[4]/2, oh=mov_params[4]/2,
						sharpen=mov_params[5], dehalo=mov_params[6])
				if mov_params[1]>-2:
					mov = core.neo_fft3d.FFT3D(pre, planes=[1,2], bt=mov_params[1],
						sigma=mov_params[3], bw=mov_params[4], bh=mov_params[4],
						ow=mov_params[4]/2, oh=mov_params[4]/2,
						sharpen=mov_params[5], dehalo=mov_params[6])
			else:
				# no denoise, pre-processing only
				mov = pre
		else:
			# no denoise, pre-processing only
			mov = pre

		# additional anti-alias
		if mov_antialias>0:
			mova = core.std.Convolution(mov, matrix=[0,1,0,1,2,1,0,1,0])
			mov = core.std.Merge(mov, mova, mov_antialias)

		# merge everything
		movf = core.std.MaskedMerge(clip, mov, movmask)
		clip = core.std.Merge(clip, movf, mov_amount)

	return clip

#------------
# LumaChroma
# chroma = -127..127
# U = yellow(-127)..blue(127)
# V = green(-127)..red(127)
#------------
# Requirements: none

def lumachroma(clip, black=0, white=255, gamma=1.0, chroma=0, gammaU=1.0,
		gammaV=1.0, shiftU=0, shiftV=0):

	chroma = 127+chroma

	# Luma
	clip = core.std.Levels(clip, min_in=black, max_in=white, min_out=0,
		max_out=255, gamma=gamma, planes=0)

	# Shift
	if shiftU<0:
		minU = 0
		maxU = 255+shiftU
	else:
		minU = shiftU
		maxU = 255
	if shiftV<0:
		minV = 0
		maxV = 255+shiftV
	else:
		minV = shiftV
		maxV = 255

	# Chroma U
	if chroma>127:
		base = chroma-128
		clip = core.std.Levels(clip, min_in=base, max_in=255-base,
			min_out=minU, max_out=maxU, gamma=gammaU, planes=1)
		clip = core.std.Levels(clip, min_in=base, max_in=255-base,
			min_out=minV, max_out=maxV, gamma=gammaV, planes=2)
	else:
		base = 127-chroma
		clip = core.std.Levels(clip, min_in=0, max_in=255,
			min_out=minU+base, max_out=maxU-base, gamma=gammaU, planes=1)
		clip = core.std.Levels(clip, min_in=0, max_in=255,
			min_out=minV+base, max_out=maxV-base, gamma=gammaV, planes=2)

	return clip


#---------
# DeGhost
#---------
# Requirements: LGhost

def deghost(clip, th=70, mode=3, shift=-4, intensity=50, expand=2, softness=2,
	planes=[0], show_mask=False):

	# detect affected areas
	mask = core.std.Convolution(clip, matrix=[-1,-2,-1,0,0,0,1,2,1], mode="h", planes=planes)

	# adjust to threshold
	mask = core.std.Levels(mask, min_in=th, max_in=255, min_out=0, max_out=255,
		planes=planes)

	# expand
	for i in range(0, expand):
		mask = core.std.Maximum(mask, planes=planes,
			coordinates=[0,0,0,1,1,0,0,0])

	# soften
	if softness>0:
		mask = core.std.BoxBlur(mask, planes, softness, 2, 0)

	# show mask
	if show_mask==True:
		white = core.std.BlankClip(clip, color=[255,0,0])
		clip = core.std.MaskedMerge(clip, white, mask, planes=planes)
		return clip

	# deghost
	dg = core.lghost.LGhost(clip, mode, shift, intensity, planes=planes)

	# merge
	clip = core.std.MaskedMerge(clip, dg, mask, planes=planes)

	return clip

#----------
# ASharpen
#----------
# Better ASharp which does not oversharp contrast edges
# Requirements: ASharp

def asharpen(clip, t=1.0, d=0.0, b=-1.0, hqbf=False, edges_thr=127,
	edges_pow=63, edges_det_width=2, edges_det_pow=1, edges_expand=2,
	edges_softness=2, edges_frame=2, edges_showmask=False):

	# create edge mask
	blurred = core.std.BoxBlur(clip, hradius=edges_det_width,
			vradius=edges_det_width, hpasses=edges_det_pow,
			vpasses=edges_det_pow)
	edgemask = core.std.MakeDiff(clip, blurred)
	edgemask = core.std.Prewitt(edgemask)
	for i in range(0, edges_expand):
		edgemask = core.std.Maximum(edgemask)
	if edges_frame>0:
		edgemask = core.std.Crop(edgemask, edges_frame, edges_frame,
				edges_frame, edges_frame)
		edgemask = core.std.AddBorders(edgemask, edges_frame, edges_frame,
				edges_frame, edges_frame, [255,0,0])
	if edges_softness>0:
		edgemask = core.std.BoxBlur(edgemask, hradius=edges_softness, hpasses=2,
				vradius=edges_softness, vpasses=2)
	edgemask = core.std.Levels(edgemask, min_in=edges_thr,
			max_in=255-edges_pow, min_out=0, max_out=255)
	if edges_showmask==True: return edgemask

	# sharpen
	sharp = core.asharp.ASharp(clip, t, d, b, hqbf)

	# exclude contrast edges
	clip = core.std.MaskedMerge(sharp, clip, edgemask)

	return clip

