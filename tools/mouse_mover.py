import logging
import random
import time

import numpy as np
from configobj import ConfigObj

import pymouse
# from captcha.key_press_vbox import *
from tools.vbox_manager import VirtualBoxController
import win32gui
import win32api
import win32com.client
import keyboard 
import pyautogui

class MouseMover(VirtualBoxController):
    def __init__(self, whnd, vbox_mode):
        self.logger = logging.getLogger('mouse')
        self.logger.setLevel(logging.DEBUG)
        if vbox_mode:
            super().__init__()
        self.mouse=pymouse.PyMouse()
        self.whnd = whnd
        self.vbox_mode=vbox_mode
        self.old_x=int(np.round(np.random.uniform(0, 500, 1)))
        self.old_y=int(np.round(np.random.uniform(0, 500, 1)))
        self.bet_button = False

    def click(self, x, y):
        if self.vbox_mode:
            self.mouse_move_vbox(x, y)
            self.mouse_click_vbox(x, y)
        else:
            #win32api.SetCursorPos((x, y))
            # self.mouse.move(x, y)
            try:
                self.shell = win32com.client.Dispatch("WScript.Shell")
                self.shell.SendKeys('%')
                win32gui.SetForegroundWindow(self.whnd)
            except:
                self.mouse.click(x, y)
            self.mouse.click(x, y)

        # time.sleep(np.random.uniform(0.2, 0.3, 1)[0])

    def mouse_mover(self, x1, y1, x2, y2):
        speed = .01
        stepMin = 7
        stepMax = 50
        rd1 = int(np.round(np.random.uniform(stepMin, stepMax, 1)[0]))
        rd2 = int(np.round(np.random.uniform(stepMin, stepMax, 1)[0]))

        xa = list(range(x1, x2, rd1))
        ya = list(range(y1, y2, rd2))

        for k in range(0, max(0, len(xa) - len(ya))):
            ya.append(y2)
        for k in range(0, max(0, len(ya) - len(xa))):
            xa.append(x2)

        xTremble = 20
        yTremble = 20

        for i in range(len(max(xa, ya))):
            x = xa[i] + int(+random.random() * xTremble)
            y = ya[i] + int(+random.random() * yTremble)
            if self.vbox_mode:
                self.mouse_move_vbox(x, y)
                time.sleep(np.random.uniform(0.01 * speed, 0.03 * speed, 1)[0])
            else:
                self.mouse.move(x, y)
                time.sleep(np.random.uniform(0.01 * speed, 0.03 * speed, 1)[0])

        if self.vbox_mode:
            self.mouse_move_vbox(x2, y2)
        else:
            self.mouse.move(x2, y2)
            #win32api.SetCursorPos((x2, y2))

        self.old_x=x2
        self.old_y=y2

    def mouse_drag(self, xs, ys, buttonToleranceXs, buttonToleranceYs, xd, yd, buttonToleranceXd, buttonToleranceYd):
        xsrand = int(np.random.uniform(0, buttonToleranceXs, 1)[0])
        ysrand = int(np.random.uniform(0, buttonToleranceYs, 1)[0])
        xdrand = int(np.random.uniform(0, buttonToleranceXd, 1)[0])
        ydrand = int(np.random.uniform(0, buttonToleranceYd, 1)[0])
        self.mouse.press(xs + xsrand, ys + ysrand)
        # self.mouse.move(xd + xdrand, yd + ydrand)
        self.mouse.release(xd + xdrand, yd + ydrand)


    def mouse_clicker(self, x2, y2, buttonToleranceX, buttonToleranceY):
        xrand = int(np.random.uniform(0, buttonToleranceX, 1)[0])
        yrand = int(np.random.uniform(0, buttonToleranceY, 1)[0])
        if self.vbox_mode:
            self.mouse_move_vbox(x2 + xrand, y2 + yrand)
        else:
            self.mouse.move(x2 + xrand, y2 + yrand)

        # time.sleep(np.random.uniform(0.1, 0.2, 1)[0])
        # win32gui.SetForegroundWindow(self.whnd)0
        
        self.click(x2 + xrand, y2 + yrand)
        # self.logger.debug("Clicked: {0} {1}".format(x2 + xrand, y2 + yrand))

        # time.sleep(np.random.uniform(0.1, 0.5, 1)[0])

class MouseMoverTableBased(MouseMover):
    def __init__(self, pokersite, whnd):
        config = ConfigObj("config.ini")
        self.logger = logging.getLogger('mouse')
        self.whnd = whnd


        try:
            mouse_control = config['control']
            if mouse_control!='Direct mouse control': self.vbox_mode=True
            else: self.vbox_mode = False
        except:
            self.vbox_mode = False
            

        super().__init__(self.whnd, self.vbox_mode)

        # amount,pre-delay,x1,xy,x1tolerance,x2tolerance
        with open('resources/coordinates.json','r') as inf:
            c = eval(inf.read())
            coo=c['mouse_mover']

        self.coo=coo[pokersite[0:2]]

    def move_mouse_away_from_buttons(self):
        
        time.sleep(np.random.uniform(0.1, 0.3, 1)[0])
        if not self.vbox_mode: (x1, y1) = self.mouse.position()
        else:
            x1 = self.old_x
            y1 = self.old_y
        x1 = 10 if x1 > 2000 else x1
        y1 = 10 if y1 > 1000 else y1

        x2 = int(np.round(np.random.uniform(100, 200, 1), 0)[0]) + x1
        y2 = int(np.round(np.random.uniform(100, 200, 1), 0)[0]) + y1


        try:
            # self.logger.debug("Moving mouse away: "+str(x1)+","+str(y1)+","+str(x2)+","+str(y2))
            self.mouse_mover(x1, y1, x2, y2)
        except Exception as e:
            self.logger.warning("Moving mouse away failed" + str(e))

    def move_mouse_away_from_buttons_jump(self):
        x2 = int(np.round(np.random.uniform(1400, 1800, 1), 0)[0])
        y2 = int(np.round(np.random.uniform(10, 200, 1), 0)[0])

        try:
            # self.logger.debug("Moving mouse away via jump: "+str(x2)+","+str(y2))
            if self.vbox_mode:
                self.mouse_move_vbox(x2, y2)
            else:
                self.mouse.move(x2, y2)
        except Exception as e:
            self.logger.warning("Moving mouse via jump away failed"+str(e))

    def enter_captcha(self, captchaString, topleftcorner):
        # self.logger.warning("Entering Captcha: " + str(captchaString))
        buttonToleranceX = 30
        buttonToleranceY = 0
        tlx = topleftcorner[0]
        tly = topleftcorner[1]
        if not self.vbox_mode: (x1, y1) = self.mouse.position()
        else:
            x1=self.old_x
            y1=self.old_y
        x2 = 30 + tlx
        y2 = 565 + tly
        self.mouse_mover(x1, y1, x2, y2)
        self.mouse_clicker(x2, y2, buttonToleranceX, buttonToleranceY)
        try:
            write_characters_to_virtualbox(captchaString, "win")
        except:
            self.logger.info("Captcha Error")
    # add by gc 4/1
    def mouse_action(self, decision, topleftcorner,bet_val = 0):

        
        if decision == 'emoji': active_emoji = topleftcorner
        if decision == 'Check Deception': decision = 'Check'
        if decision == 'Call Deception': decision = 'Call'
        if decision == 'Bet Bluff':
            if bet_val == 1:
                decision = 'Bet 1/2 POT'
            elif bet_val ==2:
                decision = 'Bet 2/3 POT'
            elif bet_val ==3:
                decision = 'Bet pot'
            elif bet_val ==0:
                decision = 'Bet'
        
        if bet_val == 1:
            if decision == 'Bet Bluff' or decision == 'Bet pot' or decision == 'Bet 1/2 POT':
                decision = 'Bet 1/2 POT'
        elif bet_val ==2:
            if decision == 'Bet Bluff' or decision == 'Bet pot':
                decision = 'Bet 2/3 POT'
        elif bet_val ==3:
            if decision == 'Bet Bluff':
                decision = 'Bet pot'
        elif bet_val ==0:
            if decision == 'Bet Bluff' or decision == 'Bet pot' or decision == 'Bet 1/2 POT' or decision == 'Bet 2/3 POT':
                decision = 'Bet'
            # decision = 'Call'
        # else:
            # decision = 'Fold'
        if not self.bet_button and decision == 'Bet':
            decision = 'Call'
        tlx = int(topleftcorner[0])
        tly = int(topleftcorner[1])
        # decision = "Precise bet"
        # self.logger.info("Mouse moving to: "+decision)
        
        self.move_mouse_away_from_buttons()
        bet_action = self.coo['Bet'][0]
        if decision == "All In":
            for action in self.coo[decision]:
                for i in range (int(action[0])):
                    if not self.vbox_mode:
                        (x1, y1) = self.mouse.position()
                    else:
                        x1 = self.old_x
                        y1 = self.old_y
                    self.mouse_mover(x1, y1, action[2]+ tlx, action[3]+ tly)
                    self.mouse_clicker(action[2]+ tlx, action[3]+ tly,action[4], action[5])
                    try:
                        win32api.SetCursorPos((x1, y1))
                    except:
                        pass
                    sleep(0.1)
                    self.mouse_clicker(bet_action[2]+ tlx, bet_action[3]+ tly,bet_action[4], bet_action[5])
                    # pyautogui.press('f3')
        elif decision == "Fold":
            pyautogui.press('f1')
        elif decision == "Check" or decision == "Call":
            pyautogui.press('f2')
        else:
            for action in self.coo[decision]:
                for i in range (int(action[0])):
                    time.sleep(np.random.uniform(0, action[1], 1)[0])
                    # self.logger.debug("Mouse action:"+str(action))
                    if not self.vbox_mode:
                        (x1, y1) = self.mouse.position()
                    else:
                        x1 = self.old_x
                        y1 = self.old_y
                    # self.mouse_mover(x1, y1, action[2]+ tlx, action[3]+ tly)
                    self.mouse_clicker(action[2]+ tlx, action[3]+ tly,action[4], action[5])
                    try:
                        win32api.SetCursorPos((x1, y1))
                    except:
                        pass
            self.mouse_clicker(bet_action[2]+ tlx, bet_action[3]+ tly,bet_action[4], bet_action[5])
            # pyautogui.press('f3')
                    # if decision == "Precise bet":
                    #     # bet_val = 10
                    #     precise_str = str(bet_val) + "\n"
                    #     keyboard.write(precise_str) 
                        # pricese_suit = "123456789d0"
                        # for num in precise_str:
                        #     num = num.replace(".","11")    
                        #     for action in self.coo["Precise pos"]:
                        #         if num == str(action[0]):
                        #             time.sleep(np.random.uniform(0, action[1], 1)[0])
                        #             # self.logger.debug("Mouse action:"+str(action))
                        #             if not self.vbox_mode:
                        #                 (x1, y1) = self.mouse.position()
                        #             else:
                        #                 x1 = self.old_x
                        #                 y1 = self.old_y
                        #             # x2 = 30 + tlx
                        #             # self.mouse_mover(x1, y1, action[2]+ tlx, action[3]+ tly)
                        #             self.mouse_clicker(action[2]+ tlx, action[3]+ tly,action[4], action[5])
                        # action = self.coo["Precise Confirm"]
                        # # self.mouse_mover(x1, y1, action[2]+ tlx, action[3]+ tly)
                        # self.mouse_clicker(action[0][2]+ tlx, action[0][3]+ tly,action[0][4], action[0][5])
                    # self.mouse_mover(action[2]+ tlx, action[3]+ tly, x1, y1)
        # time.sleep(0.2)


                
    # def mouse_action(self, decision, topleftcorner):
    #     if decision == 'Check Deception': decision = 'Check'
    #     if decision == 'Call Deception': decision = 'Call'

    #     tlx = int(topleftcorner[0])
    #     tly = int(topleftcorner[1])
    #     win32gui.SetForegroundWindow(self.whnd)
    #     self.logger.info("Mouse moving to: "+decision)
    #     for action in self.coo[decision]:
    #         for i in range (int(action[0])):
    #             time.sleep(np.random.uniform(0, action[1], 1)[0])
    #             self.logger.debug("Mouse action:"+str(action))
    #             if not self.vbox_mode:
    #                 (x1, y1) = self.mouse.position()
    #             else:
    #                 x1 = self.old_x
    #                 y1 = self.old_y
    #             x2 = 30 + tlx
    #             self.mouse_mover(x1, y1, action[2]+ tlx, action[3]+ tly)
    #             self.mouse_clicker(action[2]+ tlx, action[3]+ tly,action[4], action[5])
    #             self.mouse_mover(action[2]+ tlx, action[3]+ tly, x1, y1)

    #     time.sleep(0.2)
    #     # self.move_mouse_away_from_buttons()

# if __name__=="__main__":
    # logger = logging.getLogger()
    # m=MouseMoverTableBased('PP',5,5)
    # topleftcorner=[22,22]
    # m.mouse_action(logger, topleftcorner)