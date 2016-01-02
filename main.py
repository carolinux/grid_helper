from matplotlib import pyplot as plt
from collections import namedtuple
import sys

import skimage.io as io


Line = namedtuple("Line","sx sy ex ey")


def draw_line_on_picture(pic, line, color=[255,0,0]):
    if line.sx == line.ex:
        ry = range(line.sy, line.ey)
        rx = range(line.sx, line.sx+20)
        #pic[ry,:][:,rx] = color  
        pic[line.sy:line.ey,line.sx: line.sx+20] = color
    
    return pic


def main(args):
    imagePath = "/home/carolinux/Pictures/artwerk.jpg"
    main_pic = io.imread(imagePath)
    #import ipdb; ipdb.set_trace()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    def onclick(event):
        print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
            event.button, event.x, event.y, event.xdata, event.ydata)
        #plt.close('all')

    line = Line(10,40,10,80)
    main_pic = draw_line_on_picture(main_pic, line)

    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    plt.imshow(main_pic)
    plt.show()


if __name__ == '__main__':
    main(sys.argv)
