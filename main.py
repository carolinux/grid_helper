from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from collections import namedtuple
import sys
import os
import copy

import numpy as np
import skimage.io as io
from skimage import color
from skimage import exposure
import colorsys
from skimage.filter import roberts, sobel, scharr, prewitt


Line = namedtuple("Line","sx sy ex ey width color")
Rect = namedtuple("Rect","bottomx bottomy topx topy hierarchy")
fig = None
patch = None
orientation = None
click_handlers = True
filename = None
ax = None
# global object
G = {}


def to_rgb3a(im):
    # we can use the same array 3 times
    return np.dstack([im] * 3)

def do_brighten(pic):
    return exposure.adjust_gamma(pic,0.7)

def do_darken(pic):
    return exposure.adjust_gamma(pic,1.3)

def edge_detect(pic):
    edges = scharr(color.rgb2grey(pic))
    #return edges
    return to_rgb3a(edges)

def draw_line_on_picture(pic, line):
    c2 = line.color
    if line.sx == line.ex:
        for j in range(line.sy, line.ey):
            for i in range(line.sx, line.sx+line.width+1):
                c1 = pic[j][i]
                if len(c1) == 3:
                    pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2])]
                else:
                    pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2]),1]
    elif line.sy == line.ey:
        for j in range(line.sy, line.sy+line.width+1):
            for i in range(line.sx, line.ex):
                c1 = pic[j][i]
                c1 = pic[j][i]
                if len(c1) == 3:
                    pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2])]
                else:
                    pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2]),1]
    else:
        raise Exception("Non straight lines not supported") # fuck homophobia tho
    return pic

parts = []
main_pic = None 
history = []
command = None
command_meta = None
colors=[[255,0,0],[0,255,0],[255,255,0],[255,255,255]]

lws = [3,2,1]
def get_color(idx):

    return colors[idx % len(colors)]

def get_line_width(idx):
    if idx<len(lws):
        return lws[idx]
    else:
        return lws[-1]


def divide(x,y):
    global parts
    global main_pic
    if not parts:
        parts =[Rect(0,0,main_pic.shape[1], main_pic.shape[0],0)]

    #import ipdb; idb.set_trace()
    # find relevant part and split it in four
    for i,rect in enumerate(parts):
        if  x>= rect.bottomx and x<rect.topx and y>=rect.bottomy and y<rect.topy:
            #import ipdb; ipdb.set_trace()
            mx = rect.bottomx + (rect.topx - rect.bottomx)/2
            my = rect.bottomy + (rect.topy - rect.bottomy)/2
            new_hierarchy = rect.hierarchy + 1
            color = get_color(new_hierarchy-1)
            lw = get_line_width(new_hierarchy-1)
            line1 = Line(mx,rect.bottomy,mx,rect.topy, lw,color)
            line2 = Line(rect.bottomx,my,rect.topx,my, lw,color)
            print line1, line2
            main_pic = draw_line_on_picture(main_pic, line1)
            main_pic = draw_line_on_picture(main_pic, line2)
            parts.remove(rect)
            parts.append(Rect(rect.bottomx, rect.bottomy, mx,my,new_hierarchy))
            parts.append(Rect(mx,my,rect.topx, rect.topy,new_hierarchy))
            parts.append(Rect(rect.bottomx,my,mx, rect.topy, new_hierarchy))
            parts.append(Rect(mx,rect.bottomy,rect.topx, my, new_hierarchy))
            return


def onclick(event):
    global G
    G["plot_geometry"] = plt.get_current_fig_manager().window.geometry()
    print event
    print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata)
    global command
    global command_meta
    command="divide"
    command_meta = event
    plt.close('all')
    #divide(event.xdata, event.ydata)
    #plot()

def fileparts(fn):
    path = os.path.dirname(fn)
    basename = os.path.basename(fn)
    name,ext = os.path.splitext(basename)
    return (path,name,ext)

def save():
    folder,name,ext = fileparts(filename)
    i=1
    while True:
        newfn = os.path.join(folder,"{}_gridded{}{}".format(name,i,ext))
        if not os.path.exists(newfn):
            #plt.savefig(newfn, bbox_inches='tight', pad_inches=0.0)
            io.imsave(newfn, main_pic)
            print newfn
            return
        i+=1


def press(event):
    global command
    global command_meta
    if event.key=="o": # o for out
        # seems s is already a shortcut for matplotlib
        save()
    if event.key=="b":
        command="brighten"
    if event.key=="d":
        command="darken"
    if event.key=="e":
        command="edge"
    if event.key=="u":
        command="undo"
    if event.key=="z":
        command="zoom"
    if event.key=="c": # do cropping before you make a grid
        command="crop"
    if event.key in "b d e u z c".split(" "):
        global G
        G["plot_geometry"] = plt.get_current_fig_manager().window.geometry()
        plt.close("all")

def handle_event():
    global command
    global command_meta
    global main_pic
    global history
    global patch
    global click_handlers

    if command == "divide":
        divide(command_meta.xdata, command_meta.ydata)
    if command == "brighten":
        main_pic = do_brighten(main_pic)
    if command == "zoom":
        click_handlers = not click_handlers
    if command == "darken":
        main_pic = do_darken(main_pic)
    if command == "edge":
        main_pic = edge_detect(main_pic)
    if command == "crop":
        if patch is not None:
            # apply patch
            # crop main_pic
            h = patch.get_height()
            w = patch.get_width()
            w1,h1 = patch.get_xy()
            main_pic = main_pic[slice(h1,h1+h),slice(w1,w1+w),slice(None)]
            patch=None

        else:
            # create patch
            if orientation=="portrait":
                w_to_h = 14.8/20.8
            else:
                w_to_h = 20.8/14.8
            shape = main_pic.shape
            border = 15
            hp = shape[0] - border
            wp = shape[1] - border

            if w_to_h * hp >wp:
                tw = wp
                th = wp / w_to_h 
            else:
                th = hp
                tw = w_to_h * hp
            print th,tw
            patch = Rectangle((0,0), tw, th, edgecolor='magenta', alpha=1, facecolor='none')
    if command == "undo":
        print "Undoing"
        print len(history)
        if len(history)>=2:
            main_pic,cmd = history[-2]
            print cmd
            history = history[:-1]

    if command!="undo":
        history.append((np.copy(main_pic),command))
    if command!="crop":
        patch = None
    command = None
    command_meta = None
    plot(patch=patch, click_handlers=click_handlers)
    if command is not None:
        handle_event()

def drag(event):
    if event.xdata is None or event.ydata is None:
        return
    patch.set_xy((event.xdata,event.ydata))
    fig.canvas.draw()

def plot(patch=None,click_handlers=True):
    global fig
    global ax
    global G
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if click_handlers:
        cid = fig.canvas.mpl_connect('button_press_event', onclick)
    cid2 = fig.canvas.mpl_connect('key_press_event', press)

    plt.imshow(main_pic)
    if patch:
        ax.add_patch(patch)
        cid3 = fig.canvas.mpl_connect('motion_notify_event', drag)
    if "plot_geometry" in G:
        plt.get_current_fig_manager().window.setGeometry(G["plot_geometry"])
    plt.show()

def main(args):
    global parts
    global main_pic
    global orientation
    global filename
    filename = args[0] #"/home/carolinux/Pictures/artwerk.jpg"
    if len(args)>1:
        orientation = args[1]
    else:
        orientation = "portrait"
    main_pic = io.imread(filename)
    print("Size {}".format(main_pic.shape))
    h =  main_pic.shape[0]
    w = main_pic.shape[1]
    if h>w:
        print("Width to Height 1 to  {}".format(h*1.0/w))
    else:
        print("Height to Width  1 to  {}".format(w*1.0/h))
    parts = []
    handle_event()


if __name__ == '__main__':
    if len(sys.argv)<2:
        print("Usage: python main.py image.png [portrait or landscape]")
        sys.exit(1)
    main(sys.argv[1:])
