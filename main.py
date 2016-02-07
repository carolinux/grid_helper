from matplotlib import pyplot as plt
from collections import namedtuple
import sys

import skimage.io as io


Line = namedtuple("Line","sx sy ex ey width color")
Rect = namedtuple("Rect","bottomx bottomy topx topy hierarchy")


def draw_line_on_picture(pic, line):
    c2 = line.color
    if line.sx == line.ex:
        for j in range(line.sy, line.ey):
            for i in range(line.sx, line.sx+line.width+1):
                c1 = pic[j][i]
                pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2])]
    elif line.sy == line.ey:
        for j in range(line.sy, line.sy+line.width+1):
            for i in range(line.sx, line.ex):
                c1 = pic[j][i]
                pic[j][i] = [0.5*(c1[0]+c2[0]),0.5*(c1[1]+c2[1]),0.5*(c1[2]+c2[2])]
    else:
        raise Exception("Non straight lines not supported") # fuck homophobia tho
    return pic

parts = []
main_pic = None 
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

curr_event=None

def onclick(event):
    print event
    print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata)
    global curr_event
    curr_event = event
    plt.close('all')
    #divide(event.xdata, event.ydata)
    #plot()

def handle_event():
    global curr_event
    if curr_event is not None:
        divide(curr_event.xdata, curr_event.ydata)
    curr_event = None
    plot()
    if curr_event is not None:
        handle_event()

def plot():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.imshow(main_pic)
    plt.show()

def main(args):
    global parts
    global main_pic
    imagePath = args[0] #"/home/carolinux/Pictures/artwerk.jpg"
    main_pic = io.imread(imagePath)
    print("Size {}".format(main_pic.shape))
    parts = [Rect(0,0,main_pic.shape[1], main_pic.shape[0],0)]
    divide(1,1)
    handle_event()


if __name__ == '__main__':
    if len(sys.argv)<2:
        print("Usage: python main.py image.png")
        sys.exit(1)
    main(sys.argv[1:])
