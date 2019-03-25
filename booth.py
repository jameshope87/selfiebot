#Standard Imports
from time import sleep
import glob, os
import subprocess
import shlex
from datetime import datetime
import shutil
import sys

REAL_PATH = os.path.dirname(os.path.realpath(__file__))

#Additional imports
try:
    from PIL import Image
    from PIL import ImageEnhance
    from picamera import PiCamera
    from gpiozero import Button
	
except ImportError as missing_module:
    print('--------------------------------------------')
    print('ERROR:')
    print(missing_module)
    print('')
    print(' - Please run the following command(s) to resolve:')
    if sys.version_info < (3,0):
        print('   pip install -r ' + REAL_PATH + '/requirements.txt')
    else:
        print('   pip3 install -r ' + REAL_PATH + '/requirements.txt')
    print('')
    sys.exit()

###################
# Variables      ##
###################
currentimgdir = "/home/pi/Pictures/booth/current/"
archiveimgdir = "/home/pi/Pictures/booth/archive/"
printcmd = "lp -d ZJ-58 -o fit-to-page"
camera_button = 2
numberOfPhotos = 3
photoDelay = 3
SCREEN_W = 800
SCREEN_H = 480


###################
# Camera Setup   ##
###################
camera.rotation = 0
camera.hflip = True
camera.start_preview()

###################
# GPIO Setup     ##
###################

button = Button(camera_button)

###################
# Helper Functions#
###################

def folderCheck():
    folders_list = [currentimgdir, archiveimgdir]
    folders_checked = []
    
    for folder in folders_list:
        if folder not in folders_checked
            folders_checked.append(folder)
        else:
            print('ERROR: Cannot use same folder path ('+folder+') twice. Refer config file.')
        
        if not os.path.exists(folder):
            print('Creating folder: ' + folder)
            os.makedirs(folder)
    

def printOverlay(string_to_print):
    """
    Writes a string to both the console and the camera preview
    """
    print(string_to_print)
    camera.annotate_text = string_to_print
    
def determine_filename(now):
    """
    Works out the file name based off the current datetime
    """
    filename = archiveimgdir + '{0:%Y-%m-%d %H:%M:%S}'.format(now)
    filename += '-{}.jpg'.format(i)
    return filename

def removeOverlay(overlay_id)
    """
    Removes overlay if there is one
    """
    if overlay_id != -1
        camera.remove_overlay(overlay_id)
        
def overlay_image(image_path, duration=0, layer=3,mode='RGB'):
    """
    Add an overlay (and sleep for an optional duration).
    If sleep duration is not supplied, then overlay will need to be removed later.
    This function returns an overlay id, which can be used to remove_overlay(id).
    """
    
    #load the image
    img = Image.open(image_path)
    if(img.size[0] > SCREEN_W):
        #resize overlays to match screen size:
        basewidth = SCREEN_W
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((basewidth,hsize), Image.ANTIALIAS)
        
    # "
    #   The camera`s block size is 32x16 so any image data
    #   provided to a renderer must have a width which is a
    #   multiple of 32, and a height which is a multiple of
    #   16.
    # "
    # Refer:
    # http://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-images-on-the-preview

    # Create an image padded to the required size with mode 'RGB' / 'RGBA'
    pad = Image.new(mode, (
        ((img.size[0] + 31) // 32) * 32,
        ((img.size[1] + 15) // 16) * 16,
    ))

    # Paste the original image
    pad.Paste(img, (0, 0))
    
    # Get the padded image data
    try:
        padded_img_data = pad.tobytes()
    except AttributeError:
        padded_img_data = pad.tostring() # Note: tostring() is depreciated in PIL v3.xrange
        
    # Add the overlay with the padded image as the source
    # but the original image's dimensions
    
    o_id = camera.add_overlay(padded_img_data, size=img.size)
    o_id.layer = layer
    
    if duration > 0:
        sleep(duration)
        camera.remove_overlay(o_id)
        o_id = -1 # '-1' indicates there is no overlay
        
    return o_id # if we have an overlay (o_id > 0), we will need to remove it later
    
def processImage(image):
    photo = Image.open(currentimgdir + "{}.jpg".format(image))
    enh = ImageEnhance.Brightness(photo)
    photo = enh.enhance(1.5)
    photo.save(currentimgdir + "{}.jpg".format(image))

def captureImages():
    now = datetime.now()
    #print(now)
    for i in range (1,numberOfPhotos + 1):
        camera.capture(currentimgdir + "{}.jpg".format(i))
        print("Image {} captured".format(i))
        filename = determine_filename(now)
        shutil.copyfile(currentimgdir + "1.jpg", filename)
        processImage(i)
        sleep(photoDelay)
    f = open(currentimgdir + "name.txt", "w+")
    f.write("Name: {0:%Y-%m-%d %H:%M:%S}".format(now))
    f.close()
    ## print images
    printImages()
    ## delete temporary images
    command = 'rm ' + currentimgdir + '*'
    process = subprocess.Popen(command, shell=True)
    process.wait

def printImages():
    files = glob.glob(currentimgdir + '*')
    #print(files)
    command = shlex.split(printcmd)
    command += files
    #print(command)
    subprocess.run(command)

if __name__ == '__main__':
    camera = PiCamera()
    sleep(2)
    while True:
        print("Ready")
        button.wait_for_press()
        captureImages()
