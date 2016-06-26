from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from collections import namedtuple
import sys
import os
import copy

import numpy as np
import json
import glob
import skimage.io as io
from skimage import color
from skimage import exposure
import colorsys
from skimage.filter import roberts, sobel, scharr, prewitt

SETTINGS_FILE="settings.json"
IMAGE_PATH="image_path"
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
G["needle"] = {}

def load_settings():
    return dict(json.load(open(SETTINGS_FILE,'r')))
    

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
        raise Exception("Non straight lines not supported")
    return pic

parts = []
main_pic = None 
history = []
command = None
command_meta = None
colors=[[255,0,0],[0,255,0],[255,255,0],[255,255,255]]
magenta = [255,0,255]

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
    print G["needle"]
    if "active" in  G["needle"] and "pt1" in G["needle"]:
        G["needle"]["pt2"] = (event.x, event.y)
        return
    elif "active" in G["needle"]:
        G["needle"]["pt1"] = (event.x, event.y)
        return
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
    if event.key=="n":
        command="needle"
    if event.key=="v":
        command="vertical_line"
    if event.key=="h":
        command="horizontal_line"
    if event.key=="d":
        command="darken"
    if event.key=="e":
        command="edge"
    if event.key=="u":
        command="undo"
    if event.key=="z":
        command="zoom"
    if event.key=="c":
        command="crop"
    if event.key=="r":
        command="resize_patch"
    if event.key=="m":
        command="mirror"
    if event.key in "b d e u z c v h n r m".split(" "):
        global G
        # save state of plot
        G["plot_geometry"] = plt.get_current_fig_manager().window.geometry()
        plt.close("all")

def handle_event():
    global command
    global command_meta
    global main_pic
    global history
    global patch
    global click_handlers
    global G

    if command=="horizontal_line" or command=="vertical_line":
        h,w = main_pic.shape[:2]
        if patch is not None:
            w1,h1 = patch.get_xy()
            if command=="horizontal_line":
                line = Line(0,int(h1),w,int(h1), int(patch.get_height()), magenta)
            else:
                line = Line(int(w1),0,int(w1),h, int(patch.get_width()), magenta)
            main_pic = draw_line_on_picture(main_pic, line)
            patch=None
        else:
            if command=="horizontal_line":
                patch = Rectangle((0,0), w, 1, edgecolor='magenta', alpha=1)
            else:
                patch = Rectangle((0,0), 1, h, edgecolor='magenta', alpha=1)

    if command=="needle":
        G["needle"]["active"] = True
        just_added_patch = False
        if "pt1" in G["needle"] and "pt2" in G["needle"]: 
            if patch is None:
                print "Drawing needle patch"
                pt1 = G["needle"]["pt1"]
                pt2 = G["needle"]["pt2"]
                patch = Rectangle((pt1[0],pt1[1]), abs(pt2[0]-pt1[0]), abs(pt2[1]-pt1[1]), edgecolor='magenta', alpha=1, facecolor='magenta')
                just_added_patch = True
        if patch is not None and not just_added_patch:
            print "finalize"
            w1,h1 = patch.get_xy()
            w = patch.get_width()
            h = patch.get_height()

            if w>h:
                print("horizontal patch")
                line = Line(int(w1),int(h1),int(w1+w),int(h1), 3, magenta)
            else:
                line = Line(int(w1),int(h1),int(w1),int(h1+h), 3, magenta)

            main_pic = draw_line_on_picture(main_pic, line)
            G["needle"] = {}

    if command == "divide":
        divide(command_meta.xdata, command_meta.ydata)
    if command == "brighten":
        main_pic = do_brighten(main_pic)
    if command == "mirror":
	main_pic = np.fliplr(main_pic)
    if command == "zoom":
        click_handlers = not click_handlers
    if command == "darken":
        main_pic = do_darken(main_pic)
    if command == "edge":
        main_pic = edge_detect(main_pic)
    if command == "resize_patch":
        if patch is not None:
            h = patch.get_height()
            w = patch.get_width()
            patch.set_width(int(w/2))
            patch.set_height(int(h/2))

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
            # TODO: can read this from settings :))
            portrait_ratio = 14.8/20.8
            if orientation=="portrait":
                w_to_h = portrait_ratio
            else:
                w_to_h = 1.0/portrait_ratio
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
    if command not in ["crop","horizontal_line","vertical_line","needle","resize_patch"]:
        patch = None
    command = None
    command_meta = None
    plot(patch=patch, click_handlers=click_handlers)
    if command is not None:
        handle_event()

def drag(event):
    if event.xdata is None or event.ydata is None:
        return
    if patch:
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

def main(specified_filename, specified_orientation):
    global parts
    global main_pic
    global orientation
    global filename
    filename = specified_filename
    orientation = specified_orientation
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

def determine_filename(fn):
    if os.path.exists(fn):
        return fn
    image_dir = settings[IMAGE_PATH]
    path_to_try = os.path.join(image_dir, fn)
    if os.path.exists(path_to_try):
        return path_to_try
    pretty_file_list =  os.linesep.join(os.listdir(image_dir))
    fn_glob ="*"+fn+"*"
    matching_files = glob.glob(os.path.join(image_dir, fn_glob))
    if not matching_files:
        raise Exception("Could not find file in {} that matches pattern {}. Available files {} {}".format(
            image_dir, fn_glob, os.linesep, pretty_file_list))
    matching_files = sorted(matching_files, key=lambda x: "gridded" not in x)
    return matching_files[-1]
        



settings  = load_settings()
if __name__ == '__main__':
    if len(sys.argv)<2:
        print("Usage: python main.py image.png [portrait or landscape]")
        sys.exit(1)
    if len(sys.argv)>1:
        orientation = sys.argv[1]
    else:
        orientation = "portrait"
    fn = determine_filename(sys.argv[1])
    print fn
    main(fn, orientation)
