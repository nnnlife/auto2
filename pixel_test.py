from PIL import Image, ImageDraw

im = Image.open("capture_48.jpeg")


def check_oneline_red(im, x1, x2, y):
    for i in range(x1, x2+1):
        r, g, b = im.getpixel((i, y))
        #print(r, g, b)
        if not (r >= 150 and g < 80 and b < 80):
            return False
        
    return True

def check_box_white(im, x1, x2, y1, y2):
    for i in range(x1, x2+1):
        for j in range(y1, y2+1):
            r, g, b = im.getpixel((i, j))
            #print(r, g, b)
            if r < 180 or g < 130 or b < 130:
                return False
            
    return True

print(check_oneline_red(im, 1103, 1106, 432))
print(check_oneline_red(im, 1103, 1106, 449))
print(check_box_white(im, 1104, 1107, 440, 442))


step = 3
start_x = 32
step_x = (206 - start_x) / (100/step)
current_hp, current_mp = 0, 0
d = ImageDraw.Draw(im)
for i in range(int(100/step)):
    r, g, b = im.getpixel((int(32 + step_x * (i+1)), 28))
    #print(r, g, b, (int(32 + step_x * (i+1)), 28))
    #d.line([(int(32 + step_x * (i+1)), 28), (int(32 + step_x * (i+1)), 20)])
    if r > 120 and g < 100 and b < 100:
        current_hp += step
    else:
        break

for i in range(int(100/step)):
    r, g, b = im.getpixel((int(32 + step_x * (i+1)), 43))
    #print(r, g, b, (int(32 + step_x * (i+1)), 43))
    if b > 50:
        current_mp += step
    else:
        #print(b)
        break


print('HP', current_hp, 'MP', current_mp)