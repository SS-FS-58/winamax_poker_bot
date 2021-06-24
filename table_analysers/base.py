import os.path
import re
import sys
import time
import logging

import cv2  # opencv 3.0
import numpy as np
import pytesseract
from PIL import Image, ImageFilter, ImageGrab
# from configobj import ConfigObj

from decisionmaker.genetic_algorithm import GeneticAlgorithm
from tools.vbox_manager import VirtualBoxController
import win32ui, win32con, win32gui
from datetime import datetime
import winsound
from models.bonatablemodel import BonaTableModel
from configobj import ConfigObj
from matplotlib import pyplot as plt

default_test_image = r"f:\Working_Folder\02_Poker_Bot\winamax_bot\screenshot_log\log_08052021102022.png"
class Table(object):
    # General tools that are used to operate the pokerbot and are valid for all tables
    def __init__(self, p, gui_signals, game_logger, version, whnd, bonatablemodel):
        self.version = version
        self.ip = ''
        self.load_templates(p)
        self.load_coordinates()
        self.logger = logging.getLogger('table')
        self.logger.setLevel(logging.DEBUG)
        self.gui_signals = gui_signals
        self.game_logger = game_logger
        self.whnd = whnd
        self.round_pot_value = 0
        self.playing_players = 0
        self.other_players = []
        self.bonatablemodel = bonatablemodel
        try:
            self.table_model_data = self.bonatablemodel.bots[list(i['whnd'] for i in self.bonatablemodel.bots).index(whnd)]
        except:
            pass
        self.table_type = bonatablemodel.type
        self.sit_count = bonatablemodel.sit_count
        self.bigBlind = bonatablemodel.bigBlind
        self.smallBlind = bonatablemodel.smallBlind
        self.allInCall = False

        # if self.table_type == 'TBT' or self.table_type == 'NORMALROOM':
            
        # else:
            # config = ConfigObj("config.ini")
            # # lasted_smallBlind = self.smallBlind
            # self.smallBlind = int(config['smallBlind'])
            # # if self.smallBlind < lasted_smallBlind :
            # #     self.smallBlind = lasted_smallBlind
            # self.bigBlind = self.smallBlind * 2
            # self.bonatablemodel.initialFunds = self.smallBlind * 50


        # add by zq 2020/3/24

        # self.gameStage = "PreFlop"
        # self.mycards = ['As','7s']
        self.mt_tm = time.time()
        # self.timeout_start = datetime.datetime.utcnow()
        self.cardsOnTable = []
        # player1 = {'id':1, 'pot':10}
        # player2 = {'id':2, 'pot':20}
        # self.other_players = [player1, player2]
        # self.round_pot_value = 0
        # self.checkButton = False
        # self.tlc = [200, 100]
        # self.currentCallValue = 0
        self.position_utg_plus = 1
        # self.first_raiser_utg = 0
        # self.second_raiser_utg = 0
        # self.first_caller_utg = 0
        # self.totalPotValue = 500
        # self.max_X = 1000
        # self.power1 = 100
        # self.other_player_has_initiative = True
        # self.isHeadsUp = True
        # self.myFunds = 1000
        # self.allInCall = False
        # # self.allInCallButton = True
        # self.other_active_players = '2'
        # self.playersAhead = '3'
        # self.first_raiser = 1
        # self.first_caller = 2
        # self.second_raiser = 3
        self.gameStage = ''
        self.oldpath = ''
        # self.path = ''
        self.oldcardsOnTable = []
        self.fastfold = False
        self.bet_button_found = False
        self.currentBetValue = 0
        self.currenRaiseValue = 0

    def update_table(self):
        self.bigBlind = self.bonatablemodel.bigBlind
        self.smallBlind = self.bonatablemodel.smallBlind
    def load_templates(self, p):
        self.tablecardImages = dict()
        self.mycardImages = dict()
        self.img1 = dict()
        self.img2 = dict()
        self.tbl = p.selected_strategy['pokerSite']
        values = "23456789TJQKA"
        suites = "cdhs"

        for x in values:
            for y in suites:
                table_card_file_name = "pics/" + self.tbl[0:2] + "/tablecards/" + x + y + ".png"
                my_card_file_name = "pics/" + self.tbl[0:2] + "/mycards/" + x + y + ".png"
                if os.path.exists(table_card_file_name) and os.path.exists(my_card_file_name):
                    self.img1[x + y.upper()] = Image.open(table_card_file_name)
                    self.tablecardImages[x + y.upper()] = cv2.cvtColor(np.array(self.img1[x + y.upper()]), cv2.COLOR_BGR2RGB)
                    self.img2[x + y.upper()] = Image.open(my_card_file_name)
                    self.mycardImages[x + y.upper()] = cv2.cvtColor(np.array(self.img2[x + y.upper()]), cv2.COLOR_BGR2RGB)
                # else:
                #     self.logger.critical("Card template File not found: " + str(x) + str(y) + ".png")

        # name = "pics/" + self.tbl[0:2] + "/button.png"
        # template = Image.open(name)
        # self.button = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
        name = "pics/" + self.tbl[0:2] + "/allinbutton.png"
        template = Image.open(name)
        self.allin = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/user_status.png"
        template = Image.open(name)
        self.user_status = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)
        

        # name = "pics/" + self.tbl[0:2] + "/topleft.png"
        # template = Image.open(name)
        # self.topLeftCorner = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        # if self.tbl[0:2] == 'SN':
        #     name = "pics/" + self.tbl[0:2] + "/topleft2.png"
        #     template = Image.open(name)
        #     self.topLeftCorner2 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        #     name = "pics/" + self.tbl[0:2] + "/topleft3.png"
        #     template = Image.open(name)
        #     self.topLeftCorner_snowieadvice1 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        #     name = "pics/" + self.tbl[0:2] + "/topleftLA.png"
        #     template = Image.open(name)
        #     self.topLeftCorner_snowieadvice2 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/coveredcard.png"
        template = Image.open(name)
        self.coveredCardHolder = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/sit_out.png"
        template = Image.open(name)
        self.lostEverything = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        # name = "pics/" + self.tbl[0:2] + "/imback.png"
        # template = Image.open(name)
        # self.ImBack = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/check.png"
        template = Image.open(name)
        self.check = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/call.png"
        template = Image.open(name)
        self.call = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        # name = "pics/" + self.tbl[0:2] + "/smalldollarsign1.png"
        # template = Image.open(name)
        # self.smallDollarSign1 = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/allincallbutton.png"
        template = Image.open(name)
        self.allInCallButton = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/Raise.png"
        template = Image.open(name)
        self.raisebutton = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        # name = "pics/" + self.tbl[0:2] + "/lostEverything.png"
        # template = Image.open(name)
        # self.lostEverything = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/dealer.png"
        template = Image.open(name)
        self.dealer = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

        name = "pics/" + self.tbl[0:2] + "/betbutton.png"
        template = Image.open(name)
        self.betbutton = cv2.cvtColor(np.array(template), cv2.COLOR_BGR2RGB)

    def load_coordinates(self):
        with open('resources/coordinates.json', 'r') as inf:
            c = eval(inf.read())
            self.coo = c['screen_scraping']

    def take_screenshot(self, initial, p):
        
        time.sleep(1)
        # Get tablemodel current idle status
        if not self.bonatablemodel.getIdle():
            # print("I idle :  " + self.bonatablemodel.table_title + str(self.table_model_data['whnd']) )
            return False
        
        if initial:
            self.gui_signals.signal_status.emit("")
            self.gui_signals.signal_progressbar_reset.emit()
            if self.gui_signals.exit_thread == True: sys.exit()
            if self.gui_signals.pause_thread == True:
                while self.gui_signals.pause_thread == True:
                    # time.sleep(1)
                    if self.gui_signals.exit_thread == True: sys.exit()

        # time.sleep(0.1)
        # config = ConfigObj("config.ini")
        # control = config['control']
        # if control == 'Direct mouse control':
        #     self.entireScreenPIL = ImageGrab.grab()

        # else:
        #     try:
        #         vb = VirtualBoxController()
        #         self.entireScreenPIL = vb.get_screenshot_vbox()
        #         self.logger.debug("Screenshot taken from virtual machine")
        #     except:
        #         self.logger.warning("No virtual machine found. Press SETUP to re initialize the VM controller")
        #         # gui_signals.signal_open_setup.emit(p,L)
        #         self.entireScreenPIL = ImageGrab.grab()
        # add by zq 2020/3/24

        # # In case of static
        # self.entireScreenPIL = Image.fromarray(cv2.cvtColor(cv2.imread(r'f:\24_Poker_bot\02_source\open_source\Poker_bot-master\temp_screenshot\test01042020000729.png'), cv2.COLOR_RGB2BGR))
        # self.tlc = [0, 0, 503, 1040]
        # self.path = r'f:\24_Poker_bot\02_source\Poker_bot\temp_screenshot\test.png'
        self.current_strategy = p.current_strategy  # needed for mongo manager
             
        # test file whnd == 0
        if (self.whnd == 0):
            # In case of static
            filename = default_test_image
            self.entireScreenPIL = Image.fromarray(cv2.cvtColor(cv2.imread(filename), cv2.COLOR_RGB2BGR))
            self.tlc = [0, 0, 1384, 1047]
            
            # plt.imshow(cv2.imread(filename))
            # plt.show()
            # self.entireScreenPIL.show()
            # cv2.imshow('image',cv2.imread(filename))
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
        else:
        # if (self.whnd == 0):
            try:
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
                self.entireScreenPIL = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_RGB2BGR)) #cv2.COLOR_BGRA2GRAY, cv2.COLOR_BGRA2BGR
                self.tlc = [_left, _top, w, h]
                # self.entireScreenPIL = Image.fromarray(cv2.cvtColor(cv2.imread(r'f:\24_Poker_bot\02_source\open_source\Poker_bot-master\test25032020034854.png'), cv2.COLOR_RGB2BGR))
                # add by zq 2020/3/25 saved screenshot files
                # self.path = r'e:\Qiang_working\PioSolver\bonapoker_bot\screenshot_log\log_{}.png'.format(datetime.now().strftime("%d%m%Y%H%M%S"))
                # self.entireScreenPIL.save(self.path)
                # print('save screenshot file: ', self.path)
                # path = r'f:\24_Poker_bot\02_source\open_source\Poker_bot-master\test11.png'
                
                # img = cv2.imread(path) 
                # self.entireScreenPIL = img
                # cv2.imshow('image',img)
                # cv2.waitKey(0)
                # cv2.destroyAllWindows()
                # cv2.imwrite(r'f:\24_Poker_bot\02_source\open_source\Poker_bot-master\test.png',img)
            except:
                return False 
        self.gui_signals.signal_status.emit(str(p.current_strategy))
        self.gui_signals.signal_progressbar_increase.emit(5)
        return True

    def find_template_on_screen(self, template, screenshot, threshold):
        # 'cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
        # 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
        try:
            method = eval('cv2.TM_SQDIFF_NORMED')
            # Apply template Matching
            res = cv2.matchTemplate(screenshot, template, method)
            loc = np.where(res <= threshold)

            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            

            # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                bestFit = min_loc
            else:
                bestFit = max_loc

            count = 0
            points = []
            for pt in zip(*loc[::-1]):
                # cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0,0,255), 2)
                count += 1
                points.append(pt)
            # plt.subplot(121),plt.imshow(res)
            # plt.subplot(122),plt.imshow(img,cmap = 'jet')
            # plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
            # plt.show()
            return count, points, bestFit, min_val
        except Exception as e:
            print(e)
            return 0, [], 0, 0

    def get_ocr_float(self, img_orig, name, force_method=0, binarize=False):
        def binarize_array(image, threshold=200):
            """Binarize a numpy array."""
            numpy_array = np.array(image)
            for i in range(len(numpy_array)):
                for j in range(len(numpy_array[0])):
                    if numpy_array[i][j] > threshold:
                        numpy_array[i][j] = 255
                    else:
                        numpy_array[i][j] = 0
            return Image.fromarray(numpy_array)

        def fix_number(t, force_method):
            t = t.replace("I", "1").replace("Â°lo", "").replace("O", "0").replace("o", "0") \
                .replace("-", ".").replace("D", "0").replace("I", "1").replace("_", ".").replace("-", ".") \
                .replace("B", "8").replace("..", ".")
            t = re.sub("[^0123456789\.]", "", t)
            try:
                if t[0] == ".": t = t[1:]
            except:
                pass
            try:
                if t[-1] == ".": t = t[0:-1]
            except:
                pass
            try:
                if t[-1] == ".": t = t[0:-1]
            except:
                pass
            try:
                if t[-1] == "-": t = t[0:-1]
            except:
                pass
            if force_method == 1:
                try:
                    t = re.findall(r'\d{1,3}\.\d{1,2}', str(t))[0]
                except:
                    t = ''
                if t == '':
                    try:
                        t = re.findall(r'\d{1,3}', str(t))[0]
                    except:
                        t = ''

            return t

        try:
            img_orig.save('pics/ocr_debug_' + name + '.png')
        except:
            # self.logger.warning("Coulnd't safe debugging png file for ocr")
            pass


        #add zq 2020/3/26-----------------------------------
        # img_cv = cv2.imread('pics/ocr_debug_' + name + '.png')
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # im_pil = Image.fromarray(img)
        # img_cv = cv2.cvtColor(im_pil, cv2.COLOR_BGR2GRAY)
        # img_cv = np.asarray(img_orig.convert('L'))

        # img_orig.save('pics/ocr_test/' + name + '{}.png'.format(datetime.now().strftime("%d%m%Y%H%M%S")))

        img_cv = cv2.cvtColor(np.asarray(img_orig), cv2.COLOR_RGB2BGR)
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        

        img_cv = cv2.resize(img_cv,(0,0),fx=7,fy=7)
        img_cv = cv2.medianBlur(img_cv,9)
        img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # cv2.imshow(name, img_cv)  
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'
        custom_config = r'-c tessedit_char_whitelist=0123456789. --oem 3 --psm 8'
        re = pytesseract.image_to_string(img_cv, config=custom_config)
        try:
            refloat = float(re)
        except:
            re = ''
        print(name + ':  ocr Result: ' + re)
        return re

        
        basewidth = 300
        wpercent = (basewidth / float(img_orig.size[0]))
        hsize = int((float(img_orig.size[1]) * float(wpercent)))
        img_resized = img_orig.convert('L').resize((basewidth, hsize), Image.ANTIALIAS)
        if binarize:
            img_resized = binarize_array(img_resized, 200)
        # img_resized.show()
        img_min = img_resized.filter(ImageFilter.MinFilter)
        # img_min.show()
        # img_med = img_resized.filter(ImageFilter.MedianFilter)
        img_mod = img_resized.filter(ImageFilter.ModeFilter).filter(ImageFilter.SHARPEN)
        # img_mod.show()
        lst = []
        # try:
        #    lst.append(pytesseract.image_to_string(img_orig, none, false,"-psm 6"))
        # except exception as e:
        #    self.logger.error(str(e))

        if force_method == 0:
            try:
                lst.append(pytesseract.image_to_string(img_min, None, False, "-psm 6"))
            except Exception as e:
                # self.logger.warning(str(e))
                try:
                    self.entireScreenPIL.save('pics/err_debug_fullscreen.png')
                except:
                    self.logger.warning("Coulnd't safe debugging png file for ocr")
                    # try:
                    #    lst.append(pytesseract.image_to_string(img_med, None, False, "-psm 6"))
                    # except Exception as e:
                    #    self.logger.error(str(e))

        try:
            if force_method == 1 or fix_number(lst[0], force_method=0) == '':
                lst.append(pytesseract.image_to_string(img_mod, None, False, "-psm 6"))
                lst.append(pytesseract.image_to_string(img_min, None, False, "-psm 6"))
        except UnicodeDecodeError:
            pass
        except Exception as e:
            # self.logger.warning(str(e))
            try:
                self.entireScreenPIL.save('pics/err_debug_fullscreen.png')
            except:
                self.logger.warning("Coulnd't safe debugging png file for ocr")

        try:
            final_value = ''
            for i, j in enumerate(lst):
                # self.logger.debug("OCR of " + name + " method " + str(i) + ": " + str(j))
                lst[i] = fix_number(lst[i], force_method) if lst[i] != '' else lst[i]
                final_value = lst[i] if final_value == '' else final_value

            # self.logger.info(name + " FINAL VALUE: " + str(final_value))
            if final_value == '':
                return ''
            else:
                return float(final_value)

        except Exception as e:
            # self.logger.warning("Pytesseract Error in recognising " + name)
            # self.logger.warning(str(e))
            try:
                self.entireScreenPIL.save('pics/err_debug_fullscreen.png')
            except:
                pass
            return ''

    def call_genetic_algorithm(self, p):
        self.gui_signals.signal_progressbar_increase.emit(5)
        self.gui_signals.signal_status.emit("Updating charts and work in background")
        n = self.game_logger.get_game_count(p.current_strategy)
        lg = int(p.selected_strategy['considerLastGames'])  # only consider lg last games to see if there was a loss
        f = self.game_logger.get_strategy_return(p.current_strategy, lg)
        self.gui_signals.signal_label_number_update.emit('gamenumber', str(int(n)))

        total_winnings = self.game_logger.get_strategy_return(p.current_strategy, 9999999)

        winnings_per_bb_100 = total_winnings / p.selected_strategy['bigBlind'] / n * 100 if n > 0 else 0

        # self.logger.info("Total Strategy winnings: %s", total_winnings)
        # self.logger.info("Winnings in BB per 100 hands: %s", np.round(winnings_per_bb_100,2))
        self.gui_signals.signal_label_number_update.emit('winnings', str(np.round(winnings_per_bb_100, 2)))

        # self.logger.info("Game #" + str(n) + " - Last " + str(lg) + ": $" + str(f))

        if n % int(p.selected_strategy['strategyIterationGames']) == 0 and f < float(
                p.selected_strategy['minimumLossForIteration']):
            self.gui_signals.signal_status.emit("***Improving current strategy***")
            # self.logger.info("***Improving current strategy***")
            winsound.Beep(500, 100)
            GeneticAlgorithm(True, self.game_logger)
            p.read_strategy()
        else:
            pass
            # self.logger.debug("Criteria not met for running genetic algorithm. Recommendation would be as follows:")
            # if n % 50 == 0: GeneticAlgorithm(False, logger, L)

    def crop_image(self, original, left, top, right, bottom):
        # original.show()
        # width, height = original.size  # Get dimensions
        cropped_example = original.crop((left, top, right, bottom))
        # cropped_example.show()
        return cropped_example

    def get_utg_from_abs_pos(self, abs_pos, dealer_pos):
        # utg_pos = (abs_pos - dealer_pos + self.sit_count - 2) % self.sit_count
        if np.isnan(abs_pos):
            return np.nan
        utg_pos = self.position_utg_plus
        for n in range(abs_pos + 1):
            if not self.other_players[n]['empty']:
                utg_pos += 1
        utg_pos = utg_pos % self.playing_players
        return utg_pos

    def get_abs_from_utg_pos(self, utg_pos, dealer_pos):
        # abs_pos = (utg_pos + dealer_pos - self.sit_count + 2) % self.sit_count
        if np.isnan(utg_pos):
            return np.nan
        current_utg_pos = self.position_utg_plus
        for n in range(self.sit_count - 1):
            if not self.other_players[n]['empty']:
                current_utg_pos += 1
                current_utg_pos = current_utg_pos % self.playing_players
            if current_utg_pos == utg_pos:
                abs_pos = n
                break
        return abs_pos

    def get_raisers_and_callers(self, p, reference_pot):
        first_raiser = np.nan
        second_raiser = np.nan
        first_caller = np.nan
        second_caller = np.nan
        third_raser = np.nan

        for n in range(self.sit_count - 1):  # n is absolute position of other player, 0 is player after bot
            i = (
                    self.dealer_position + n) % (self.sit_count - 1) # less myself as 0 is now first other player to my left and no longer myself
            # self.logger.debug("Go through pots to find raiser abs: {0} {1}".format(i, self.other_players[i]['pot']))
            if self.other_players[i]['pot'] != '':  # check if not empty (otherwise can't convert string)
                if self.other_players[i]['pot'] > reference_pot:
                    # reference pot is bb for first round and bot for second round
                    if np.isnan(first_raiser):
                        first_raiser = int(i)
                        first_raiser_pot = self.other_players[i]['pot']
                    else:
                        if self.other_players[i]['pot'] > first_raiser_pot:
                            second_raiser = int(i)

        first_raiser_utg = self.get_utg_from_abs_pos(first_raiser, self.dealer_position)
        try:
            highest_raiser = np.nanmax([first_raiser, second_raiser])
        except:
            highest_raiser = first_raiser
            pass
        second_raiser_utg = self.get_utg_from_abs_pos(second_raiser, self.dealer_position)

        first_possible_caller = int(self.big_blind_position_abs_op + 1) if np.isnan(highest_raiser) else int(
            highest_raiser + 1)
        # self.logger.debug("First possible potential caller is: " + str(first_possible_caller))

        # get first caller after raise in preflop
        for n in range(first_possible_caller, (self.sit_count - 1)):  # n is absolute position of other player, 0 is player after bot
            # self.logger.debug(
            #     "Go through pots to find caller abs: " + str(n) + ": " + str(self.other_players[n]['pot']))
            if self.other_players[n]['pot'] != '':  # check if not empty (otherwise can't convert string)
                if (self.other_players[n]['pot'] == float(self.bigBlind) and self.other_players[n]['utg_position'] != 0) or \
                                self.other_players[n]['pot'] > float(self.bigBlind):
                    first_caller = int(n)
                    break

        first_caller_utg = self.get_utg_from_abs_pos(first_caller, self.dealer_position)

        # check for callers between bot and first raiser. If so, first raiser becomes second raiser and caller becomes first raiser
        first_possible_caller = 0
        if self.dealer_position == 0: first_possible_caller = 2 # bot is sitting on Dealer
        if self.dealer_position == self.sit_count - 1: first_possible_caller = 1 # bot is sitting on SB
        # if self.dealer_position == 0: first_possible_caller = 1 # bot is sitting on BB
        if not np.isnan(first_raiser):
            for n in range(first_possible_caller, first_raiser):
                if self.other_players[n]['status'] == 1 and \
                        not (self.other_players[n]['utg_position'] == (self.playing_players - 1) % self.playing_players  and self.other_players[n]['pot'] == self.bigBlind) and \
                        not (self.other_players[n]['utg_position'] == (self.playing_players - 2) % self.playing_players and self.other_players[n]['pot'] == self.smallBlind) and \
                        not (self.other_players[n]['pot'] == ''):
                    second_raiser = first_raiser
                    first_raiser = n
                    first_raiser_utg = self.get_utg_from_abs_pos(first_raiser, self.dealer_position)
                    second_raiser_utg = self.get_utg_from_abs_pos(second_raiser, self.dealer_position)
                    break

        # self.logger.debug("First raiser abs: " + str(first_raiser))
        # self.logger.info("First raiser utg+" + str(first_raiser_utg))
        # self.logger.debug("Second raiser abs: " + str(second_raiser))
        # self.logger.info("Highest raiser abs: " + str(highest_raiser))
        # self.logger.debug("First caller abs: " + str(first_caller))
        # self.logger.info("First caller utg+" + str(first_caller_utg))

        return first_raiser, second_raiser, first_caller, first_raiser_utg, second_raiser_utg, first_caller_utg

    def derive_preflop_sheet_name(self, t, h, first_raiser_utg, first_caller_utg, second_raiser_utg):
        first_raiser_string = 'R' if not np.isnan(first_raiser_utg) else ''
        first_raiser_number = str(first_raiser_utg + 1) if first_raiser_string != '' else ''

        second_raiser_string = 'R' if not np.isnan(second_raiser_utg) else ''
        second_raiser_number = str(second_raiser_utg + 1) if second_raiser_string != '' else ''

        first_caller_string = 'C' if not np.isnan(first_caller_utg) else ''
        first_caller_number = str(first_caller_utg + 1) if first_caller_string != '' else ''

        round_string = '2' if h.round_number == 1 else ''

        # utg posotion is less 1 morw before because of Straddle
        sheet_name = str(t.position_utg_plus) + \
                     round_string + \
                     str(first_raiser_string) + str(first_raiser_number) + \
                     str(second_raiser_string) + str(second_raiser_number) + \
                     str(first_caller_string) + str(first_caller_number)

        if h.round_number == 2:
            sheet_name = 'R1R2R1A2'
        # add by zq 2020/3/24
        # sheet_name = '6R4C5'
#---------------------------------

        self.preflop_sheet_name = sheet_name
        return self.preflop_sheet_name
