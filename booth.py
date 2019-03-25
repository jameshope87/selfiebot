from picamera import PiCamera
from time import sleep
from gpiozero import Button
import glob, os
import subprocess
import shlex
from datetime import datetime
import shutil
from PIL import Image
from PIL import ImageEnhance

imgdir = "/home/pi/Pictures/booth/"
printcmd = "lp -d ZJ-58 -o fit-to-page"
camera = PiCamera()
filename = ''
#camera.start_preview()
button = Button(2)

def processImage(image):
    photo = Image.open(imgdir + "current/{}.jpg".format(image))
    enh = ImageEnhance.Brightness(photo)
    photo = enh.enhance(1.5)
    photo.save(imgdir + "current/{}.jpg".format(image))

def captureImages():
    global filename
    now = datetime.now()
    #print(now)
    for i in range (1,4):
        camera.capture(imgdir + "current/{}.jpg".format(i))
        filename = imgdir + 'archive/{0:%Y-%m-%d %H:%M:%S}'.format(now)
        filename += '-{}.jpg'.format(i)
        print("Image {} captured".format(i))
        shutil.copyfile(imgdir + "current/1.jpg", filename)
        processImage(i)
        sleep(3)
    f = open(imgdir + "current/name.txt", "w+")
    f.write("Name: {0:%Y-%m-%d %H:%M:%S}".format(now))
    f.close()
    ## print images
    printImages()
    ## delete temporary images
    command = 'rm ' + imgdir + 'current/*'
    process = subprocess.Popen(command, shell=True)
    process.wait

def printImages():
    files = glob.glob(imgdir + 'current/*')
    #print(files)
    command = shlex.split(printcmd)
    command += files
    #print(command)
    subprocess.run(command)

if __name__ == '__main__':
    sleep(2)
    while True:
        print("Ready")
        button.wait_for_press()
        captureImages()
