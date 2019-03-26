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
    import picamera
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
camera_button = 4
numberOfPhotos = 3
prepDelay = 2
SCREEN_W = 800
SCREEN_H = 480
COUNTDOWN = 3


##################
## Camera Setup ##
##################
camera = picamera.PiCamera()
camera.rotation = 0
camera.hflip = True


################
## GPIO Setup ##
################

button = Button(camera_button)

######################
## Helper Functions ##
######################

def folderCheck():
    folders_list = [currentimgdir, archiveimgdir]
    folders_checked = []
    
    for folder in folders_list:
        if folder not in folders_checked:
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
    
def determineFilenamePrefix():
    """
    Works out the file name based off the current datetime
    """
    now = datetime.now()
    filename = archiveimgdir + '{0:%Y-%m-%d %H:%M:%S}'.format(now)
    return filename, now

def removeOverlay(overlay_id):
    """
    Removes overlay if there is one
    """
    if overlay_id != -1:
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
    pad.paste(img, (0, 0))
    
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

#############
## Screens ##
#############

def prepForPhotoScreen(photoNumber):
    """
    Prompt the user to get ready for the next photo
    """
    
    get_ready_image = REAL_PATH + '/assets/get_ready_' + str(photoNumber) + '.png'
    overlay_image(get_ready_image, prepDelay, 3, 'RGBA')
    
def processImage(image):
    photo = Image.open(currentimgdir + "{}.jpg".format(image))
    enh = ImageEnhance.Brightness(photo)
    photo = enh.enhance(1.5)
    photo.save(currentimgdir + "{}.jpg".format(image))

def captureImages(photoNumber, filenamePrefix):
    """
    Function to actualy capture the photo, process it and save a copy to the archive
    """
    filename = filenamePrefix + '-{}.jpg'.format(photoNumber)
    
    #countdown and display on screen
    for counter in range(COUNTDOWN, 0, -1):
        printOverlay("             ..." + str(counter))
        sleep(1)
        
    #Take a still image
    camera.annotate_text = ''
    camera.capture(currentimgdir + "{}.jpg".format(photoNumber))
    print("Image {} captured".format(photoNumber))
    shutil.copyfile(currentimgdir + "{}.jpg".format(photoNumber), filename)
    processImage(photoNumber)

def playbackScreen(filenamePrefix):
    """
    Review photos before printing
    """
    prevOverlay = False
    for photoNumber in range(1, numberOfPhotos + 1):
        filename = filenamePrefix + '-{}.jpg'.format(photoNumber)
        thisOverlay = overlay_image(filename, False, (3 + numberOfPhotos))
        
        if prevOverlay:
            removeOverlay(prevOverlay)
        sleep(2)
        prevOverlay = thisOverlay
        
    removeOverlay(prevOverlay)
    

def printImages(currTime):
    f = open(currentimgdir + "name.txt", "w+")
    f.write("Name: {0:%Y-%m-%d %H:%M:%S}".format(currTime))
    f.close()
    files = glob.glob(currentimgdir + '*')
    #print(files)
    command = shlex.split(printcmd)
    command += files
    #print(command)
    #subprocess.run(command)
    ## delete temporary images
    command = 'rm ' + currentimgdir + '*'
    #process = subprocess.Popen(command, shell=True)
    #process.wait
    
    #All done
    print('All Done!')
    finishedImage = REAL_PATH + '/assets/all_done_delayed_upload.png'
    overlay_image(finishedImage, 5)

def shutterPressed():
    global shutterHasBeenPressed
    shutterHasBeenPressed = True
    
def main():

    """
    Main program loop
    """
    #Start Program
    print('Welcome to the photo booth!')
    #print('(version ' + __version__ + ')')
    print('')
    print('Press the \'Take photo\' button to take a photo')
    print('Use [Ctrl] + [\\] to exit')
    print('')
    sleep(2)
    #Setup required folders
    folderCheck()
    
    #start camera preview
    camera.start_preview(resolution=(SCREEN_W, SCREEN_H))
    
    #Display Intro screens
    intro_image_1 = REAL_PATH + '/assets/intro_1.png'
    intro_image_2 = REAL_PATH + '/assets/intro_2.png'
    overlay_1 = overlay_image(intro_image_1, 0, 3)
    overlay_2 = overlay_image(intro_image_2, 0, 4)
    
    #Wait for button press
    i = 0
    blink_speed = 10
    
    button.when_pressed = shutterPressed
    
    while True:
        shutterHasBeenPressed = False
        #Stay in loop until button is pressed
        if shutterHasBeenPressed is False:
            i += 1
            if i == blink_speed:
                overlay_2.alpha = 255
            elif i == (2 * blink_speed):
                overlay_2.alpha = 0
                i = 0
            #Restart while loop
            sleep(0.1)
            continue
        button has been pressed!
        print("Button Pressed!")
        removeOverlay(overlay_2)
        removeOverlay(overlay_1)
        #get filename
        filenamePrefix, now = determineFilenamePrefix()
        
        for photoNumber in range(1, numberOfPhotos + 1):
            prepForPhotoScreen(photoNumber)
            captureImages(photoNumber, filenamePrefix)
        
        printImages(now)
        playbackScreen(filenamePrefix)
        
        overlay_1 = overlay_image(intro_image_1, 0, 3)
        overlay_2 = overlay_image(intro_image_2, 0, 4)
        print("press the button!")

if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        print('Goodbye')
"""
    finally:
        camera.stop_preview()
        camera.close()
        sys.exit()
"""
