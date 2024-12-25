# Adapted from code by Grégoire Sage.

import argparse
import math
import sys
from PIL import Image

WATCHFACE_DIMENSIONS = 450  # height and width from watchface.xml
AMBIENT_LIMIT = 0.15    # proportion of shape area that can be non-black
bleedFactor = 1.0       # factor by which area of all-white circle exceeds pi*r^2
areaBlackSystem = 0     # exta px for 'no bluetooth' icon with no significant overlap

def calcOPR(width, scale, shapeName, areaBlackWatchface, areaShape, intensity):
    print(f"Shape is {shapeName}")
    print(f"Image area (with bleed) is {round(areaShape)} pixels")
    if FRACTIONAL_INTENSITY:
        print("Average intensity is {:.2f}%".format(intensity / 1950.75 / areaShape)) # 1950.75 = (255*3)*255/100
        maxIntensity = AMBIENT_LIMIT * areaShape    # number of full-intensity px
        overLimit = round(intensity / 195075.0 - maxIntensity)
    else:   # black vs. non-black
        print("{:.2f}% of pixels are not black".format(100. * (areaShape - areaBlackWatchface) / areaShape))
        overLimit = areaShape * (1 - AMBIENT_LIMIT) - areaBlackWatchface
    overUnder = "OVER" if overLimit >= 0 else "under"
    overLimit = math.ceil(math.fabs(overLimit))
    print("At {}×{}, {} limit by {} white pixels; ie, about {:.1f} square".format(width, width, overUnder, overLimit, math.sqrt(overLimit)))
    if width != WATCHFACE_DIMENSIONS:
        print("At {}×{}, {} limit by {:.0f} white pixels; ie, about {:.1f} square".format(WATCHFACE_DIMENSIONS, WATCHFACE_DIMENSIONS, overUnder, overLimit/scale, math.sqrt(overLimit/scale)))

parser = argparse.ArgumentParser(description='Assess AOD of Wear OS screenshot.')
parser.add_argument('source', help='filename (.png)')
parser.add_argument('-s', action="store_true", help='watchface is square (default: round)')
parser.add_argument('-n', action="store_true", help='consider all non-black pixels to be fully used')
parser.add_argument('-b', type=float, help='bleed factor')
parser.add_argument('-c', action="store_true", help='calculate bleed factor from white circle')
args = parser.parse_args()

FRACTIONAL_INTENSITY = args.n == False    # whether to display stats for partial illumination rather than black vs. non-black

if FRACTIONAL_INTENSITY and areaBlackSystem > 0:
    print("Error: can't use non-zero systemOverlayPixelCount with FRACTIONAL_INTENSITY")
    exit(1)

im = Image.open(args.source)

if im.width != im.height:   # TODO 5 support rect (eg, "Wear OS Rectangular" AVD)
    print("Error: image isn't square")
    exit(1)

pixels = im.getdata()
#print(pixels[0])
# TODO 5.5 try to assess whether image is round

if len(pixels[0]) < 3:  # TODO 5 allow greyscale images (eg, from Paintshop Pro)
    print("Error: image doesn't seem to be RGB or RGBA")
    exit(1)

areaSquare = len(pixels)

intensity = 0   # sum of (R+B+G)*A
areaBlackWatchface = 0
if FRACTIONAL_INTENSITY:
    if len(pixels[0]) == 3:
        intensity = sum(p[0] + p[1] + p[2] for p in pixels)
        intensity *= 255
    else:
        intensity = sum((p[0] + p[1] + p[2]) * p[3] for p in pixels)
else:
    if len(pixels[0]) == 3:
        areaBlackTotal = sum(p[0] + p[1] + p[2] == 0 for p in pixels)
    else:
        areaBlackTotal = sum((p[0] + p[1] + p[2]) * p[3] == 0 for p in pixels)
    areaBlackWatchface = areaBlackTotal + areaBlackSystem   # assume system icon(s) don't overlap watchface non-black
    areaNonBlackWatchface = areaSquare-areaBlackWatchface

areaCircle = math.pi/4 * areaSquare

if args.c:  # calculate bleed factor from white circle
    if FRACTIONAL_INTENSITY:
        bleed = float(intensity) / areaCircle / 765 / 255
    else:
        bleed = areaNonBlackWatchface / areaCircle
    print(f"Bleed is {bleed:.6f}")
    if bleed < 0.95 or bleed > 1.05: print("Bleed value is improbable; ensure image is white circle")
    exit(1)

# Set areaCircle to actual values of AVD screenshots for common diameters:
if args.b:
    bleedFactor = args.b
else:
    bleedFactor = 0.995 if FRACTIONAL_INTENSITY else 1.0015
areaCircle *= bleedFactor

areaCropped = areaSquare - areaCircle   # assume all pixels outside circle are black

print(f"Image size is {im.width}×{im.height} pixels")
print(f"Format is {'RGB' if len(pixels[0])==3 else 'RGBA'}")
print(f"Bleed factor is {bleedFactor}")
print(f"Top left pixel is {pixels[0]}")

if FRACTIONAL_INTENSITY:
    print(f"Total intensity Σ(R+G+B)A is {intensity}")
else:
    print(f"Black area (total) is {round(areaBlackTotal)} pixels")
    print(f"Non-black area (system) is {round(areaBlackSystem)} pixels")
    print(f"Black area (watchface) is {round(areaBlackWatchface)} pixels")
    print(f"Non-black area (watchface) is {round(areaNonBlackWatchface)} pixels")

scale = float(im.width) / WATCHFACE_DIMENSIONS

if (args.s):
    calcOPR(im.width, scale, 'square', areaBlackWatchface, areaSquare, intensity)
else:
    calcOPR(im.width, scale, 'circle', areaBlackWatchface-areaCropped, areaCircle, intensity)