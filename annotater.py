import cv2
import copy
import colorsys
import sys
import random
history = []
counter = 0
start_random = random.random()
def _get_hex_round_color(current_round_index):
    global start_random
    val = 0
    for i in range(current_round_index,0,-1):
        random.seed(start_random+i)
        val += (0.1+random.random()*0.8) % 1
    return [int(255*col) for col in colorsys.hsv_to_rgb(val, 1, 1)]

def click_event(event, x, y, flags, params):
    global history
    global counter
    font = cv2.FONT_HERSHEY_SIMPLEX
    if event == cv2.EVENT_LBUTTONDOWN:
        if flags & cv2.EVENT_FLAG_SHIFTKEY > 0:
            mod_im = copy.deepcopy(history[-1])
            cv2.putText(mod_im, f"{chr(ord("A")+counter)}", (x, y), font, 1, _get_hex_round_color(counter), 2)
            counter += 1
            cv2.imshow('window', mod_im)
            return
        mod_im = copy.deepcopy(history[-1])
        mod_im = cv2.putText(mod_im, f"{chr(ord("A")+counter)}", (x, 50), font, 1, _get_hex_round_color(counter), 2)
        mod_im = cv2.line(mod_im, (x, 100000), (x, 100), _get_hex_round_color(counter), 3)
        counter += 1
        history.append(mod_im)
        cv2.imshow('window', history[-1])
    if event == cv2.EVENT_MBUTTONDOWN:
        if len(history) > 1:
            history = history[:-1]
            counter -= 1
        cv2.imshow('window', history[-1])
if __name__=="__main__":
    opened = sys.argv[1]
    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    img = cv2.imread(opened, 1)
    h, w, *_ = img.shape
    wh,ww = 1080,1920
    aspect_ratio = ww / w
    if w < h:
        aspect_ratio = wh / h
    img = cv2.resize(img, None, fx=aspect_ratio, fy=aspect_ratio, interpolation=cv2.INTER_AREA)
    history.append(img)
    cv2.imshow('window', img)
    cv2.setMouseCallback('window', click_event)
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            cv2.imwrite(opened.split(".")[0] + "_Annoed.png", history[-1])
            break