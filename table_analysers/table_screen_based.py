import datetime
import inspect
import re
import sys
import threading
import time
import cv2  # opencv 3.0
import numpy as np
import pytesseract
from PIL import Image, ImageFilter
from copy import copy
import operator
import collections
from decisionmaker.montecarlo_python import MonteCarlo
from tools.mouse_mover import MouseMoverTableBased
from table_analysers.base import Table
import win32gui, win32ui, win32con

log_path = r'D:\Poker_Bot\winamax_bot\screenshot_log\log_{}.png'

class TableScreenBased(Table):
    def get_top_left_corner(self, p):
        self.current_strategy = p.current_strategy  # needed for mongo manager
        # self.tlc = points[0]
        # self.logger.debug("Top left corner found")
        self.timeout_start = datetime.datetime.utcnow()
        self.mt_tm = time.time()
        return True
        # img = cv2.cvtColor(np.array(self.entireScreenPIL), cv2.COLOR_BGR2RGB)
        # count, points, bestfit, _ = self.find_template_on_screen(self.topLeftCorner, img, 0.01)
        # try:
        #     count2, points2, bestfit2, _ = self.find_template_on_screen(self.topLeftCorner2, img, 0.01)
        #     if count2 == 1:
        #         count = 1
        #         points = points2
        # except:
        #     pass

        # if count == 1:
            # self.tlc = points[0]
            # self.logger.debug("Top left corner found")
            # self.timeout_start = datetime.datetime.utcnow()
            # self.mt_tm = time.time()
            # return True
        # else:

        #     self.gui_signals.signal_status.emit(self.tbl + " not found yet")
        #     self.gui_signals.signal_progressbar_reset.emit()
        #     self.logger.debug("Top left corner NOT found")
        #     time.sleep(1)
        #     return False
    
    def check_for_pot_bet_button(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        cards = ' '.join(self.mycards)
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        betbtn = {}
        suit = "fst"
        total_count = 0
        for n in suit:
            name = "pics/" + self.tbl[0:2] + "/buttons/" + n + ".png"
            template = Image.open(name)
            btn_template = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            count, points, bestfit, _ = self.find_template_on_screen(btn_template, img, 0.01)
            
            if count > 0:
                betbtn.update({
                  n:1  
                })
                total_count += 1
            else:
                betbtn.update({
                  n:0  
                })
        # count, points, bestfit, _ = self.find_template_on_screen(self.button, img, func_dict['tolerance'])
        # for i in suit:
        #     if betbtn[i] == 1:
        #         print(i + ":btn exist!")
        #     else:
        #         print(i + ":btn does not exist!")
        self.potbetbutton = total_count
        if total_count > 0:
            self.gui_signals.signal_status.emit("Pot Bet Buttons found  " + str(total_count) + 's')
            # self.logger.info("Pot Bet Buttons found  " + str(betbtn) + 's')
            return True
        else:
            # self.logger.debug("No buttons found")
            return True
    
    def check_for_button(self):
        self.check_for_checkbutton()
        self.check_for_allincall()
        self.check_for_call()
        if self.checkButton or self.callButton or self.allInCall:
            self.bonatablemodel.setIdle(False)
            self.table_model_data['status'] = 1
            path = log_path.format(datetime.datetime.now().strftime("%d%m%Y%H%M%S"))
            self.entireScreenPIL.save(path)
            print('save screenshot file: ', path)
            # print("I am working now :  " + self.bonatablemodel.table_title + str(self.table_model_data['whnd']) )
            # print("I am working now :  " + self.bonatablemodel.table_title + str(self.table_model_data['mycard']) )
            return True
        else:
            return True

        # func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # self.gui_signals.signal_progressbar_increase.emit(5)
        # cards = ' '.join(self.mycards)
        # pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
        #                             func_dict['x2'], func_dict['y2'])
        # img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        # count, points, bestfit, _ = self.find_template_on_screen(self.button, img, func_dict['tolerance'])

        # if count > 0:
        #     self.gui_signals.signal_status.emit("Buttons found, cards: " + str(cards))
        #     # self.logger.info("Buttons Found, cards: " + str(cards))
        #     return True

        # else:
        #     # self.logger.debug("No buttons found")
        #     return False

    def check_for_checkbutton(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_status.emit("Check for Check")
        self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Checking for check button")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        count, points, bestfit, minval = self.find_template_on_screen(self.check, img, func_dict['tolerance'])

        if count > 0:
            self.checkButton = True
            self.currentCallValue = 0.0
            # self.logger.debug("check button found")
        else:
            self.checkButton = False
            # self.logger.debug("no check button found")
        # self.logger.debug("Check: " + str(self.checkButton))
        return True

    def check_for_captcha(self, mouse):
        # func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # if func_dict['active']:
        #     ChatWindow = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
        #                             func_dict['x2'], func_dict['y2'])
        #     basewidth = 500
        #     wpercent = (basewidth / float(ChatWindow.size[0]))
        #     hsize = int((float(ChatWindow.size[1]) * float(wpercent)))
        #     ChatWindow = ChatWindow.resize((basewidth, hsize), Image.ANTIALIAS)
        #     # ChatWindow.show()
        #     try:
        #         t.chatText = (pytesseract.image_to_string(ChatWindow, None,
        #         False, "-psm 6"))
        #         t.chatText = re.sub("[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\.]",
        #         "", t.chatText)
        #         keyword1 = 'disp'
        #         keyword2 = 'left'
        #         keyword3 = 'pic'
        #         keyword4 = 'key'
        #         keyword5 = 'lete'
        #         self.logger.debug("Recognised text: "+t.chatText)
        #
        #         if ((t.chatText.find(keyword1) > 0) or (t.chatText.find(keyword2)
        #         > 0) or (
        #                     t.chatText.find(keyword3) > 0) or
        #                     (t.chatText.find(keyword4) > 0) or (
        #                     t.chatText.find(keyword5) > 0)):
        #             self.logger.warning("Submitting Captcha")
        #             captchaIMG = self.crop_image(self.crop_image(self.entireScreenPIL, func_dict['x1_2'], func_dict['y1_2'],
        #                             func_dict['x2_2'], func_dict['y2_2']))
        #             captchaIMG.save("pics/captcha.png")
        #             # captchaIMG.show()
        #             time.sleep(0.5)
        #             t.captcha = solve_captcha("pics/captcha.png")
        #             mouse.enter_captcha(t.captcha)
        #             self.logger.info("Entered captcha: "+str(t.captcha))
        #     except:
        #         self.logger.warning("CheckingForCaptcha Error")
        return True

    def check_for_imback(self, mouse):
        if self.tbl == 'SN': return True
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        # Convert RGB to BGR
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        count, points, bestfit, minvalue = self.find_template_on_screen(self.ImBack, img, func_dict['tolerance'])
        if count > 0:
            self.gui_signals.signal_status.emit("I am back found")
            mouse.mouse_action("Imback", self.tlc)
            return False
        else:
            return True

    def check_for_call(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Check for Call")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        count, points, bestfit, _ = self.find_template_on_screen(self.call, img, func_dict['tolerance'])
        if count > 0:
            self.callButton = True
            # self.logger.debug("Call button found")
        else:
            self.callButton = False
            # self.logger.info("Call button NOT found")
            # pil_image.save("pics/debug_nocall.png")
        return True

    def check_for_betbutton(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Check for betbutton")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        count, points, bestfit, _ = self.find_template_on_screen(self.betbutton, img, func_dict['tolerance'])
        if count > 0:
            self.betButton = True
            self.allInCall = False
            self.raiseButton = False
            self.allinButton = False
            # self.logger.debug("Bet button found")
        else:
            self.betButton = False
            count, points, bestfit, _ = self.find_template_on_screen(self.raisebutton, img, func_dict['tolerance'])
            if count > 0:
                self.raiseButton = True
                self.allInCall = False
                self.allinButton = False
                # self.logger.debug("Raise button found")
            else:
                self.raiseButton = False
                count, points, bestfit, _ = self.find_template_on_screen(self.allin, img, func_dict['tolerance'])
                if count > 0:
                    self.allinButton  = True
                else:
                    self.allinButton = False
                # self.logger.info("Bet and Raise button NOT found")
        return True
    
    def check_for_allincall(self):

        # if not self.bet_button_found:
        #     self.allInCall = True
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # self.logger.debug("Check for All in call button")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        # Convert RGB to BGR
        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        count, points, bestfit, _ = self.find_template_on_screen(self.allInCallButton, img, 0.01)
        if count > 0:
            self.allInCall = True
            # self.logger.debug("All in call button found")
        else:
            self.allInCall = False
            # self.logger.debug("All in call button not found")

        # if not self.bet_button_found:
        #     self.allInCall = True
        #     # self.logger.debug("Assume all in call because there is no bet button")

        return True

    def get_table_cards(self, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Get Table cards")
        self.oldcardsOnTable = self.cardsOnTable
        self.cardsOnTable = []
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])

        img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)

        card_images = self.tablecardImages

        for key, value in card_images.items():
            template = value
            method = eval('cv2.TM_SQDIFF_NORMED')
            res = cv2.matchTemplate(img, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if min_val < 0.0017:
                self.cardsOnTable.append(key)
        print("--- Table Cards ---", self.cardsOnTable)
        # add by zq 2020/3/24
        # self.gameStage = 'PreFlop'
        # if len(self.cardsOnTable) > 0:
        #     print(str(self.cardsOnTable))
        # saved screen shot file
        # cv2.imwrite(self.path, self.entireScreenPIL)
        # if self.oldpath != self.path and len(self.oldcardsOnTable) != len(self.cardsOnTable):
        #     self.entireScreenPIL.save(self.path)
        #     print(self.path + '    file saved')
        #     self.oldpath = self.path

        if len(self.cardsOnTable) < 1:
            self.gameStage = "PreFlop"
        elif len(self.cardsOnTable) == 3:
            self.gameStage = "Flop"
        elif len(self.cardsOnTable) == 4:
            self.gameStage = "Turn"
        elif len(self.cardsOnTable) == 5:
            self.gameStage = "River"
        # add by zq 2020/3/24
        # self.gameStage = 'PreFlop'

        if self.gameStage == '':
            # self.logger.critical("Table cards not recognised correctly: " + str(len(self.cardsOnTable)))
            self.gameStage = "River"
        print('--- Current Game Stage --- ', self.gameStage)
        # self.logger.info("---")
        # self.logger.info("Gamestage: " + self.gameStage)
        # self.logger.info("Cards on table: " + str(self.cardsOnTable))
        # self.logger.info("---")

        self.max_X = 1 if self.gameStage != 'PreFlop' else 0.86

        return True

    def check_fast_fold(self, h, p, mouse):
        # if h.fastfold == True:
        #     return True
        # elif not self.check_for_button() and h.fastfold == True:
        #     return False
        if p.selected_strategy['preflop_override'] and self.gameStage == "PreFlop":
            m = MonteCarlo()
            crd1, crd2 = m.get_two_short_notation(self.mycards)
            crd1 = crd1.upper()
            crd2 = crd2.upper()
            hand_range_level = 9
            # allowed_cards = m.get_opponent_allowed_cards_list(0.5)
            tier = [
                ["AA", "AKS", "AKO", "AQS", "AQO", "AJS", "KK", "QQ"],
                ["AJO", "ATS", "ATO", "KQS", "KQO", "KJS", "QJS", "JJ", "TT"],
                ["A9S", "A8S", "KJO", "KTS", "QJO", "QTS", "JTS", "99", "88", "77"],
                ["A7S", "A6S", "A5S", "KTO", "K9S", "QTO", "Q9S", "JTO", "J9S", "T9S", "66", "55", "44", "33", "22"],
                ["A9O", "A8O", "A4S", "A3S", "A2S", "J9O", "T9O", "T8S", "98S"],
                ["A7O", "A6O", "A5O", "A4O", "K9O", "K8S", "K7S", "K6S", "K5S", "Q9O", "Q8S", "J8S", "87S"],
                ["A3O", "A2O", "K4S", "K3S", "K2S", "J7S", "T8O", "T7S", "98O", "97S", "76S"],
                ["Q8O", "Q7S", "Q6S", "Q5S", "Q4S", "Q3S", "Q2S", "J8O", "T6S", "97O", "96S", "87O", "86S", "76O", "75S", "65S"],
                ["T7O", "96O", "95S", "86O", "75O", "65O", "64S", "64O", "63S", "54S", "54O", "53S"],
            ]

            allowed_cards = set()
            for i in range(hand_range_level):
                allowed_cards.update(tier[i])

            # 1. "AA", "AKS", "AKO", "AQS", "AQO", "AJS", "KK", "QQ"
            # 2. "AJO", "ATS", "ATO", "KQS", "KQO", "KJS", "QJS", "JJ", "TT"
            # 3. "A9S", "A8S", "KJO", "KTS", "QJO", "QTS", "JTS", "99", "88", "77" 
            # 4. "A7S", "A6S", "A5S", "KTO", "K9S", "QTO", "Q9S", "JTO", "J9S", "T9S", "66", "55", "44", "33", "22"
            # 5. "A9O", "A8O", "A4S", "A3S", "A2S", "J9O", "T9O", "T8S", "98S"
            # 6. "A7O", "A6O", "A5O", "A4O", "K9O", "K8S", "K7S", "K6S", "K5S", "Q9O", "Q8S", "J8S", "87S"
            # 7. "A3O", "A2O", "K4S", "K3S", "K2S", "J7S", "T8O", "T7S", "98O", "97S", "76S"
            # 8. "Q8O", "Q7S", "Q6S", "Q5S", "Q4S", "Q3S", "Q2S", "J8O", "T6S", "97O", "96S", "87O", "86S", "76O", "75S", "65S"
            # 9. "T7O", "96O", "95S", "86O", "75O", "65O", "64S", "64O", "63S", "54S", "54O", "53S"
            # sheet_name = str(self.position_utg_plus + 1)
            # if int(sheet_name) > 5: return True
            # sheet = h.preflop_sheet[sheet_name]
            # sheet['Hand'] = sheet['Hand'].apply(lambda x: str(x).upper())
            # handlist = set(sheet['Hand'].tolist())

            found_card = ''

            if crd1 in allowed_cards:
                found_card = crd1
            elif crd2 in allowed_cards:
                found_card = crd2
            elif crd1[0:2] in allowed_cards:
                found_card = crd1[0:2]

            if found_card == '' and h.fastfold == False:
                if self.checkButton:
                    mouse_target = "Check"
                    mouse.mouse_action(mouse_target, self.tlc)
                    self.bonatablemodel.setIdle(True)
                    self.table_model_data['decision'] = 'Check'
                    self.table_model_data['status'] = 1
                    print("+++++++ Current Table Title :   " + str(self.bonatablemodel.table_title) + "     ++++++++++++++++")
                    print(" My Cards :   " + str(self.mycards))
                    print("Fast Fold Action is check")
                    time.sleep(3)
                else:
                    mouse_target = "Fold"
                    mouse.mouse_action(mouse_target, self.tlc)
                    self.bonatablemodel.setIdle(True)
                    self.table_model_data['decision'] = 'Fold'
                    self.table_model_data['status'] = 0
                    print("+++++++ Current Table Title :   " + str(self.bonatablemodel.table_title) + "     ++++++++++++++++")
                    print(" My Cards :   " + str(self.mycards))
                    print("Fast Fold")
                    time.sleep(3)
                h.fastfold = True
                return False
            # else:
            #     return self.check_for_button()
            # elif h.fastfold == True:
                # self.check_for_checkbutton()
                # if self.checkButton:
                #     mouse_target = "Check"
                #     mouse.mouse_action(mouse_target, self.tlc)
                # self.check_for_call()
                # # self.check_for_allincall()
                # if self.callButton:
                #     mouse_target = "Fold"
                #     mouse.mouse_action(mouse_target, self.tlc)
                # return True
        if self.checkButton or self.callButton or self.allInCall:
            return True
        else:
            return False

    def get_my_cards(self, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]

        def go_through_each_card(img, debugging):
            dic = {}
            for key, value in self.mycardImages.items():
                template = value
                method = eval('cv2.TM_SQDIFF_NORMED')

                res = cv2.matchTemplate(img, template, method)

                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                if min_val < 0.01:# 
                    self.mycards.append(key)
                dic[key] = min_val

                if debugging:
                    pass
                    # dic = sorted(dic.items(), key=operator.itemgetter(1))
                    # self.logger.debug(str(dic))
            # print(dic)
            return self.mycards

        self.gui_signals.signal_progressbar_increase.emit(5)
        self.mycards = []
        self.my_position = 0
        for i, fd in enumerate(func_dict, start=0):
            self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
                                            fd[2], fd[3])
            # pil_image.show()
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            # (thresh, img) = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY |
            # cv2.THRESH_OTSU)
            cards = go_through_each_card(img, False)
            if len(cards) > 1:
                self.my_position = i
                break
        # if len(self.mycards) == 2:
            # print(str(self.mycards))

        if len(self.mycards) == 2:
            # self.logger.info("My cards: " + str(self.mycards))
            self.table_model_data['mycard'] = self.mycards
            print("--- My Cards --- ", self.mycards)
            
            # print(' Now Table is working : ' + str(self.whnd) + str(self.mycards))
            return True
        else:
            # self.logger.debug("Did not find two player cards: " + str(self.mycards))
            go_through_each_card(img, True)
            return False

    def init_get_other_players_info(self):
        other_player = dict()
        other_player['utg_position'] = ''
        other_player['name'] = ''
        other_player['status'] = ''
        other_player['funds'] = ''
        other_player['pot'] = ''
        other_player['decision'] = ''
        other_player['empty'] = ''
        self.other_players = []
        for i in range(self.sit_count - 1):
            op = copy(other_player)
            op['abs_position'] = i
            self.other_players.append(op)

        return True

    def get_other_player_names(self, p):
        if p.selected_strategy['gather_player_names'] == 1:
            func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
            self.gui_signals.signal_status.emit("Get player names")

            for i, fd in enumerate(func_dict):
                self.gui_signals.signal_progressbar_increase.emit(2)
                pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
                                            fd[2], fd[3])
                basewidth = 500
                wpercent = (basewidth / float(pil_image.size[0]))
                hsize = int((float(pil_image.size[1]) * float(wpercent)))
                pil_image = pil_image.resize((basewidth, hsize), Image.ANTIALIAS)
                try:
                    recognizedText = (pytesseract.image_to_string(pil_image, None, False, "-psm 6"))
                    recognizedText = re.sub(r'[\W+]', '', recognizedText)
                    # self.logger.debug("Player name: " + recognizedText)
                    self.other_players[i]['name'] = recognizedText
                except Exception as e:
                    self.logger.debug("Pyteseract error in player name recognition: " + str(e))
        return True

    def get_other_player_funds(self, p):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]
        self.gui_signals.signal_status.emit("Get player funds")
        for i, fd in enumerate(func_dict, start=0):
            self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
                                        fd[2], fd[3])
            points_x = {}
            suits="0123456789dk"
            for j in suits :
                name = "pics/" + self.tbl[0:2] + "/funds_number/" + j + ".png"
                template = Image.open(name)
                self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
                count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.14)
                if count != 0:
                    for point in points:    
                        points_x.update({
                            point[0]:j
                            })
            # if i < round(self.sit_count / 2) and round((self.sit_count - 5)/2) < i:
            #     name = "pics/" + self.tbl[0:2] + "/pot_number/r.png"
            #     template = Image.open(name)
            #     self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            #     img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            #     count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.05)
            #     if count != 0:
            #         points_x.update({
            #             points[0][0]:'d'
            #             })
            # test = ""
            # sorted_d = sorted(points_x.items(), key=operator.itemgetter(1))
            sorted_d = collections.OrderedDict(sorted(points_x.items()))
            value = ""
            # for val in sorted_d:
            #     val = val[0].replace("d",".")
            #     value += val
            exist_dot = False
            for val in sorted_d.values():
                if val == "d":
                    if not exist_dot:
                        val = "."
                        exist_dot = True
                    else:
                        val =""
                value += val
            #Kilo detect
            kilo = 1
            if value.find('k') == len(value) - 1:
                kilo = 1000
                value = value.replace('k','')
            if value == '':
                value = 0
            else:
                value = float(value) * kilo
            # if value != '': 
            #     value = float(value) 
            # else:
            #     value = 0
            # if i == 1:
            #     value = value/100
            self.other_players[i]['funds'] = value
            print("other player funds: ", value)
        return True
        # if p.selected_strategy['gather_player_names'] == 1:
        #     func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        #     self.gui_signals.signal_status.emit("Get player funds")
        #     for i, fd in enumerate(func_dict, start=0):
        #         self.gui_signals.signal_progressbar_increase.emit(1)
        #         pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
        #                                     fd[2], fd[3])
        #         # pil_image.show()
        #         value = self.get_ocr_float(pil_image, str(inspect.stack()[0][3]))
        #         value = float(value) if value != '' else ''
        #         self.other_players[i]['funds'] = value
        # return True
    def get_empty_status(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]
        self.gui_signals.signal_status.emit("Get other playsrs' status")

        self.playing_players = 1
        for i, fd in enumerate(func_dict, start=0):
            self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
                                        fd[2], fd[3])
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, minvalue = self.find_template_on_screen(self.user_status, img, 0.04)
            # self.logger.debug("Player status: " + str(i) + ": " + str(count))
            if self.sit_count == 2:
                if not count > 0:
                    self.other_players[0]['empty'] = 1
                else:
                    self.playing_players += 1
                    self.other_players[0]['empty'] = 0
            else:
                if not count > 0:
                    self.other_players[i]['empty'] = 1
                else:
                    self.playing_players += 1
                    self.other_players[i]['empty'] = 0
        print( " Now in this table playing player :   " + str(self.playing_players)) 
        self.bonatablemodel.playing_players = self.playing_players
        return True


    def get_other_player_pots(self):
       
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]
        self.gui_signals.signal_status.emit("Get other player pots")
        for i, fd in enumerate(func_dict, start=0):
            # self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],fd[2], fd[3])
            points_x = {}
            suits="0123456789dk"
            for j in suits :
                name = "pics/" + self.tbl[0:2] + "/otherplayers_potnumber/" + j + ".png"
                template = Image.open(name)
                pots = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
                # max_output_value = 255 
                # neighborhood_size = 99
                # subtract_from_mean = 10
                # image_binarized = cv2.adaptiveThreshold(img,
                #                                 max_output_value,
                #                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                #                                 cv2.THRESH_BINARY,
                #                                 neighborhood_size,
                #                                 subtract_from_mean)
                # plt.imshow(image_binarized, cmap='gray')
                # plt.show()
                count, points, bestfit, _ = self.find_template_on_screen(pots, img, 0.04)
                if count != 0:
                    for point in points:    
                        points_x.update({
                            point[0]:j
                            })
            
            sorted_d = collections.OrderedDict(sorted(points_x.items()))
            value = ""
            
            for val in sorted_d.values():
                # val = val.replace("d",".")#.replace("r",".")
                value += val
            # print(i)
            # print(value)
            # Find spot is not '.'
            if value.find('d') == len(value) - 4 or value.find('d') == len(value) - 7:
                value = value.replace('d','', 1)
            else:
                value = value.replace('d','.', 1)
            
            #Kilo detect
            kilo = 1
            if value.find('k') == len(value) - 1:
                kilo = 1000
                value = value.replace('k','')
            
            if value != '': 
                try:
                    value = float(value)  * kilo
                except:
                    value =0

            else:
                value = 0
            # if i == 1:
            #     value = value/100
            self.other_players[i]['pot'] = value
            # print("----other player pots:---")
            # print(value)
        return True
        # func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # self.gui_signals.signal_status.emit("Get player pots")
        # for n in range(5):
        #     fd = func_dict[n]
        #     self.gui_signals.signal_progressbar_increase.emit(1)
        #     pot_area_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
        #                                      fd[2], fd[3])
        #     img = cv2.cvtColor(np.array(pot_area_image), cv2.COLOR_BGR2RGB)
        #     count, points, bestfit, minvalue = self.find_template_on_screen(self.smallDollarSign1, img,
        #                                                                     float(func_dict[5]))
        #     has_small_dollarsign = count > 0
        #     if has_small_dollarsign:
        #         pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
        #                                     fd[2], fd[3])
        #         method = func_dict[6]
        #         value = self.get_ocr_float(pil_image, str(inspect.stack()[0][3]), force_method=method)
        #         try:
        #             if not str(value) == '':
        #                 value = re.findall(r'\d{1}\.\d{1,2}', str(value))[0]
        #         except:
        #             self.logger.warning("Player pot regex problem: " + str(value))
        #             value = ''
        #         value = float(value) if value != '' else ''
        #         self.logger.debug("FINAL POT after regex: " + str(value))
        #         self.other_players[n]['pot'] = value
        # return True

    def get_bot_pot(self, p):
        fd = self.coo[inspect.stack()[0][3]][self.tbl]
        pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1], fd[2],
                                    fd[3])
        # value = self.get_ocr_float(pil_image, str(inspect.stack()[0][3]), force_method=1)
        # try:
        #     value = float(re.findall(r'\d{1}\.\d{1,2}', str(value))[0])
        # except:
        #     # self.logger.debug("Assuming bot pot is 0")
        #     value = 0
        points_x = {}
        suits="0123456789dk"
        for j in suits :
            name = "pics/" + self.tbl[0:2] + "/otherplayers_potnumber/" + j + ".png"
            template = Image.open(name)
            pots = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, _ = self.find_template_on_screen(pots, img, 0.04)
            if count != 0:
                for point in points:    
                    points_x.update({
                        point[0]:j
                        })
        
        sorted_d = collections.OrderedDict(sorted(points_x.items()))
        value = ""
        
        for val in sorted_d.values():
            # val = val.replace("d",".")#.replace("r",".")
            value += val
        if value.find('d') == len(value) - 4 or value.find('d') == len(value) - 7:
            value = value.replace('d','', 1)
        else:
            value = value.replace('d','.', 1)
        #Kilo detect
        kilo = 1
        if value.find('k') == len(value) - 1:
            kilo = 1000
            value = value.replace('k','')

        if value != '': 
            try:
                value = float(value) * kilo
            except:
                value =0

        else:
            value = 0
        # if i == 1:
        #     value = value/100
        self.bot_pot = value
        return value

    def get_other_player_status(self, p, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]
        self.gui_signals.signal_status.emit("Get other playsrs' status")

        self.covered_players = 0
        for i, fd in enumerate(func_dict, start=0):
            self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],
                                        fd[2], fd[3])
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, minvalue = self.find_template_on_screen(self.user_status, img, 0.01)
            # self.logger.debug("Player status: " + str(i) + ": " + str(count))
            if count > 0:
                self.covered_players += 1
                self.other_players[i]['status'] = 1
            else:
                self.other_players[i]['status'] = 0

            self.other_players[i]['utg_position'] = self.get_utg_from_abs_pos(self.other_players[i]['abs_position'],
                                                                              self.dealer_position)

        self.other_active_players = sum([v['status'] for v in self.other_players])
        if self.gameStage == "PreFlop":
            self.playersBehind = sum(
                [v['status'] for v in self.other_players if v['abs_position'] >= self.dealer_position + 4 - 1])
        else:
            self.playersBehind = sum(
                [v['status'] for v in self.other_players if v['abs_position'] >= self.dealer_position + 2 - 1])
        self.playersAhead = self.other_active_players - self.playersBehind
        self.isHeadsUp = True if self.other_active_players < 2 else False
        # self.logger.debug("Other players in the game: " + str(self.other_active_players))
        # self.logger.debug("Players behind: " + str(self.playersBehind))
        # self.logger.debug("Players ahead: " + str(self.playersAhead))

        if h.round_number == 0:
            # reference_pot = float(p.selected_strategy['bigBlind'])
            reference_pot = float(self.bigBlind)
        else:
            reference_pot = float(self.bigBlind) #self.get_bot_pot(p)

        # get first raiser in (tested for preflop)
        self.first_raiser, \
        self.second_raiser, \
        self.first_caller, \
        self.first_raiser_utg, \
        self.second_raiser_utg, \
        self.first_caller_utg = \
            self.get_raisers_and_callers(p, reference_pot)

        if ((h.previous_decision == "Call" or h.previous_decision == "Call2") and str(h.lastRoundGameID) == str(
                h.GameID)) and \
                not (self.checkButton == True and self.playersAhead == 0):
            self.other_player_has_initiative = True
        else:
            self.other_player_has_initiative = False

        # self.logger.info("Other player has initiative: " + str(self.other_player_has_initiative))
        self.bonatablemodel.other_players = self.other_players
        self.bonatablemodel.main_bot_whnd = self.whnd
        self.bonatablemodel.setActivePlayers(self.other_active_players + 1)
        return True

    def get_round_number(self, h):
        if h.histGameStage == self.gameStage and h.lastRoundGameID == h.GameID:
            h.round_number += 1
        else:
            h.round_number = 0
        return True

    def get_dealer_position(self):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl + str(self.sit_count)]
        self.gui_signals.signal_progressbar_increase.emit(5)
        # pil_image = self.crop_image(self.entireScreenPIL, 0, 0,
        #                             503, 1040)
        # # print("+++========================== get_dealer_position =========================+++")
        # img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        # count, points, bestfit, _ = self.find_template_on_screen(self.dealer, img, 0.05)
        # try:
        #     point = points[0] 
        # except: 
        #     # self.logger.debug("No dealer found")
        #     return False

        self.position_utg_plus = -2
        for n, fd in enumerate(func_dict, start=0):
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1], fd[2], fd[3])
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, minvalue = self.find_template_on_screen(self.dealer, img, 0.05)
            
            # if point[0] >= fd[0] and point[1] >= fd[1] and point[0] <= fd[2] and point[1] <= fd[3]:
            if count > 0:
                # self.position_utg_plus = (self.sit_count * 2 - 3 - n) % self.sit_count 
                self.position_utg_plus = self.playing_players - 2 # if n == self.sit_count
                self.dealer_position = n # 0 is myself, 1 is player to the left
                # self.logger.info('Bot position is UTG+' + str(self.position_utg_plus))  # 0 mean bot is UTG
                # print('Bot position is UTG+' + str(self.position_utg_plus))
                # print("dealer found is utg position -2")
            elif not self.other_players[n - 1]['empty'] and self.position_utg_plus > -2:
                self.position_utg_plus = (self.position_utg_plus + 1) % self.playing_players

        if self.position_utg_plus == -2:
            self.position_utg_plus = 0
            self.dealer_position = self.playing_players - 2
            # self.logger.error('Could not determine dealer position. Assuming UTG')
        # else:
            # self.logger.info('Dealer position (0 is myself and 1 is next player): ' + str(self.dealer_position))
        print("My utg position is :   " + str(self.position_utg_plus))
        
        self.big_blind_position_abs_all = (self.dealer_position + 2) % self.sit_count  # 0 is myself, 1 is player to my left
        self.big_blind_position_abs_op = self.big_blind_position_abs_all - 1

        self.table_model_data['utg_position'] = self.position_utg_plus

        return True

    def get_total_pot_value(self, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        self.gui_signals.signal_status.emit("Get Pot Value")
        # self.logger.debug("Get TotalPot value")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])

        value = self.get_ocr_float(pil_image, 'TotalPotValue', force_method=1)

        try:
            if not str(value) == '':
                value = float(re.findall(r'\d{1,2}\.\d{1,2}', str(value))[0])
        except:
            # self.logger.warning("Total pot regex problem: " + str(value))
            value = ''
            # self.logger.warning("unable to get pot value")
            self.gui_signals.signal_status.emit("Unable to get pot value")
            pil_image.save("pics/ErrPotValue.png")
            self.totalPotValue = h.previousPot

        if value == '':
            self.totalPotValue = 0
        else:
            self.totalPotValue = value

        # self.logger.info("Final Total Pot Value: " + str(self.totalPotValue))
        return True
    def get_raise_value(self,p,mouse):
        mouse.mouse_action("Raise Btn", self.tlc)
        
        wDC = win32gui.GetWindowDC(self.whnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        mem_dc = dcObj.CreateCompatibleDC()
        screenshot = win32ui.CreateBitmap()
        _left , _top , _right , _bottom = win32gui.GetWindowRect ( self.whnd )
        w = _right-_left
        h = _bottom - _top
        screenshot.CreateCompatibleBitmap (dcObj, w, h)
        mem_dc.SelectObject(screenshot) 
        mem_dc.BitBlt((0, 0), (w, h), dcObj, (0, 0),win32con.SRCCOPY) 
        signedIntsArray = screenshot.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (h, w, 4)
        dcObj.DeleteDC()
        mem_dc.DeleteDC()
        win32gui.ReleaseDC(self.whnd, wDC)
        win32gui.DeleteObject(screenshot.GetHandle())
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_status.emit("Get Raise value")
        self.gui_signals.signal_progressbar_increase.emit(5)
        pil_image = self.crop_image(img, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        # img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        # cv2.imwrite('buttonrect.png',img)
        points_x = {}
        suits="0123456789"
        for i in suits :
            name = "pics/" + self.tbl[0:2] + "/raise_number/" + i + ".png"
            template = Image.open(name)
            self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.05)
            if count != 0:
                points_x.update({
                    i:bestfit[0]
                    })
        # test = ""
        # sorted_x = sorted(points_x.x_coo(), key=operator.itemgetter(1))
        sorted_d = sorted(points_x.items(), key=operator.itemgetter(1))
        value = ""
        for val in sorted_d:
            val = val[0].replace("d",".")
            value += val
        
        if value == '':
            self.currenRaiseValue = 0
        else:
            self.currentRaiseValue = float(value)
        print("Raise Value")
        print(value)
        # time.sleep(1)
        mouse.mouse_action("Fold", self.tlc)
        self.currentBetValue = self.currenRaiseValue
        return True

    def get_current_bet_value(self, p):
        current_betbtn_value = dict()
        current_betbtn_value['pot'] = ''
        self.current_betbtn_value = []
        for i in range(3):
            op = copy(current_betbtn_value)
            op['abs_position'] = i
            self.current_betbtn_value.append(op)
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        self.gui_signals.signal_status.emit("Get Bet Value")
        
        for i, fd in enumerate(func_dict, start=0):
            self.gui_signals.signal_progressbar_increase.emit(1)
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],fd[2], fd[3])
            # self.logger.debug("Get bet value")
            pil_image = self.crop_image(self.entireScreenPIL, fd[0], fd[1],fd[2], fd[3])
            self.currentBetValue = self.get_ocr_float(pil_image, 'BetValue')
            points_x = {}
            suits="0123456789dk"
            for j in suits :
                # name = "pics/" + self.tbl[0:2] + "/bet_value/" + j + ".png"
                name = "pics/" + self.tbl[0:2] + "/call_bet_number/" + j + ".png"
                template = Image.open(name)
                pots = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
                count, points, bestfit, _ = self.find_template_on_screen(pots, img, 0.03)
                if count != 0:
                    for point in points:    
                        points_x.update({
                            point[0]:j
                            })
            sorted_d = collections.OrderedDict(sorted(points_x.items()))
            value = ""
            for val in sorted_d.values():
                val = val.replace("d",".")
                value += val
            #Kilo detect
            kilo = 1
            if value.find('k') == len(value) - 1:
                kilo = 1000
                value = value.replace('k','')

            if value != '': 
                value = float(value) * kilo
            else:
                value = 0
            # self.currentBetValue[i]['pot'] = value
            self.current_betbtn_value[i]["pot"] = value
            # print(value)
        self.totalPotValue = self.current_betbtn_value[2]["pot"]
        print("----currentBetValue pots:---", self.totalPotValue)
        return True
    def get_round_pot_value(self, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(2)
        self.gui_signals.signal_status.emit("Get round pot value")
        # self.logger.debug("Get round pot value")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])

        value = self.get_ocr_float(pil_image, 'TotalPotValue', force_method=1)

        try:
            if not str(value) == '':
                value = float(re.findall(r'\d{1,2}\.\d{1,2}', str(value))[0])
        except:
            # self.logger.warning("Round pot regex problem: " + str(value))
            value = ''
            # self.logger.warning("unable to get round pot value")
            self.gui_signals.signal_status.emit("Unable to get round pot value")
            pil_image.save("pics/ErrRoundPotValue.png")
            self.round_pot_value = h.previous_round_pot_value

        if value == '':
            self.round_pot_value = 0
        else:
            self.round_pot_value = value

        # self.logger.info("Final round pot Value: " + str(self.round_pot_value))
        return True

    def get_my_funds(self, h, p):

        # 2020/4/1 updated by gc
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Get my funds")
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        points_x = {}
        suits="0123456789dk"
        for i in suits :
            name = "pics/" + self.tbl[0:2] + "/funds_number/" + i + ".png"
            template = Image.open(name)
            self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.08)
            if count != 0:
                for point in points:    
                    points_x.update({ 
                        point[0]:i
                        })
        # test = ""
        # sorted_d = sorted(points_x.items(), key=operator.itemgetter(1))
        sorted_d = collections.OrderedDict(sorted(points_x.items()))
        value = ""
        # for val in sorted_d:
        #     val = val[0].replace("d",".")
        #     value += val
        exist_dot = False
        for val in sorted_d.values():
            if val == "d":
                if not exist_dot:
                    val = "."
                    exist_dot = True
                else:
                    val =""
            value += val
        #Kilo detect
        kilo = 1
        if value.find('k') == len(value) - 1:
            kilo = 1000
            value = value.replace('k','')
        if value == '':
            self.myFunds = 0
        else:
            self.myFunds = float(value) * kilo
        # self.logger.debug("Funds: " + str(self.myFunds))
        print("My Funds: " + str(self.myFunds))
        return True
        # func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # self.gui_signals.signal_progressbar_increase.emit(5)
        # self.logger.debug("Get my funds")
        # print("+++========================== Get my funds ==========================+++")
        # pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
        #                             func_dict['x2'], func_dict['y2'])

        # if p.selected_strategy['pokerSite'][0:2] == 'PP':
        #     basewidth = 200
        #     wpercent = (basewidth / float(pil_image.size[0]))
        #     hsize = int((float(pil_image.size[1]) * float(wpercent)))
        #     pil_image = pil_image.resize((basewidth, hsize), Image.ANTIALIAS)

        # pil_image_filtered = pil_image.filter(ImageFilter.ModeFilter)
        # pil_image_filtered2 = pil_image.filter(ImageFilter.MedianFilter)

        # self.myFundsError = False
        # try:
        #     pil_image.save("pics/myFunds.png")
        # except:
        #     self.logger.info("Could not save myFunds.png")

        # self.myFunds = self.get_ocr_float(pil_image, 'MyFunds')

        # if self.myFunds == '':
        #     self.myFunds = self.get_ocr_float(pil_image_filtered, 'MyFunds')
        # if self.myFunds == '':
        #     self.myFunds = self.get_ocr_float(pil_image_filtered2, 'MyFunds')

        # if self.myFunds == '':
        #     self.myFundsError = True
        #     # self.myFunds = float(h.myFundsHistory[-1])
        #     self.myFunds = 100 # add by zq
        #     self.logger.info("myFunds not regognised!")
        #     self.gui_signals.signal_status.emit("Funds NOT recognised")
        #     self.logger.warning("Funds NOT recognised. See pics/FundsError.png to see why.")
        #     self.entireScreenPIL.save("pics/FundsError.png")
        #     time.sleep(0.5)
        # try:
        #     self.myFunds = float(self.myFunds)
        # except:
        #     self.myFunds = 100.0
        # self.logger.debug("Funds: " + str(self.myFunds))

        # return True

    def get_current_call_value(self, p):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_status.emit("Get Call value")
        self.gui_signals.signal_progressbar_increase.emit(5)

        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])

        if not self.checkButton:
            points_x = {}
            suits="0123456789dk"
            for i in suits :
                name = "pics/" + self.tbl[0:2] + "/call_bet_number/" + i + ".png"
                template = Image.open(name)
                self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
                count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.045)
                if count != 0:
                    for point in points:    
                        points_x.update({
                            point[0]:i
                            })
            sorted_d = collections.OrderedDict(sorted(points_x.items()))
            value = ""
            for val in sorted_d.values():
                value += val
            if value.find('d') == len(value) - 4 or value.find('d') == len(value) - 7:
                value = value.replace('d','', 1)
            else:
                value = value.replace('d','.', 1)
            #Kilo detect
            kilo = 1
            if value.find('k') == len(value) - 1:
                kilo = 1000
                value = value.replace('k','')
            if value == '':
                self.currentCallValue = 0
            else:
                self.currentCallValue = float(value) * kilo
            self.minCall = float(self.currentCallValue)
        elif self.checkButton:
            self.currentCallValue = 0
            self.minCall = float(self.currentCallValue)
        if self.currentCallValue != '':
            self.getCallButtonValueSuccess = True
        else:
            try:
                pil_image.save("pics/ErrCallValue.png")
            except:
                pass
        self.currentBetValue = self.currentCallValue * 2
        print("--- Current Call Value ---", self.currentCallValue)
        return True
    def get_callbutton_pots(self, h):
        func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        self.gui_signals.signal_progressbar_increase.emit(5)
        self.gui_signals.signal_status.emit("Get Callbutton value")
        # self.logger.debug("Get Callbutton value")
        # pil_image = self.crop_image(self.entireScreenPIL, 321,832,363,847)
        pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                    func_dict['x2'], func_dict['y2'])
        # cv2.imwrite("callvalue.png",np.array(pil_image))
        points_x = {}
        suits="0123456789dk"
        for i in suits :
            name = "pics/" + self.tbl[0:2] + "/call_number/" + i + ".png"
            template = Image.open(name)
            self.callnumber = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
            count, points, bestfit, _ = self.find_template_on_screen(self.callnumber, img, 0.05)
            if count != 0:
                points_x.update({
                    i:bestfit[0]
                    })
        # test = ""
        # sorted_x = sorted(points_x.x_coo(), key=operator.itemgetter(1))
        sorted_d = sorted(points_x.items(), key=operator.itemgetter(1))
        value = ""
        for val in sorted_d:
            val = val[0].replace("d",".")
            value += val
        #Kilo detect
        kilo = 1
        if value.find('k') == len(value) - 1:
            kilo = 1000
            value = value.replace('k','')
        if value == '':
            self.callbtnValue = 0
        else:
            self.callbtnValue = float(value) * kilo

        # if value == '':
        #     self.callbtnValue = 0
        # else:
        #     self.callbtnValue = float(value)
        # self.logger.info("Call button Value: " + str(self.callbtnValue))
        return True    

    # def get_current_bet_value(self, p):
    #     func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
    #     self.gui_signals.signal_progressbar_increase.emit(5)

    #     self.gui_signals.signal_status.emit("Get Bet Value")
    #     self.logger.debug("Get bet value")

    #     pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
    #                                 func_dict['x2'], func_dict['y2'])

    #     self.currentBetValue = self.get_ocr_float(pil_image, 'BetValue')
    #     try:
    #         self.currentBetValue = float(self.currentBetValue)
    #     except:
    #         self.currentBetValue = 0.0
    #     if self.currentCallValue == '' and p.selected_strategy['pokerSite'][0:2] == "PS" and self.allInCall:
    #         self.logger.warning("Taking call value from button on the right")
    #         self.currentCallValue = self.currentBetValue
    #         self.currentBetValue = 9999999

    #     if self.currentBetValue == '':
    #         self.logger.warning("No bet value")
    #         self.currentBetValue = 9999999.0

    #     if self.currentCallValue == '':
    #         self.logger.error("Call Value was empty")
    #         if p.selected_strategy['pokerSite'][0:2] == "PS" and self.allInCall:
    #             self.currentCallValue = self.currentBetValue
    #             self.currentBetValue = 9999999
    #         try:
    #             self.entireScreenPIL.save('log/call_err_debug_fullscreen.png')
    #         except:
    #             pass

    #         self.currentCallValue = 9999999.0
    #     try:
    #         self.currentCallValue = float(self.currentCallValue)
    #     except:
    #         self.currentCallValue = 1.0

    #     if self.currentBetValue < self.currentCallValue and not self.allInCall:
    #         self.currentCallValue = self.currentBetValue / 2
    #         self.BetValueReadError = True
    #         self.entireScreenPIL.save("pics/BetValueError.png")

    #     if self.currentBetValue < self.currentCallValue and self.allInCall:
    #         self.currentBetValue = self.currentCallValue + 0.01
    #         self.BetValueReadError = True
    #         self.entireScreenPIL.save("pics/BetValueError.png")

    #     self.currentCallValue = self.minCall
    #     self.currentBetValue = self.minCall * 2
    #     self.logger.info("Final call value: " + str(self.currentCallValue))
    #     self.logger.info("Final bet value: " + str(self.currentBetValue))
    #     return True

    def check_sit_in(self, h, t, p, gui_signals, mouse):
        if self.tbl == 'SN':
            
            func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
            pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
                                        func_dict['x2'], func_dict['y2'])
            img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)

            # name = "pics/" + self.tbl[0:2] + "/sit_in.png"
            # template = Image.open(name)
            # self.lostEverything = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
            # cv2.imshow('result',img)
            # cv2.waitKey()
            # cv2.destroyAllWindows()

            count, points, bestfit, _ = self.find_template_on_screen(self.lostEverything, img, 0.05)
            if count > 0:
                print("--- Sit in ---")
                # mouse.mouse_action("Sitin", self.tlc)
                # time.sleep(2)
                # mouse.mouse_action("Joingame", self.tlc)

            return True
        # func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
        #                             func_dict['x2'], func_dict['y2'])
        # img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_BGR2RGB)
        # count, points, bestfit, _ = self.find_template_on_screen(self.lostEverything, img, 0.001)
        # if count > 0:
        #     h.lastGameID = str(h.GameID)
        #     self.myFundsChange = float(0) - float(h.myFundsHistory[-1])
        #     self.game_logger.mark_last_game(t, h, p)
        #     self.gui_signals.signal_status.emit("Everything is lost. Last game has been marked.")
        #     self.gui_signals.signal_progressbar_reset.emit()
        #     self.logger.warning("Game over")
        #     # user_input = input("Press Enter for exit ")
        #     # gui_signals.signal_curve_chart_update1.emit(h.histEquity, h.histMinCall, h.histMinBet, t.equity,
        #     #                                             t.minCall, t.minBet,
        #     #                                             'bo',
        #     #                                             'ro')
        #     #
        #     # gui_signals.signal_curve_chart_update2.emit(t.power1, t.power2, t.minEquityCall, t.minEquityBet,
        #     #                                             t.smallBlind, t.bigBlind,
        #     #                                             t.maxValue,
        #     #                                             t.maxEquityCall, t.max_X, t.maxEquityBet)
        #     sys.exit()
        # else:
        #     return True

    def get_new_hand(self, mouse, h, p):
        self.gui_signals.signal_progressbar_increase.emit(5)
        if h.previousCards != self.mycards and len(self.mycards) == 2:
            # self.logger.info("+++========================== NEW HAND ==========================+++")
            self.time_new_cards_recognised = datetime.datetime.utcnow()
            # self.get_game_number_on_screen(h)
            self.get_my_funds(h, p)
            self.table_model_data['funds'] = self.myFunds
            # if self.bonatablemodel.type == 'TOUNAMENT1' or self.bonatablemodel.type == 'TOUNAMENT2':
            #     self.bonatablemodel.initialFunds = self.myFunds
            h.fastfold = False
            print("+++========================== NEW HAND ==========================+++")
            h.lastGameID = str(h.GameID)
            h.GameID = int(round(np.random.uniform(0, 999999999), 0))
            cards = ' '.join(self.mycards)
            self.gui_signals.signal_status.emit("New hand: " + str(cards))

            if not len(h.myFundsHistory) == 0:
                self.myFundsChange = float(self.myFunds) - float(h.myFundsHistory[-1])
                self.game_logger.mark_last_game(self, h, p)

            # t_algo = threading.Thread(name='Algo', target=self.call_genetic_algorithm, args=(p,))
            # t_algo.daemon = True
            # t_algo.start()

            self.gui_signals.signal_funds_chart_update.emit(self.game_logger)
            self.gui_signals.signal_bar_chart_update.emit(self.game_logger, p.current_strategy)

            h.myLastBet = 0
            h.myFundsHistory.append(self.myFunds)
            h.previousCards = self.mycards
            h.lastSecondRoundAdjustment = 0
            h.last_round_bluff = False  # reset the bluffing marker
            h.round_number = 0

            # mouse.move_mouse_away_from_buttons_jump()
            # self.take_screenshot(False, p)
            self.gameStage = 'PreFlop'
            

            # saved screen shot file
            # cv2.imwrite(self.path, self.entireScreenPIL)
            # self.entireScreenPIL.save(self.path)
            # print(self.path + '    file saved')
            # self.oldpath = self.path

        # else:
        #     # self.logger.info("Game number on screen: " + str(h.game_number_on_screen))
        #     self.get_my_funds(h, p)

        return True

    def upload_collusion_wrapper(self, p, h):
        if not (h.GameID, self.gameStage) in h.uploader:
            h.uploader[(h.GameID, self.gameStage)] = True
            self.game_logger.upload_collusion_data(h.game_table_name, self.mycards, p, self.gameStage)
        return True
    def get_collusion_cards(self):
        
        player_dropped_out = True
        collusion_cards = []
        try:
            temp = list(i['mycard'] for i in self.bonatablemodel.bots if i['whnd'] != self.whnd)
            for i in temp:
                collusion_cards.extend(i)
            print(str(collusion_cards))
        except:
            collusion_cards = []
        return [], player_dropped_out
        # return collusion_cards, player_dropped_out
    # def get_game_number_on_screen(self, h):

       
        # try:
        #     func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        # except KeyError:
        #     h.game_number_on_screen = ''
        #     return True

        # pil_image = self.crop_image(self.entireScreenPIL, func_dict['x1'], func_dict['y1'],
        #                             func_dict['x2'], func_dict['y2'])
        # basewidth = 200
        # wpercent = (basewidth / float(pil_image.size[0]))
        # hsize = int((float(pil_image.size[1]) * float(wpercent)))
        # img_resized = pil_image.resize((basewidth, hsize), Image.ANTIALIAS)

        # img_min = img_resized.filter(ImageFilter.MinFilter)
        # # img_med = img_resized.filter(ImageFilter.MedianFilter)
        # img_mod = img_resized.filter(ImageFilter.ModeFilter).filter(ImageFilter.SHARPEN)

        # try:
        #     h.game_number_on_screen = pytesseract.image_to_string(img_mod, None, False, "-psm 6")
        # except:
        #     self.logger.warning("Failed to get game number from screen")
        #     h.game_number_on_screen = ''

        # return True

    def get_snowie_advice(self, p, h):
        # if self.tbl == 'SN':
        #     func_dict = self.coo[inspect.stack()[0][3]][self.tbl]
        #     img = cv2.cvtColor(np.array(self.entireScreenPIL), cv2.COLOR_BGR2RGB)
        #     count1, points1, bestfit, minvalue = self.find_template_on_screen(self.topLeftCorner_snowieadvice1, img,
        #                                                                       0.07)
        #     # count2, points2, _ = self.find_template_on_screen(self.topLeftCorner_snowieadvice2, img, 0.07)
        #
        #     if count1 == 1:
        #         tlc_adv1 = points1[0]
        #         # tlc_adv2 = points2[0]
        #
        #         fd = func_dict['fold']
        #         fold_image = self.crop_image(self.entireScreenPIL, tlc_adv1[0] + fd['x1'], tlc_adv1[1] + fd['y1'],
        #                                      tlc_adv1[0] + fd['x2'], tlc_adv1[1] + fd['y2'])
        #         fd = func_dict['call']
        #         call_image = self.crop_image(self.entireScreenPIL, tlc_adv1[0] + fd['x1'], tlc_adv1[1] + fd['y1'],
        #                                      tlc_adv1[0] + fd['x2'], tlc_adv1[1] + fd['y2'])
        #         fd = func_dict['raise']
        #         raise_image = self.crop_image(self.entireScreenPIL, tlc_adv1[0] + fd['x1'], tlc_adv1[1] + fd['y1'],
        #                                       tlc_adv1[0] + fd['x2'], tlc_adv1[1] + fd['y2'])
        #         # fd=func_dict['betsize']
        #         # betsize_image = self.crop_image(self.entireScreenPIL, tlc_adv2[0] + fd['x1'], tlc_adv2[1] + fd['y1'],
        #         #                             tlc_adv2[0] + fd['x2'], tlc_adv2[1] + fd['y2'])
        #
        #         self.fold_advice = float(self.get_ocr_float(fold_image, str(inspect.stack()[0][3])))
        #         self.call_advice = float(self.get_ocr_float(call_image, str(inspect.stack()[0][3])))
        #         try:
        #             self.raise_advice = float(self.get_ocr_float(raise_image, str(inspect.stack()[0][3])))
        #         except:
        #             self.raise_advice = np.nan
        #         # self.betzise_advice = float(self.get_ocr_float(betsize_image, str(inspect.stack()[0][3])))
        #
        #         self.logger.info("Fold Advice: {0}".format(self.fold_advice))
        #         self.logger.info("Call Advice: {0}".format(self.call_advice))
        #         self.logger.info("Raise Advice: {0}".format(self.raise_advice))
        #         # logger.info("Betsize Advice: {0}".format(self.betzise_advice))
        #     else:
        #         self.logger.warning("Could not identify snowie advice window. minValue: {0}".format(minvalue))

        return True
