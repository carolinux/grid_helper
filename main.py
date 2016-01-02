from matplotlib import pyplot as plt
from collections import namedtuple
import sys

import skimage.io as io


Line = namedtuple("Line","sx sy ex ey width")
Rect = namedtuple("Rect","bottomx bottomy topx topy")


def draw_line_on_picture(pic, line, color=[255,0,0]):
    if line.sx == line.ex:
        pic[line.sy:line.ey,line.sx: line.sx+line.width] = color
    elif line.sy == line.ey:
        pic[line.sy:line.sy+line.width,line.sx: line.ex] = color
    else:
        raise Exception("Non straight lines not supported") # fuck homophobia tho
    return pic

parts = []
main_pic = None 
lw = 3
def divide(x,y):
    global parts
    global main_pic
    #import ipdb; idb.set_trace()
    # find relevant part and split it in four
    for i,rect in enumerate(parts):
        if  x>= rect.bottomx and x<rect.topx and y>=rect.bottomy and y<rect.topy:
            #import ipdb; ipdb.set_trace()
            # TODO remove this from parts array and replace with 4 more
            mx = rect.bottomx + (rect.topx - rect.bottomx)/2
            my = rect.bottomy + (rect.topy - rect.bottomy)/2
            line1 = Line(mx,rect.bottomy,mx,rect.topy, lw)
            line2 = Line(rect.bottomx,my,rect.topx,my, lw)
            print line1, line2
            main_pic = draw_line_on_picture(main_pic, line1)
            main_pic = draw_line_on_picture(main_pic, line2)
            parts.remove(rect)
            parts.append(Rect(rect.bottomx, rect.bottomy, mx,my))
            parts.append(Rect(mx,my,rect.topx, rect.topy))
            parts.append(Rect(rect.bottomx,my,mx, rect.topy))
            parts.append(Rect(mx,rect.bottomy,rect.topx, my))
            return


def onclick(event):
    print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata)
    #plt.close('all')
    divide(event.xdata, event.ydata)
    plot()

def plot():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.imshow(main_pic)
    plt.show()

def main(args):
    global parts
    global main_pic
    imagePath = "/home/carolinux/Pictures/artwerk.jpg"
    main_pic = io.imread(imagePath)
    parts = [Rect(0,0,main_pic.shape[1], main_pic.shape[0])]
    divide(1,1)
    plot()


if __name__ == '__main__':
    main(sys.argv)
