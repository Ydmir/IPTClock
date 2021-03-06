#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################################
#  IPTClock, a graphical countdown clock for use with the international physicist's tournament
#    Copyright (C) 2016-2017  Albin Jonasson Svärdsby & Joel Magnusson
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################################



#########################
# Written in python 3,
# will exit for lower verions
##########################


#######################
# Import dependencies #
#######################

# check tkversion
# Import packages, and check for python version
import sys
if sys.version_info[0] < 3:
    print('You are using a Python version < 3 !! \n Functionality crippled!\n ')
    sys.exit(0)
else:
    import tkinter as tk
    import _thread # in order to utilize threads # the threading that is used is written for python 3
    usePython3 = True

import math
import time as pyTime

# check os
usingLinuxMasterRace = False
usingWindows = False
usingMac = False
from sys import platform as _platform

if _platform == "linux" or _platform == "linux2":
    # LINUX
   usingLinuxMasterRace = True
elif _platform == "darwin":
   # MAC OS X
    usingMac = True
elif _platform == "win32":
   # Windows
    usingWindows = True


from tkinter import messagebox
#from tkinter import simpledialog
import tkinter.simpledialog as simpledialog

# import tkfont #to change font #NOT IMPLEMENTED

# imports the matplotlib and set variable installedMatplotlib
installedMatplotlib = True

import matplotlib as mpl
mpl.use('TkAgg')

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.image as mpimg

import math
import time

# check if we use audio or not (.wave format)
try:
    import pyaudio
    installedPyaudio = True
except ImportError:
    installedPyaudio = False

if installedPyaudio:
    import wave


####################
# Global Variables #
####################
fps = 1

# Blue: '#7DC7EE'
# Yellow: '#FED812', '#eded1e'
# Red: '#d32c2c'
# Purple: '#864da0'
defaultBackgroundColor = None  # 'blue'    # String, following tkinter naming. color used for background, buttons and labels etc. NOT color behind wedge, use "None" without "" to get system default
wedgeBackgroundColor = None  # '#13235b' #String, following matplotlib naming.  color of the wedge background (for example to adhere to present year's color scheme. None defaults to Tkinter color from defaultBackgroundColor
clockColors = ['#7DC7EE', '#FED812', '#d32c2c', '#864da0']  # List of colors for the clock to cycle through

# Path to sponsor image [Presently PNG!], if using tkinter and label, it has to be in GIF and if we use matplotlib it has to be in PNG.
leftSponsImagePath = './Images/Sponsors/sponsors.png' # './testPicture.gif'  # './ponyAndDuck.gif'

pathToSoundFile = ''#'./Audio/theDuckSong2.wav'  # If left empty nothing happens, requires [.wav]

stagesPath = "./stages.txt"

# To be introduced...:
# defaultFont = # string deciding the standard font
# defaultFontSize =  # integer, fontsize of text


###################
# Import Settings #
###################
def import_stages():
    settings = open(stagesPath).read()
    separator = ' -- '
    if settings is not '':
        lines = [line.split(separator) for line in settings.split('\n')]
        stages = []
        for lineNbr, line in enumerate(lines):
            try:
                stage_time = int(line[0])
                stage_description = line[1]
                stages.append((stage_description, stage_time))
            except ValueError:
                pass
            except IndexError:
                pass
        return stages


#######################
# ClockGraphics Class #
#######################
class ClockGraphics:
    def __init__(self):
        # Definition of initial clock state/position
        self._clock_center = [0, 0]
        self._clock_reference_angle = 90
        self._clock_radius = 0.9
        self._angle = 0

        # Creation of clock graphical elements
        self._ax, self._fig, self._canvas = create_clock_canvas()
        self._wedge = self._create_wedge(2)
        self._backgroundDisc = self._create_circle(1, True)
        self._perimiterCircle = self._create_circle(3, False)

        # Dependable settings. Should later be set through kwargs.
        self._colors = [wedgeBackgroundColor] + clockColors  # [wedgeBackgroundColor, wedgeColor, 'red', 'purple']

        # Reset the clock
        self.reset()

    def _create_wedge(self, zorder):
        wedge = mpl.patches.Wedge(self._clock_center, self._clock_radius, self._clock_reference_angle, self._clock_reference_angle, zorder=zorder)
        self._ax.add_patch(wedge)
        return wedge

    def _create_circle(self, zorder, fill):
        circle = mpl.patches.Circle(self._clock_center, self._clock_radius, fill=fill, zorder=zorder)
        self._ax.add_patch(circle)
        return circle

    def _isTwelve(self):
        return abs(self._angle) % 360 < 1e-3 or 360 - abs(self._angle) % 360 < 1e-3

    def _update_wedge(self):
        if self._isTwelve():
            self._wedge.set_theta1(self._clock_reference_angle - 1e-3)
        else:
            self._wedge.set_theta1(self._clock_reference_angle + self._angle)

    def _updateCanvas(self):
        # Tkinter need to redraw the canvas to actually show the new updated matplotlib figure
        self._canvas.draw()

    def _switch_colors(self):
        lap = int(abs(self._angle - 1e-3)/360)
        if lap < len(self._colors)-1:
            wedge_color = self._colors[lap+1]
            background_color = self._colors[lap]
        else:
            wedge_color = self._backgroundDisc.get_facecolor()
            background_color = self._wedge.get_facecolor()
        self._wedge.set_facecolor(wedge_color)
        self._backgroundDisc.set_facecolor(background_color)

    def set_angle(self, new_angle):
        self._angle = new_angle
        self.update()

    def update(self):
        if self._isTwelve():
            self._switch_colors()
        self._update_wedge()
        self._updateCanvas()

    def reset(self):
        self.set_angle(0)


###############
# Timer Class #
###############
class Timer:
    def __init__(self):
        self._tick_state = False
        self._start_time = 0
        self._time = 0
        self._string = ''

        self._string_pattern = '{0:02d}:{1:02d}'  # the pattern format for the timer to ensure 2 digits
        self._time_step = 1/fps

        self.set_timer(self._start_time)

    def _update_string(self):
        seconds = int(abs(math.ceil(self._time - 1e-3)) % 60)
        minutes = int(abs(math.ceil(self._time - 1e-3)) // 60)
        # fixes the countdown clock when deadline is passed
        if self._time < 0:
                self._string = '-' + self._string_pattern.format(minutes, seconds)
        else:
            self._string = self._string_pattern.format(minutes, seconds)

    def _set_time(self, time):
        self._time = time
        self._update_string()

    def start_time(self):
        return self._start_time

    def time(self):
        return self._time

    def string(self):
        return self._string

    def set_timer(self, start_time):
        self._start_time = start_time
        self.reset()

    def tick(self):
        self._set_time(self._time-self._time_step)

    def isTicking(self):
        return self._tick_state

    def start(self):
        self._tick_state = True

    def pause(self):
        self._tick_state = False

    def reset(self):
        self._tick_state = False
        self._set_time(self._start_time)


###############
# Stage Class #
###############
class Stage:
    def __init__(self):
        self._stages = import_stages()
        self._nStages = len(self._stages)
        self._current_stage = 0

    def get(self):
        return self._current_stage

    def set(self, stage_number):
        self._current_stage = stage_number

    def description(self):
        return self._stages[self._current_stage][0]

    def time(self):
        return self._stages[self._current_stage][1]

    def next(self):
        if self._current_stage < self._nStages-1:
            self._current_stage += 1

    def previous(self):
        if self._current_stage > 0:
            self._current_stage -= 1

    def get_stages(self):
        return self._stages.copy()


###############
# Clock Class #
###############
class Clock:
    def __init__(self):
        self.stage = Stage()
        self.timer = Timer()
        self.clock_graphics = ClockGraphics()
        self.startPlayingSongTime = 55 # time in seconds when death mode sound is played

        self.countdownText, self.presentationTextLabel = create_clock_labels()  # orig on LH self.challengeTimeLabel

        self._update_stage_dependencies()

    # To start the countdown
    def start(self):
        self.timer.start()

    # To pause the countdown
    def pause(self):
        self.timer.pause()

    # To reset the countdown to startTime
    def reset(self):
        # reset the timer
        self.timer.reset()

        # Update the countdownText Label with the updated time
        self.countdownText.configure(text=self.timer.string())

        # reset the clock graphics
        self.clock_graphics.reset()

    # function updating the time
    def update(self):
        # Every time this function is called,
        # decrease timer with one second
        t0 = time.time()
        if self.timer.isTicking():
            self.timer.tick()

            # Update the countdownText Label with the updated time
            self.countdownText.configure(text=self.timer.string())

            # Update the clock graphics. Clock starts at 0 then negative direction clockwise
            angle = -360 * ((self.timer.start_time() - self.timer.time()) / self.timer.start_time())
            self.clock_graphics.set_angle(angle)

            # check for countdown time for activating "low health mode"
            if self.timer.time() == self.startPlayingSongTime:
                _thread.start_new_thread(PlayASoundFile, (pathToSoundFile,))

        # Call the update() function after 1/fps seconds
        dt = (time.time() - t0) * 1000
        time_left = max(0, int(1000 / fps - dt))
        master.after(time_left, self.update)

    def set_stage(self, stage_number):
        self.stage.set(stage_number)
        self._update_stage_dependencies()

    def previous_stage(self):
        self.stage.previous()
        self._update_stage_dependencies()

    def next_stage(self):
        self.stage.next()
        self._update_stage_dependencies()

    def _update_stage_dependencies(self):
        self.timer.set_timer(self.stage.time())

        self.countdownText.configure(text=self.timer.string())
       # self.challengeTimeLabel.configure(text=self.timer.string())
        self.reset()
        self.presentationTextLabel.configure(text=self.stage.description())  # update text presenting stage

###########
# Timeout #
###########
        
class TimeoutClass:
    # Presently it makes calls to IPTClock (which is a clock class), which isn't very nice
    def __init__(self):
        self.timeoutTime = 60 # [s]
        self.timerStopTime = 0
        self.timeoutState = True
        self._string_pattern = '{0:02d}:{1:02d}:{2:02d}'
        self._time = self.timeoutTime * 100 #[centi s]
        self.timestep = 10 #[ms]
        self.update_string()

        # check if clock is running
        self.tick_state = IPTClock.timer._tick_state             
        IPTClock.pause() # pause clock
        
    def setupTimeout(self):
        # create and positions the pop up frame
        self.top = tk.Toplevel()
        self.top.title("TIMEOUT!")
        self.msg = tk.Label(self.top, text=self.string,  font=('Courier New', 60) )
        self.msg.pack(fill='x')

        self.button = tk.Button(self.top, text="Dismiss", command=self.exit_timeout)
        self.button.pack()

    
    # function updating the time
    def update(self):
        if self.timeoutState :
            self.update_string()       
            # Update the countdownText Label with the updated time
            self.msg.configure(text=self.string)
                
            master.after(self.timestep, self.update) # tkinter function ,waits ms and executes command
            self._time = self._time -self.timestep/10

            # check exit criteria
            if self._time < self.timerStopTime:
                # terminate countdown and unpause main clock
                self.timeoutState = False
                if self.ongoingTimer:
                    IPTClock.start()
                self.top.destroy()
                
       
    def update_string(self):
        # updates the timeoutstring
        seconds = int( ( abs( math.ceil(self._time - 1e-3) )/100 )  % 60)
        minutes = int( ( abs(math.ceil(self._time - 1e-3) )/100)  // 60)
        centiseconds = int(abs(math.ceil(self._time -1e-3) ) % 100  )
        # fixes the countdown clock when deadline is passed
        if self._time < 0:
            self.string = '-' + self._string_pattern.format(minutes, seconds, centiseconds)
        else:
            self.string = self._string_pattern.format(minutes, seconds, centiseconds)

    def exit_timeout(self):
        self.top.destroy() # this results in an exception, not breaking the program but ugly.

        if self.tick_state: # check so that we don't start the clock if it wasn't running before timeout
            IPTClock.start()

        
# function creating class and running update
def Timeout():    
    IPTTimeout = TimeoutClass()
    IPTTimeout.setupTimeout()
    IPTTimeout.update()
    

###################
# SponsImageClass #
###################

class SponsImage():
    def __init__(self):
        self._sponsImage = leftSponsImagePath # must be PNG
        self.img = mpimg.imread( self._sponsImage )#'./ponyAndDuck.png') # converts/load image
        self.widthRatioOfImage = 0.3 # how much of the screen that is sponsImage
        self._determine_pixeldistance()
        self._fig, self._canvas, self._plt  = self._create_sponsImage_canvas()
        

    def _updateCanvas(self):
        # Tkinter need to redraw the canvas to actually show the new updated matplotlib figure
        self._canvas.draw()

    def _determine_pixeldistance(self):
        #determines how many mm there is between the pixels
        widthmm, heightmm, width, height = self.screen_dimensions()
        self.pixDist_width = widthmm*1.0/width
        self.pixDist_height = heightmm*1.0/height
       

    def _create_sponsImage_canvas(self):
        widthmm, heightmm, width, height = self.screen_dimensions()

        # inch convert
        widthInch =  widthmm* 0.0393700787 * self.widthRatioOfImage
        heightInch = heightmm * 0.0393700787

        sponsFig = plt.figure(figsize =(widthInch,heightInch) ,edgecolor=None, facecolor=wedgeBackgroundColor)
        
        imgplot = plt.imshow(self.img)
        plt.axis('off') # removes labels and axis, numbers etc.
        plt.tight_layout(pad=0, w_pad=0, h_pad=0) # removes padding round figure

        # Create own frame for the canvas
        self.SponsFrame = tk.Frame(master)
        sponsCanvas = FigureCanvasTkAgg(sponsFig, master=self.SponsFrame)
        sponsCanvas.show()

        # align frame and let canvas expand
        self.SponsFrame.grid(row=0, column=0, columnspan=1, rowspan=14 , sticky='NW') 
        sponsCanvas.get_tk_widget().grid(row=0, column=0, columnspan=1, rowspan=14 , sticky='NWES')
        return sponsFig, sponsCanvas, imgplot 


    def screen_dimensions(self):
        #returns size of screen in mm and pixels
        widthmm = master.winfo_screenmmheight() #returns size of master object in mm
        heightmm = master.winfo_screenmmwidth()

        width = master.winfo_screenheight() #returns size of master object in mm
        height = master.winfo_screenwidth()        
        return widthmm, heightmm, width, height

    def canvas_size(self):
        widthPix = self._canvas.winfo_width()
        heightPix = self._canvas.winfo_height()
        return widthPix, heightPix


    def updateFigSize(self):
#        widthPix, heightPix = master.winfo_width(), master.winfo_height()
#        widthPix, heightPix = self._canvas.winfo_width(), self._canvas.winfo_height()
        widthPix, heightPix =  self.SponsFrame.winfo_width(), self.SponsFrame.winfo_height()
 
        widthmm = widthPix * self.pixDist_width
        heightmm = heightPix * self.pixDist_height
               
        # inch convert
        widthInch =  widthmm* 0.0393700787 # * self.widthRatioOfImage
        heightInch = heightmm * 0.0393700787
        self._fig.set_size_inches( widthInch,heightInch, forward=True)
        #self._canvas.show()
        self._updateCanvas()


        
###################
# Sound Functions #
###################
def PlayASoundFile(pathToSoundFile):
    CHUNK = 64  # 1024
    wf = wave.open(pathToSoundFile, 'rb')

    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    # open stream (2)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # read data
    data = wf.readframes(CHUNK)

    # play stream (3)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

    # stop stream (4)
    stream.stop_stream()
    stream.close()

    # close PyAudio (5)
    p.terminate()



###################
# Button Commands #
###################
# emphasise quit()
def _quit():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        sys.exit(0)


def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        sys.exit(0)


# toggling Fullscreen
def toogleFullscreen():
    toogleFullscreenButton()

def toogleFullscreenLinux(temp):
    toogleFullscreenButton() 


def toogleFullscreenButton():
    global master, fullscreenButton
    state = not master.fullscreen
    master.attributes('-fullscreen', state)
    master.focus_set()
    master.fullscreen = state
    if (master.fullscreen):
        fullscreenButton.configure(text="Windowed")
        master.fullscreenSwitch.set(True) # traced variable
    else:
        fullscreenButton.configure(text="Fullscreen")
        master.fullscreenSwitch.set(False) # traced variable

def endFullscreenLinux(tmp):
    endFullscreen() # there's some difference between os and input using keyes


def endFullscreen():
    global master, fullscreenButton
    master.fullscreen = False
    master.attributes("-fullscreen", False)
    fullscreenButton.configure(text="Fullscreen")
    master.focus_set()
    SponsImageResize() # needed since it might skip resizing back elsewise
    master.fullscreenSwitch.set(False) # traced variable

def EditReporter():
    reporterString = simpledialog.askstring('Edit Reporter', 'Reporter', initialvalue=reporterNameLabel.cget('text'))
    reporterNameLabel.configure(text=reporterString)


def EditOpponent():
    opponentString = simpledialog.askstring('Edit Opponent', 'Opponent', initialvalue=opponentNameLabel.cget('text'))
    opponentNameLabel.configure(text=opponentString)


def EditReviewer():
    reviewerString = simpledialog.askstring('Edit Reviewer', 'Reviewer', initialvalue=reviewerNameLabel.cget('text'))
    reviewerNameLabel.configure(text=reviewerString)




    

#################
# GUI Functions #
#################
def create_clock_labels():
    # Digital clock present time
#    challengeTimeLabel = tk.Label(master, text='', font=('Courier New', 26))
#    challengeTimeLabel.grid(row=9, column=2, columnspan=3, rowspan=1)
#    challengeTimeLabel.configure(background=defaultBackgroundColor)

    # Digital clock countdown
    countdownText = tk.Label(master, text='', font=('Courier New', 46))
    countdownText.grid(row=2, column=2, columnspan=3)
    countdownText.configure(background=defaultBackgroundColor)

    # Presentation of current phase
    presentationTextLabel = tk.Label(master, text='', font=('Courier New', 32), wraplength=1400)
    presentationTextLabel.grid(row=9, column=2, columnspan=3, sticky=tk.S)
    presentationTextLabel.configure(background=defaultBackgroundColor)
    return countdownText, presentationTextLabel #, challengeTimeLabel


def create_clock_canvas():
    fig = plt.figure(figsize=(16, 16), edgecolor=None, facecolor=wedgeBackgroundColor)

    ax = fig.add_subplot(111)
#    ax.set_axis_bgcolor(None)
    ax.set_facecolor(None)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect(1)  # similar to "axis('equal')", but better.
    ax.axis('off')  # makes axis borders etc invisible.

    canvas = FigureCanvasTkAgg(fig, master=master)
    canvas.show()
    canvas.get_tk_widget().grid(row=3, column=2, columnspan=3, rowspan=1)  # , sticky=tk.N)
    return ax, fig, canvas





def SponsImageResizeOnEvent(event):
    SponsImageResize() # I know but it works



def SponsImageResize():

######## OLD image presentation using just tkinter###########
#    # checks if the image is larger then the window and rescales. Slow process
#    global master
#    # get screen width and height    
#    ws = master.winfo_width() # width of the screen
#    hs = master.winfo_height() # height of the screen
#    
#    #get size of image
#    hi = master.image.height()
#    wi = master.image.width()

#    if ( hi > hs): #check i height of image is bigger then the window
#        scalefactor = hs/hi
#        new_width_pixels = round(ws / scalefactor )
#        new_height_pixels = hs
#
#        # since 
#        if ( math.log(new_height_pixels,10) > 2 ):
#            nlog =  math.log(new_height_pixels,10)
#            new_height_pixels = round( new_height_pixels / (10**( nlog-1) ) )
#            new_hi = round( hi / (10**( nlog-1) ) )            
#        else:
#            new_hi = hi
#
#        # since the only input is integers we need to scale up before we can scale down to reach good size
#        master.newImage = master.image.zoom(new_height_pixels) # Memory problems apears for higher values into zoom
#        master.newImage = master.newImage.subsample(new_hi) # and subsample back to desired size            
#        master.sponsLabel.configure(image = master.newImage)
    IPTSpons.updateFigSize()

def SponsImageFullscreen(a,b,c):
######## OLD image presentation using just tkinter###########
 #   global master
 #   ws = master.winfo_screenwidth() # width of the screen
 #   hs = master.winfo_screenheight() # height of the screen
 #   #get size of image
 #   hi = master.image.height()
 #   wi = master.image.width()
 #   if ( hi > hs): #check i height of image is bigger then the window
 #       scalefactor = hs/hi
 #       new_width_pixels = round(ws / scalefactor )
 #       new_height_pixels = hs
 #       
 #       # since 
 #       if ( math.log(new_height_pixels,10) > 2 ):
 #           nlog =  math.log(new_height_pixels,10)
 #           new_height_pixels = round( new_height_pixels / (10**( nlog-1) ) )
 #           new_hi = round( hi / (10**( nlog-1) ) )
 #           print('small')
 #       else:
 #           new_hi = hi
 #           # since the only input is integers we need to scale up before we can scale down to reach good size
 #       master.newImage = master.image.zoom(new_height_pixels) # Memory problems apears for higher values into zoom            
 #       master.newImage = master.newImage.subsample(new_hi) # and subsample back to desired size
 #   else:
 #       master.newImage = master.image
 #   master.sponsLabel.configure(image = master.newImage)
    IPTSpons.updateFigSize()



# about this application
def AboutPopup():
    # creates a popup window showing basic info and copywright
    top_about = tk.Toplevel()
    top_about.title("About IPTClock")


    about_logo=tk.Label(top_about, image=logo_image)
    about_logo.pack(side='left')

    about_message = "IPTClock is a countdown clock written for use in the International Physicist's Tournament. The program is written using Python 3 with Tkinter and matplotlib.\n\n Copyright (c) 2016-2017 by Albin Jonasson Svärdsby  \n Joel Magnusson"
    about_msg = tk.Message(top_about, text=about_message)
    about_msg.pack(side='right')

    about_exit_button = tk.Button(top_about, text="Dismiss", command=top_about.destroy)
    about_exit_button.pack(side='bottom')



###################
# GUI Definitions #
###################
master = tk.Tk()  # define master tk object


# fix icon on window
if usingWindows:
    pass
#    master.iconbitmap(default='./Images/Ico/newIPTlogo_without_text.ico') #'./Images/Ico/newIPTlogo_without_text.ico')

elif usingLinuxMasterRace:
    img = tk.PhotoImage(file='./Images/Ico/IPTlogo_color.png') #newIPTlogo_without_text.png')
    master.tk.call('wm', 'iconphoto', master._w, img)

elif usingMac:
    pass

else:
    pass

# change window title
master.wm_title("IPTClock")

# bindings for fullscreen
master.fullscreen = False
master.attributes('-fullscreen', False)

if usingLinuxMasterRace or usingMac:
    master.bind("<F11>", toogleFullscreenLinux)
    master.bind("<Escape>", endFullscreenLinux)
else:
    master.bind("<F11>", toogleFullscreen)    
    master.bind("<Escape>", endFullscreen)


# set the background color, given from variable at start
master.configure(background=defaultBackgroundColor)

# Find default background color and check in case we use it
defaultbgColor = master.cget('bg')  # find system window default color
bgRGB = master.winfo_rgb(defaultbgColor)
bgRGB = (bgRGB[0]/(256**2), bgRGB[1]/(256**2), bgRGB[2]/(256**2))

if wedgeBackgroundColor is None:
    wedgeBackgroundColor = bgRGB

# boolean for fullscreen
master.fullscreen = False

######################################################
#################
# Sponsor Image #
#################

IPTSpons = SponsImage()

### OLD image presentation using just tkinter###########
#master.image = tk.PhotoImage(file=leftSponsImagePath)
#master.sponsLabel = tk.Label(master, image=master.image)
#master.sponsLabel.grid(row=0, column=0, columnspan=1, rowspan=14, sticky='N')
#####################################################



##################################################################


####################
# Competitor Names #
####################
# Reporter
reporterLabel = tk.Label(master, text="Reporter:", font=('Courier New', 16))
reporterLabel.grid(row=11, column=2)
reporterLabel.configure(background=defaultBackgroundColor)
reporterNameLabel = tk.Label(master, text='', font=('Courier New', 16))
reporterNameLabel.grid(row=11, column=3, sticky=tk.W)

# Opponent
opponentLabel = tk.Label(master, text="Opponent:", font=('Courier New', 16))
opponentLabel.grid(row=12, column=2)
opponentLabel.configure(background=defaultBackgroundColor)
opponentNameLabel = tk.Label(master, text='', font=('Courier New', 16))
opponentNameLabel.grid(row=12, column=3, sticky=tk.W )

# Reviewer
reviewerLabel = tk.Label(master, text="Reviewer:", font=('Courier New', 16))
reviewerLabel.grid(row=13, column=2)
reviewerLabel.configure(background=defaultBackgroundColor)
reviewerNameLabel = tk.Label(master, text='', font=('Courier New', 16))
reviewerNameLabel.grid(row=13, column=3, sticky=tk.W)

####################
# Initialize Clock #
####################
IPTClock = Clock()


###################
# Control Buttons #
###################
# Start Button
startButton = tk.Button(master=master, text='Start', command=IPTClock.start)
startButton.grid(row=4, column=7, sticky='WE')
startButton.configure(background=defaultBackgroundColor)

# Pause Button
pauseButton = tk.Button(master=master, text='Pause', command=IPTClock.pause)
pauseButton.grid(row=5, column=7, sticky='WE')
pauseButton.configure(background=defaultBackgroundColor)

# Reset button
resetButton = tk.Button(master=master, text='Reset', command=IPTClock.reset)
resetButton.grid(row=11, column=7, sticky='WE')
resetButton.configure(background=defaultBackgroundColor)

# Quit button
quitButton = tk.Button(master=master, text='Quit', command=_quit)
quitButton.grid(row=13, column=7, sticky='WE')
quitButton.configure(background=defaultBackgroundColor)

# Fullscreen
fullscreenButton = tk.Button(master=master, text='Fullscreen', command=toogleFullscreenButton)
fullscreenButton.grid(row=7, column=7, sticky='WE')
fullscreenButton.configure(background=defaultBackgroundColor)

# Edit Reporter
editReporterButton = tk.Button(master=master, text='Edit', command=EditReporter)
editReporterButton.grid(row=11, column=5)
editReporterButton.configure(background=defaultBackgroundColor)

# Edit Opponent
editOpponentButton = tk.Button(master=master, text='Edit', command=EditOpponent)
editOpponentButton.grid(row=12, column=5)
editOpponentButton.configure(background=defaultBackgroundColor)

# Edit Reviewer
editReviewerButton = tk.Button(master=master, text='Edit', command=EditReviewer)
editReviewerButton.grid(row=13, column=5)
editReviewerButton.configure(background=defaultBackgroundColor)

# Previous Stage
previousStageButton = tk.Button(master=master, text='<<', command=IPTClock.previous_stage)
previousStageButton.grid(row=8, column=7, sticky='WE')

# Next Stage
nextStageButton = tk.Button(master=master, text='>>', command=IPTClock.next_stage)
nextStageButton.grid(row=9, column=7, sticky='WE')

# timeout
timeoutButton = tk.Button(master=master, text='Timeout', command=Timeout)
timeoutButton.grid(row=10,column=7,sticky='WE')


#####################
# layout lines
####################

horizontalLine = tk.Label(master, text='-', background='darkgray', height=1, font=('Courier New', 1), borderwidth=0)
horizontalLine.grid(row=10, column=2, columnspan=4, sticky='WE')

verticalLineRight = tk.Label(master, text='-', background='darkgray', height=1, font=('Courier New', 1), borderwidth=0)
verticalLineRight.grid(row=0, column=6, columnspan=1, rowspan=14, sticky='NS')

verticalLineLeft = tk.Label(master, text='-', background='darkgray', height=1, font=('Courier New', 1), borderwidth=0)
verticalLineLeft.grid(row=0, column=1, columnspan=1, rowspan=14, sticky='NS')


##########################
# Top menu configuration #
##########################

menubar = tk.Menu(master)
filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_separator()

filemenu.add_command(label="Exit", command=_quit)
menubar.add_cascade(label="File", menu=filemenu)


# drop down menu to chose stage
stagemenu = tk.Menu(menubar, tearoff=0)
for i, stage in enumerate(IPTClock.stage.get_stages()):
    stagemenu.add_command(label=str(i) + ": " + stage[0],
                          command=lambda stage_number=i: IPTClock.set_stage(stage_number))

menubar.add_cascade(label="Stage", menu=stagemenu)


# help menu
logo_image = tk.PhotoImage(file= './Images/IPTlogos/IPTlogo_Color.gif') #'./Images/IPTlogos/newIPTlogo_without_text.gif') # needed outside aboutPopup to avoid garbage collect


helpmenu = tk.Menu(menubar, tearoff=0) # create helpmenu
helpmenu.add_command(label="About", command= AboutPopup )

menubar.add_cascade(label="Help", menu=helpmenu) # add helpmenu

master.config(menu=menubar) # set the final menu

# change column behaviour for scaling
master.rowconfigure(0, weight=1)
master.columnconfigure(3, weight=1)
master.rowconfigure(3, weight=1)
master.rowconfigure(9, minsize=125)


# fix initial window size and position
w = 900 # width for the Tk root [pixels]
h = 700 # height for the Tk root
# get screen width and height
ws = master.winfo_screenwidth() # width of the screen [pixels]
hs = master.winfo_screenheight() # height of the screen

# calculate x and y coordinates for the Tk root window
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

master.geometry('%dx%d+%d+%d' % (w, h, x, y))

IPTClock.update()  # update the countdown




# binds resize of master window and execute rescale of spons image
master.fullscreenSwitch = tk.BooleanVar() # variable to trace
master.fullscreenSwitch.set(False) # initial value

master.bind('<Configure>', SponsImageResizeOnEvent )
master.fullscreenSwitch.trace('w', SponsImageFullscreen) # watch the variable master.fullscreenSwitch, when i changes on switching to fullscreen it will execute command SponsImageFullscreen

    
master.protocol("WM_DELETE_WINDOW", on_closing)  # necessary to cleanly exit the program when using the windows manager

# start the GUI loop
master.mainloop()
