from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt, QFile, QByteArray, QTimer
from PyQt5.QtGui import QKeySequence
import win32gui
import windep
import time
import os
import script_runner
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime, timedelta


KEY_HEAL='3'
KEY_GROUP_HEAL='e'
KEY_SHIELD='r'
KEY_OPOTION='h'
KEY_HOME='z'
KEY_ORA='8'
KEY_AUTO='h'
KEY_ENEMY_ATTACK='v'


class CursorInfo(QThread):
    cursor_trace = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            time.sleep(0.1)
            cursor = win32gui.GetCursorInfo()
            #print(cursor)
            self.cursor_trace.emit(cursor[2][0], cursor[2][1])

class RecordArea(QTextEdit):
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.recording = False

    def set_current_pos(self, x, y):
        self.x = x
        self.y = y

    def keyPressEvent(self, e):
        if self.recording:
            if e.key() == Qt.Key_Up or e.key() == Qt.Key_Down:
                self.insertPlainText('(' + str(self.x) + ',' + str(self.y) + ',' + ('UP' if e.key() == Qt.Key_Up else 'DOWN') + ')')
            elif e.key() == Qt.Key_Right:
                self.insertPlainText('(' + str(self.x) + ',' + str(self.y) + ',' + 'CLICK' + ')') 
            elif e.key() == Qt.Key_Backslash:
                self.insertPlainText('(!)')
            else:
                self.insertPlainText('(' + QKeySequence(e.key()).toString() + ')')
        else:
            super().keyPressEvent(e)
        print(e)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cursor_thread = CursorInfo()
        self.cursor_thread.cursor_trace.connect(self.receive_cursor)
        self.is_recording = False
        self.srunner = script_runner.ScriptRunner()
        self.srunner.current_command_changed.connect(self.receive_command_info)
        self.heal_check_timer = QTimer()
        self.heal_check_timer.setInterval(1000)
        self.heal_check_timer.timeout.connect(self.heal_check)
        self.song = AudioSegment.from_wav("alarm.wav")
        self.use_mp_mode = False
        self.fill_mp_mode = False
        self.on_hp_potion = False
        self.last_mp_start_time = datetime.now()
        self.boost_mode = False
        self.keep_current_boost = False
        self.keep_press_key = False
        self.key_tmp_rl = False
        self.against_mode = False
        self.guard_time = datetime.now()
        self.enemy_time = None


    @pyqtSlot()
    def start_trace(self):
        if self.is_recording:
            self.record_button.setText('RECORD')
            self.cursor_thread.running = False
            self.is_recording = False
            self.edit_area.recording = False
            self.button_enable_while_record(True)
        else:
            self.record_button.setText('RECORDING...')
            self.cursor_thread.running = True
            self.cursor_thread.start()
            self.is_recording = True
            self.edit_area.recording = True
            self.button_enable_while_record(False)
            self.edit_area.setFocus()

    @pyqtSlot(str)
    def receive_command_info(self, command):
        self.extra_info.setText(command)

    @pyqtSlot(int,int)
    def receive_cursor(self, x, y):
        self.edit_area.set_current_pos(x, y)
        self.cursor_info.setText('x: ' + str(x) + '\ty: ' + str(y))

    @pyqtSlot()
    def clear_text(self):
        self.edit_area.clear()

    def button_enable_while_record(self, is_on):
        self.clear_button.setEnabled(is_on)
        self.start_button.setEnabled(is_on)
        self.load_button.setEnabled(is_on)
        self.save_button.setEnabled(is_on)
        self.capture_button.setEnabled(is_on)

    def button_enable_while_play(self, is_on):
        self.record_button.setEnabled(is_on)
        self.clear_button.setEnabled(is_on)
        self.load_button.setEnabled(is_on)
        self.save_button.setEnabled(is_on)
        self.capture_button.setEnabled(is_on)

    @pyqtSlot()
    def run_script(self):
        if self.srunner.running:
            self.srunner.running = False
            self.button_enable_while_play(True)
            self.start_button.setText('RUN')
        else:
            win = windep.WinDep()
            try:
                l, t, w, h = win.window_found(self.win_name.text())
            except:
                return
            if w == -1 and h == -1:
                QMessageBox.warning(self, 'ERROR', 'Cannot find window ' + self.win_name.text())
            else:
                self.srunner.set_script(self.edit_area.toPlainText())
                self.srunner.running = True 
                self.srunner.start()
                self.button_enable_while_play(False)
                self.start_button.setText('STOP')

    @pyqtSlot()
    def start_capture(self):
        win = windep.WinDep()
        try:
            l, t, w, h = win.window_found(self.win_name.text())
        except:
            return
        
        #print('window', l, t, w, h)
        if w == -1 and h == -1:
            QMessageBox.warning(self, 'ERROR', 'Cannot find window ' + self.win_name.text())
        else:
            win.window_width = w
            win.window_height = h
            im = win.capture(l, t)
            filename, file_ext = 'capture', 'jpeg'
            path = '.' + os.sep + '%s.%s' % (filename, file_ext)
            uniq = 1
            while os.path.exists(path):
                path = '.' + os.sep + '%s_%d.%s' % (filename, uniq, file_ext)
                uniq += 1
            im.save(path)
            self.extra_info.setText('SAVED AS ' + path)
    
    @pyqtSlot()
    def save_script(self):
        filename = QFileDialog.getSaveFileName(self, 'Save Script', '.' + os.sep + 'untitle.l2m', 'Script (*.l2m)')
        if filename:
            print(filename)
            script_file = open(filename[0], 'w')
            script_file.write(self.edit_area.toPlainText())
            script_file.close()

    @pyqtSlot()
    def load_script(self):
        filename = QFileDialog.getOpenFileName(self, 'Open Script', '.' + os.sep, 'Script (*.l2m)')
        if filename:
            print(filename)
            script_file = open(filename[0], 'r')
            script = script_file.read()
            print('SCRIPT', script)
            if script:
                self.edit_area.clear()
                self.edit_area.setText(script)
            script_file.close()

    def turn_on_guard(self):
        if datetime.now() - self.guard_time > timedelta(seconds=22):
            self.srunner.key_input(KEY_SHIELD)
            self.srunner.key_input(KEY_SHIELD)
            self.srunner.key_input(KEY_SHIELD)
            self.guard_time = datetime.now()


    def set_boost_mode(self, on):
        if self.keep_current_boost:
            return
            
        if self.boost_mode and not on:
            self.boost_mode = False
            self.srunner.key_input(',')
        elif not self.boost_mode and on:
            self.boost_mode = True
            self.srunner.key_input(',')

    def set_hp_potion(self, on):
        if self.on_hp_potion and not on:
            self.on_hp_potion = False
            self.srunner.key_input('.')
        elif not self.on_hp_potion and on:
            self.on_hp_potion = True
            self.srunner.key_input('.')


    def check_oneline_red(self, im, x1, x2, y):
        for i in range(x1, x2+1):
            r, g, b = im.getpixel((i, y))
            #print(r, g, b)
            if not (r >= 150 and g < 80 and b < 80):
                return False
            
        return True

    def check_box_white(self, im, x1, x2, y1, y2):
        for i in range(x1, x2+1):
            for j in range(y1, y2+1):
                r, g, b = im.getpixel((i, j))
                #print(r, g, b)
                if r < 180 or g < 130 or b < 130:
                    return False
                
        return True
        

    @pyqtSlot()
    def heal_check(self):
        win = windep.WinDep()
        try:
            l, t, w, h = win.window_found(self.win_name.text())
        except:
            return
            
        print('heal window', l, t, w, h)
        win.window_width = w
        win.window_height = h
        im = win.capture(l, t)
        step = 3
        start_x = 32
        step_x = (206 - start_x) / (100/step)
        current_hp, current_mp = 0, 0

        for i in range(int(100/step)):
            r, g, b = im.getpixel((int(32 + step_x * (i+1)), 28))
            #print(r, g, b, (int(32 + step_x * (i+1)), 28))
            if r > 120 and g < 100 and b < 100:
                current_hp += step
            else:
                break
                
        for i in range(int(100/step)):
            r, g, b = im.getpixel((int(32 + step_x * (i+1)), 43))
            print(r, g, b, (int(32 + step_x * (i+1)), 28))
            if b > 50:
                current_mp += step
            else:
                break
        print('hp', current_hp, 'mp', current_mp)
        enemy = False
        extra_info = ''
        cap = False

        if (self.check_oneline_red(im, 1103, 1106, 432) and
                self.check_oneline_red(im, 1103, 1106, 449) and 
                self.check_box_white(im, 1104, 1107, 440, 442)):
            enemy = True
            cap = True

        if current_hp == 0:
            return

        #enemy = False

        if self.keep_press_key and (0 < current_mp < 30 or current_hp <= 35):
            self.key_release()
            self.key_tmp_rl = True
        elif self.keep_press_key and self.key_tmp_rl and current_mp > 40 and current_hp > 45:
            self.key_press()
            self.key_tmp_rl = False

        if enemy:
            self.key_release()
            self.key_tmp_rl = True
            self.enemy_time = datetime.now()
            self.do_capture(im)
            self.srunner.key_input(KEY_ENEMY_ATTACK)
            self.srunner.key_input(KEY_ENEMY_ATTACK)
            self.srunner.key_input(KEY_ENEMY_ATTACK)
            self.srunner.key_input(KEY_ENEMY_ATTACK)
            

        heal_hp_level = 80
        
        if current_hp <= 20:
            self.srunner.key_input(KEY_HOME)
            cap = True
            play(self.song)
            self.autoheal_script()
        elif self.enemy_time is not None or current_hp <= 50:
            self.set_hp_potion(True)                    
            self.set_boost_mode(True)
            self.turn_on_guard()
            self.srunner.key_input(KEY_HEAL)
            self.srunner.key_input(KEY_HEAL)
            self.srunner.key_input(KEY_HEAL)
            self.srunner.key_input(KEY_GROUP_HEAL)
            self.srunner.key_input(KEY_GROUP_HEAL)
            self.srunner.key_input(KEY_GROUP_HEAL)
        elif current_hp <= heal_hp_level:
            self.srunner.key_input(KEY_HEAL)
        elif not enemy and current_hp >= 70:
            self.set_hp_potion(False)
            if current_mp > 50:
                self.set_boost_mode(False)

            if self.enemy_time is not None and datetime.now() - self.enemy_time > timedelta(seconds=30):
                self.enemy_time = None
                self.srunner.key_input(KEY_AUTO)


        extra_info = ' '

        if self.key_tmp_rl:
            extra_info += '(RL)'

        if enemy:
            extra_info += '(PK)'
        
        if self.on_hp_potion:
            extra_info += '(HP)'
        elif self.fill_mp_mode:
            extra_info += '(MP)'

        if self.boost_mode:
            extra_info += '(BOOST)'
            
        self.extra_info.setText('HP: ' + str(current_hp) + ' MP: ' + str(current_mp) + extra_info)
        if cap:
            self.do_capture(im)


    def do_capture(self, im):
        filename, file_ext = 'capture', 'jpeg'
        path = '.' + os.sep + '%s.%s' % (filename, file_ext)
        uniq = 1
        while os.path.exists(path):
            path = '.' + os.sep + '%s_%d.%s' % (filename, uniq, file_ext)
            uniq += 1
        im.save(path)

    @pyqtSlot(int)
    def mp_mode_changed(self, state):
        if state == Qt.Checked:
            self.use_mp_mode = True
        else:
            self.use_mp_mode = False

    @pyqtSlot(int)
    def keep_boost(self, state):
        if state == Qt.Checked:
            self.keep_current_boost = True
        else:
            self.keep_current_boost = False

    @pyqtSlot(int)
    def keep_press(self, state):
        if state == Qt.Checked and not self.keep_press_key:
            self.keep_press_key = True
        elif state == Qt.Unchecked and self.keep_press_key:
            self.keep_press_key = False

    @pyqtSlot()
    def autoheal_script(self):
        if self.heal_check_timer.isActive():
            self.key_release()
            self.heal_check_timer.stop()
            self.fill_mp_mode = False
            self.on_hp_potion = False
            self.last_mp_start_time = datetime.now()
            self.boost_mode = False
            self.key_tmp_rl = False
            self.enemy_time = None
            self.autoheal_button.setText('START AUTO HEAL')
        else:
            self.heal_check_timer.start()
            self.autoheal_button.setText('STOP AUTO HEAL')
            self.enemy_time = None

            if self.keep_press_key:
                win = windep.WinDep()
                try:
                    l, t, w, h = win.window_found(self.win_name.text())
                except:
                    return
                self.key_press()

    @pyqtSlot()
    def mouse_click(self):
        win = windep.WinDep()
        try:
            l, t, w, h = win.window_found(self.win_name.text())
        except:
            return
        #x1 = int(self.mouse_x_input.text())
        #y1 = int(self.mouse_y_input.text())
        time.sleep(1)
        self.srunner.mouse_click(l + 100, t + 10)
        

    @pyqtSlot()
    def mouse_swipe(self):
        x1 = int(self.mouse_x_input.text())
        y1 = int(self.mouse_y_input.text())
        x2 = int(self.mouse_x2_input.text())
        y2 = int(self.mouse_y2_input.text())
        self.srunner.mouse_swipe(x1, y1, x2, y2)

    @pyqtSlot()
    def key_press(self):
        k = self.key_input_edit.text()
        self.srunner.key_press(k)

    @pyqtSlot()
    def key_release(self):
        self.srunner.key_release()


    def init_ui(self):
        self.layout = QGridLayout()

        self.edit_area = RecordArea()


        self.info_area_layout = QVBoxLayout()
        self.cursor_info = QLabel()
        self.extra_info = QLabel()
        self.win_label = QLabel('Window name')
        self.win_name = QLineEdit()
        self.win_name.setText('LINEAGE2M')

        self.info_area_layout.addWidget(self.cursor_info)
        self.info_area_layout.addWidget(self.extra_info)
        self.info_area_layout.addWidget(self.win_label)
        self.info_area_layout.addWidget(self.win_name)

        self.mouse_test_layout = QHBoxLayout()
        self.mouse_x_input = QLineEdit()
        self.mouse_y_input = QLineEdit()
        self.mouse_x2_input = QLineEdit()
        self.mouse_y2_input = QLineEdit()
        self.mouse_click_button = QPushButton('Click')
        self.mouse_swipe_button = QPushButton('Swipe')
        self.mouse_test_layout.addWidget(self.mouse_x_input)
        self.mouse_test_layout.addWidget(self.mouse_y_input)
        self.mouse_test_layout.addWidget(self.mouse_x2_input)
        self.mouse_test_layout.addWidget(self.mouse_y2_input)
        self.mouse_x_input.setMaxLength(4)
        self.mouse_y_input.setMaxLength(4)
        self.mouse_x2_input.setMaxLength(4)
        self.mouse_y2_input.setMaxLength(4)
        self.mouse_test_layout.addWidget(self.mouse_click_button)
        self.mouse_test_layout.addWidget(self.mouse_swipe_button)

        self.key_area_layout = QHBoxLayout()
        self.key_input_edit = QLineEdit(KEY_ORA)
        self.key_input_edit.setMaxLength(1)
        self.press_key_button = QPushButton('Press')
        self.release_key_button = QPushButton('Release')
        self.key_area_layout.addWidget(self.key_input_edit)
        self.key_area_layout.addWidget(self.press_key_button)
        self.key_area_layout.addWidget(self.release_key_button)

        self.button_area_layout = QVBoxLayout()
        self.record_button = QPushButton('RECORD')
        self.clear_button = QPushButton('CLEAR')
        self.start_button = QPushButton('RUN')
        self.load_button = QPushButton('LOAD')
        self.save_button = QPushButton('SAVE')
        self.capture_button = QPushButton('CAPTURE')
        self.autoheal_button = QPushButton('START AUTO HEAL')
        self.swap_check = QCheckBox('MP MODE')
        self.boost_check = QCheckBox('KEEP CURRENT BOOST')
        self.press_check = QCheckBox('KEEP PRESS')

        self.mouse_click_button.clicked.connect(self.mouse_click)
        self.mouse_swipe_button.clicked.connect(self.mouse_swipe)

        self.press_key_button.clicked.connect(self.key_press)
        self.release_key_button.clicked.connect(self.key_release)

        self.record_button.clicked.connect(self.start_trace)
        self.clear_button.clicked.connect(self.clear_text)

        self.start_button.clicked.connect(self.run_script)
        self.capture_button.clicked.connect(self.start_capture)

        self.load_button.clicked.connect(self.load_script)
        self.save_button.clicked.connect(self.save_script)

        self.autoheal_button.clicked.connect(self.autoheal_script)

        self.swap_check.stateChanged.connect(self.mp_mode_changed)
        self.boost_check.stateChanged.connect(self.keep_boost)
        self.press_check.stateChanged.connect(self.keep_press)

        self.button_area_layout.addWidget(self.record_button)
        self.button_area_layout.addWidget(self.clear_button)
        self.button_area_layout.addWidget(self.start_button)
        self.button_area_layout.addWidget(self.load_button)
        self.button_area_layout.addWidget(self.save_button)
        self.button_area_layout.addWidget(self.capture_button)
        self.button_area_layout.addWidget(self.autoheal_button)
        self.button_area_layout.addWidget(self.swap_check)
        self.button_area_layout.addWidget(self.boost_check)
        self.button_area_layout.addWidget(self.press_check)


        self.layout.addWidget(self.edit_area, 0, 0, 4, 1)
        self.layout.addLayout(self.info_area_layout, 0, 1)
        self.layout.addLayout(self.mouse_test_layout, 1, 1)
        self.layout.addLayout(self.key_area_layout, 2, 1)
        self.layout.addLayout(self.button_area_layout, 3, 1)

        self.setLayout(self.layout)

