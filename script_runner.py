from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt
import time
import serial



class ScriptRunner(QThread):
    current_command_changed = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = False
        self.commands = []
        self._setup_serial()

    def _setup_serial(self):
        try:
            self.aduino = serial.Serial('COM3', 9600)
            if self.aduino.isOpen() == False:
                self.aduino.open()
        except serial.serialutil.SerialException:
            pass

    def _get_commands(self, script):
        commands = []
        token = script.split('(')
        for t in token:
            if not t: continue
            elif t.endswith(')'):
                commands.append(t[:-1])
        return commands

    def set_script(self, script):
        self.commands.clear()
        self.commands = self._get_commands(script)

    def key_input(self, k):
        msg = b'\x02\x04\x01' + k.encode() + b'\n'
        print('key_input', k, len(msg), msg)
        self.aduino.write(msg)
        time.sleep(0.3)

    def key_press(self, k):
        msg = b'\x02\x05\x01' + k.encode() + b'\n'
        print('key_press', k, len(msg), msg)
        self.aduino.write(msg)
        time.sleep(0.2)
    
    def key_release(self):
        msg = b'\x02\x06\x00' + b'\n'
        print('key_release', len(msg), msg)
        self.aduino.write(msg)
        time.sleep(0.2)

    def mouse_click(self, x, y):
        msg = b'\x02\x07\x04' + x.to_bytes(2, 'big') + y.to_bytes(2, 'big') + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)
        msg = b'\x02\x08\x00' + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)
        print('mouse click', x, y, len(msg), msg, x.to_bytes(2, 'big'))

    def mouse_swipe(self, x1, y1, x2, y2):
        msg = b'\x02\x07\x04' + x1.to_bytes(2, 'big') + y1.to_bytes(2, 'big') + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)
        msg = b'\x02\x09\x00' + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)
        msg = b'\x02\x07\x04' + x2.to_bytes(2, 'big') + y2.to_bytes(2, 'big') + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)
        msg = b'\x02\x10\x00' + b'\n'
        self.aduino.write(msg)
        time.sleep(0.2)

    def _mouse_control(self, x, y, action):
        pass

    def run(self):
        while self.running:
            for c in self.commands:
                if not self.running:
                    return

                if len(c) == 1:
                    if c == '!':
                        time.sleep(1)
                        self.current_command_changed.emit('SLEEP(1)')
                    else:
                        self.current_command_changed.emit('KEY(' + c + ')')
                        self.key_input(c)
                elif c.count(',') == 2: # Mouse
                    mouse_command = c.split(',')
                    x, y, action = int(mouse_command[0]), int(mouse_command[1]), mouse_command[2]
                    self.current_command_changed.emit('MOUSE(' + str(x) + ',' + str(y) + '): ' + action) 
                    self._mouse_control(x, y, action)

if __name__ == '__main__':
    s = ScriptRunner()
    s.set_script('(123,234,UP)(!)(D)(234,642,CLICK)')
