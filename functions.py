# FUNCTIONS.PY by Efenstor
# Modified in December 2021

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
# Requirements: MVTools or MVTools-Float

def denoise(clip, blksizeX=8, blksizeY=8, overlap=2, thsad=200, thsadc=400):

	overlapX = int(blksizeX/overlap)
	overlapY = int(blksizeY/overlap)

	sup = core.mv.Super(clip)
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
	if thsad==0:
		plane = 3
	elif thsadc==0:
		plane = 0
	else:
		plane = 4
	clip = core.mv.Degrain3(clip, sup, mvbw1, mvfw1, mvbw2, mvfw2, mvbw3, mvfw3,
			thsad=thsad, thsadc=thsadc, plane=plane)

	return clip


#------------
# FlowFPS
#------------
# Requirements: MVTools or MVTools-Float

def flowfps(clip, num, den, blksize, keepfps):

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


#---------
# AddBlur
#---------
# Requirements: MVTools or MVTools-Float

def addblur(clip, amount, blksize):

	overlap = int(blksize/2)

	sup = core.mv.Super(clip, pel=2)

	mvbw1 = core.mv.Analyse(sup, isb=True, delta=1, overlap=overlap,
			blksize=blksize)
	mvfw1 = core.mv.Analyse(sup, isb=False, delta=1, overlap=overlap,
			blksize=blksize)
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

	clip = core.std.Interleave(clips=[clip,clip])
	frameA = clip
	frameB = core.std.DeleteFrames(clip, 0)
	if transition==0:
		clip = frameA
	elif transition==1:
		clip = frameB
	else:
		clip = core.std.Merge(frameA, frameB, transition)
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

def strobe(clip, transition):

	src_fpsnum = clip.fps_num
	src_fpsden = clip.fps_den

	frameA = core.std.SelectEvery(clip, 4, 0)
	frameB = core.std.SelectEvery(clip, 4, 1)
	clip = core.std.Merge(frameA, frameB, transition)
	clip = core.std.Interleave(clips=[clip,clip,clip,clip])
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
#---------
# Requirements: DeblockPP7

def deblock(clip, blksize=8, qp=8.0, ml=16.0):

	overlap = int(blksize/2)

	deblock = core.pp7.DeblockPP7(clip=clip, qp=qp)
	sup = core.mv.Super(clip)
	mvfw = core.mv.Analyse(sup, isb=False, blksize=blksize, overlap=overlap)
	mask = core.mv.Mask(clip=clip, vectors=mvfw, kind=1, ml=ml, gamma=1.0)
	clip = core.std.MaskedMerge(clip, deblock, mask)
	return clip


#--------------
# Deaberration
#--------------
# Default values are for Canon HF100 with Raynox x0.3 with the 37mm-37mm ring

# Requirements: none

def deaberration(clip, r_size=1.002, g_size=1.002, b_size=1.0):

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

	return clip


#-------------
# UnsharpMask
#-------------
# Requirements: none

def unsharpmask(clip, strength=1, radius=1, passes=2, planes=[0]):

	blur = core.std.BoxBlur(clip, planes=planes, hradius=radius, vradius=radius,
			hpasses=passes, vpasses=passes)
	diff = core.std.MakeDiff(clip, blur, planes=planes)
	sharp = core.std.MergeDiff(clip, diff, planes=planes)
	clip = core.std.Merge(clip, sharp, strength)

	return clip


#--------
# DeHalo
#--------
# Requirements: TBilateral, AddGrain

def dehalo(clip, edge_gamma=0.7, hl_th=63, offset=1, halo_width=25,
		softness=8, sdev=2, idev=6, planes=[0], grain_l=0, grain_c=0,
		show_mask=False, show_hl=False, show_filtered=False):

	# detect edges
	mask = core.std.Sobel(clip, planes)
	mask = core.std.Levels(mask, gamma=edge_gamma)

	# produce the halo mask
	hmask = mask
	for i in range(0, halo_width):
		hmask = core.std.Maximum(hmask, planes)

	# subtract the safe areas
	smask = mask
	if offset!=0:
		if offset>0:
			for i in range(0, offset):
				smask = core.std.Maximum(smask, planes)
		else:
			for i in range(0, -offset):
				smask = core.std.Minimum(smask, planes)
	mask = core.std.Expr([hmask, smask], "x y -")

	# subtract the hightlight areas from the halo areas
	hlmask = core.std.Binarize(clip, threshold=hl_th, planes=planes)
	if show_hl==True: return hlmask
	mask = core.std.Expr([mask, hlmask], "x y -")

	# soften the mask
	if softness>0:
		mask = core.std.BoxBlur(mask, planes, softness, 2, softness, 2)
	if show_mask==True: return mask

	# filter
	if show_filtered==False:
		filtered = core.tbilateral.TBilateral(clip, diameter=7, sdev=sdev,
				idev=idev, planes=[0])
	else:
		filtered = core.std.BlankClip(clip, color=[255, 0, 0])

	# add grain
	if grain_l > 0 or grain_c > 0:
		filtered = core.grain.Add(filtered, var=grain_l, uvar=grain_c)

	# merge
	clip = core.std.MaskedMerge(clip, filtered, mask)

	return clip


#----------
# Denoise2
#----------
# Requirements: MVTools or MVTools-Float

def denoise2(clip, blksizeX=8, blksizeY=8, overlap=2, thsad=300, thsadc=300,
			edges_thsad=1500, edges_thsadc=1500, edges_threshold=63,
			edges_width=3, edges_softness=3, show_mask=False):

	mask = core.std.Sobel(clip)
	mask = core.std.Binarize(mask, threshold=edges_threshold)

	hmask = mask
	for i in range(0, edges_width):
		hmask = core.std.Maximum(hmask)
	if edges_softness>0:
		mask = core.std.BoxBlur(hmask, hradius=edges_softness, hpasses=2,
				vradius=edges_softness, vpasses=2)
	else:
		mask = hmask

	if show_mask==True: return mask

	normal = denoise(clip, blksizeX, blksizeY, overlap, thsad, thsadc)
	edges = denoise(clip, blksizeX, blksizeY, overlap, edges_thsad,
			edges_thsadc)
	clip = core.std.MaskedMerge(normal, edges, mask)

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

