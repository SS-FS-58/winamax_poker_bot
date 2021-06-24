import matplotlib

matplotlib.use('Qt5Agg')
import logging, logging.handlers
import pytesseract
import threading
import sys
from PIL import Image
from PyQt5 import QtWidgets, QtGui
import win32gui, win32api

from tools.mouse_mover import MouseMoverTableBased
import pandas as pd
from gui.gui_qt_ui import Ui_Pokerbot
from gui.gui_qt_logic import UIActionAndSignals
from tools.mongo_manager import StrategyHandler, UpdateChecker, GameLogger
from table_analysers.table_screen_based import TableScreenBased
from decisionmaker.current_hand_memory import History, CurrentHandPreflopState
from decisionmaker.montecarlo_python import run_montecarlo_wrapper
from decisionmaker.decisionmaker import Decision
from models.bonatablemodel import BonaTableModel
from models.bonatablemodel import BonaTableModelController
import re
import time
from datetime import datetime
from configobj import ConfigObj
import numpy as np
import pygetwindow as gw
import random

# Current version 
version = 2.33

# Table Title search strings
Bonapoker_title_string1 = r'NL Holdem'
# Bonapoker_title_string1 = r'timeshow'
# Bonapoker_title_string1 = r'POKARA'
Bonapoker_title_string3 = r'Freeroll'
Bonapoker_title_string2 = r'Covid 19'
Bonapoker_title_string4 = r'124'
Bonapoker_title_string_general = r'NL H'

# Where do you save the table screenshot
image_backup_filepath = r'D:\Poker_Bot\winamax_bot\screenshot_log'
screenshot_mode = False
# How many Windows Manager update every seconds
windows_update_time = 30

# Windows gaps
bona_windows_gap_max = 483 # 503 default value
bona_window_width = 1384
bona_window_height = 1047

# You can set table display left and width value.
display_left = 0

# You can set delay time for mouse after decision of bot
mouse_delay_min = 0
mouse_delay_gap = 3

collusion_bluff_fold_mode = False 


class ThreadManager(threading.Thread):
    def __init__(self, threadID, name, counter, gui_signals, whnd, bonatablemodel):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.gui_signals = gui_signals
        self.whnd = whnd
        self.logger = logging.getLogger('main')
        self.logger.setLevel(logging.DEBUG)
        self.game_logger = GameLogger()               
        self._stop = threading.Event()
        self.bonatablemodel = bonatablemodel

    # function using _stop function 
    def stop(self): 
        self._stop.set() 
  
    def stopped(self): 
        return self._stop.isSet() 

    def update_most_gui_items(self, preflop_state, p, m, t, d, h, gui_signals):
        try :
            sheet_name = t.preflop_sheet_name
        except:
            sheet_name = ''
        gui_signals.signal_decision.emit(str(d.decision + " " + sheet_name))
        gui_signals.signal_status.emit(d.decision) 
        range2 = ''
        if hasattr(t, 'reverse_sheet_name'):
            range = t.reverse_sheet_name
            if hasattr(preflop_state, 'range_column_name'):
                range2 = " " + preflop_state.range_column_name + ""
        else:
            range = str(m.opponent_range)
        if range == '1': range = 'All cards'

        if t.gameStage != 'PreFlop' and p.selected_strategy['preflop_override']:
            sheet_name=preflop_state.preflop_sheet_name

        gui_signals.signal_label_number_update.emit('equity', str(np.round(t.abs_equity * 100, 2)) + "%")
        gui_signals.signal_label_number_update.emit('required_minbet', str(np.round(t.minBet,2)))
        gui_signals.signal_label_number_update.emit('required_mincall', str(np.round(t.minCall,2)))
        # gui_signals.signal_lcd_number_update.emit('potsize', t.totalPotValue)
        gui_signals.signal_label_number_update.emit('gamenumber', str(int(self.game_logger.get_game_count(p.current_strategy))))
        gui_signals.signal_label_number_update.emit('assumed_players', str(int(t.assumedPlayers)))
        gui_signals.signal_label_number_update.emit('calllimit', str(np.round(d.finalCallLimit,2)))
        gui_signals.signal_label_number_update.emit('betlimit', str(np.round(d.finalBetLimit,2)))
        gui_signals.signal_label_number_update.emit('runs', str(int(m.runs)))
        gui_signals.signal_label_number_update.emit('sheetname', sheet_name)
        gui_signals.signal_label_number_update.emit('collusion_cards', str(m.collusion_cards))
        gui_signals.signal_label_number_update.emit('mycards', str(t.mycards))
        gui_signals.signal_label_number_update.emit('tablecards', str(t.cardsOnTable))
        gui_signals.signal_label_number_update.emit('opponent_range', str(range) + str(range2))
        gui_signals.signal_label_number_update.emit('mincallequity', str(np.round(t.minEquityCall, 2) * 100) + "%")
        gui_signals.signal_label_number_update.emit('minbetequity', str(np.round(t.minEquityBet, 2) * 100) + "%")
        gui_signals.signal_label_number_update.emit('outs', str(d.outs))
        gui_signals.signal_label_number_update.emit('initiative', str(t.other_player_has_initiative))
        gui_signals.signal_label_number_update.emit('round_pot', str(np.round(t.round_pot_value,2)))
        gui_signals.signal_label_number_update.emit('pot_multiple', str(np.round(d.pot_multiple,2)))

        if t.gameStage != 'PreFlop' and p.selected_strategy['use_relative_equity']:
            gui_signals.signal_label_number_update.emit('relative_equity', str(np.round(t.relative_equity,2) * 100) + "%")
            gui_signals.signal_label_number_update.emit('range_equity', str(np.round(t.range_equity,2) * 100) + "%")
        else:
            gui_signals.signal_label_number_update.emit('relative_equity', "")
            gui_signals.signal_label_number_update.emit('range_equity', "")


        # gui_signals.signal_lcd_number_update.emit('zero_ev', round(d.maxCallEV, 2))

        gui_signals.signal_pie_chart_update.emit(t.winnerCardTypeList)
        gui_signals.signal_curve_chart_update1.emit(h.histEquity, h.histMinCall, h.histMinBet, t.equity,
                                                    t.minCall, t.minBet,
                                                    'bo',
                                                    'ro')

        gui_signals.signal_curve_chart_update2.emit(t.power1, t.power2, t.minEquityCall, t.minEquityBet,
                                                    t.smallBlind, t.bigBlind,
                                                    t.maxValue_call,t.maxValue_bet,
                                                    t.maxEquityCall, t.max_X, t.maxEquityBet)

    def run(self):
        h = History(self.name)
        preflop_url, preflop_url_backup = u.get_preflop_sheet_url()
        # try:
        #     h.preflop_sheet = pd.read_excel(preflop_url, sheet_name=None)# update by zq 2020/3/24
        # except:
        #     h.preflop_sheet = pd.read_excel(preflop_url_backup, sheet_name=None)

        self.game_logger.clean_database()

        p = StrategyHandler()
        p.read_strategy()

        preflop_state = CurrentHandPreflopState()

        p.read_strategy()
        t = TableScreenBased(p, gui_signals, self.game_logger, version, self.whnd, self.bonatablemodel)
        # set sitting number 
        # t.sit_count = sit_counter
        mouse = MouseMoverTableBased(p.selected_strategy['pokerSite'], self.whnd)
        # mouse.move_mouse_away_from_buttons_jump                
        while True:
            if self.gui_signals.pause_thread:
                while self.gui_signals.pause_thread == True:
                    # time.sleep(1)
                    if self.gui_signals.exit_thread == True: sys.exit()

            if self.stopped(): 
                del h
                del p
                del t
                del mouse
                return

            ready = False
            while (not ready):
                ready = t.take_screenshot(True, p) and \
                        t.check_sit_in(h, t, p, gui_signals, mouse) and \
                        t.get_my_cards(h) and \
                        t.get_new_hand(mouse, h, p) and \
                        t.get_table_cards(h) and \
                        t.check_for_button() and \
                        t.check_fast_fold(h, p, mouse) and \
                        t.check_for_betbutton() and \
                        t.check_for_pot_bet_button() and \
                        t.get_current_call_value(p) and \
                        t.get_current_bet_value(p) and \
                        t.init_get_other_players_info() and \
                        t.get_empty_status() and \
                        t.get_dealer_position() and \
                        t.get_round_number(h) and \
                        t.get_other_player_names(p) and \
                        t.get_other_player_funds(p) and \
                        t.get_other_player_pots() and \
                        t.get_other_player_status(p, h)
                        

                    # Backup functions -------------------------------------
                    # ready = t.take_screenshot(True, p) and \
                    #     t.get_top_left_corner(p) and \
                    #     t.check_for_captcha(mouse) and \
                    #     t.get_lost_everything(h, t, p, gui_signals, mouse) and \
                    #     t.check_for_imback(mouse) and \
                    #     t.get_my_cards(h) and \
                    #     t.get_new_hand(mouse, h, p) and \
                    #     t.check_fast_fold(h, p, mouse) and \
                    #     t.get_table_cards(h) and \
                    #     t.upload_collusion_wrapper(p, h) and \
                    #     t.get_dealer_position() and \
                    #     t.get_snowie_advice(p, h) and \
                    #     t.check_for_button() and \
                    #     t.check_for_pot_bet_button() and \ 
                    #     t.get_round_number(h) and \
                    #     t.init_get_other_players_info() and \
                    #     t.get_other_player_names(p) and \
                    #     t.get_other_player_funds(p) and \
                    #     t.get_other_player_pots() and \
                    #     t.get_total_pot_value(h) and 
                    #     t.get_round_pot_value(h) and 
                    #     t.check_for_checkbutton() and \
                    #     t.get_other_player_status(p, h) and \
                    #     t.check_for_call() and \
                    #     t.check_for_betbutton() and \
                    #     t.check_for_allincall() and \
                    #     t.get_current_call_value(p) and \
                    #     t.get_current_bet_value(p)# and \
                    #     t.get_raise_value(p,mouse)

                #---------------------------------------------------------

                # Delete Classes
                # if not ready:
                #     del t
                #     del mouse

                # add by zq 2020/3/24
                # ready = True

            if not self.gui_signals.pause_thread:
                config = ConfigObj("config.ini")
                m = run_montecarlo_wrapper(p, self.gui_signals, config, ui, t, self.game_logger, preflop_state, h)
                d = Decision(t, h, p, self.game_logger)
                d.make_decision(t, h, p, self.logger, self.game_logger)
                if self.gui_signals.exit_thread: sys.exit()

                self.update_most_gui_items(preflop_state, p, m, t, d, h, self.gui_signals)

                # self.logger.info(
                #     "Equity: " + str(t.equity * 100) + "% -> " + str(int(t.assumedPlayers)) + " (" + str(
                #         int(t.other_active_players)) + "-" + str(int(t.playersAhead)) + "+1) Plr")
                # self.logger.info("Final Call Limit: " + str(d.finalCallLimit) + " --> " + str(t.minCall))
                # self.logger.info("Final Bet Limit: " + str(d.finalBetLimit) + " --> " + str(t.minBet))
                # self.logger.info(
                #     "Pot size: " + str((t.totalPotValue)) + " -> Zero EV Call: " + str(round(d.maxCallEV, 2)))
                # self.logger.info("+++++++++++++++++++++++ Decision: " + str(d.decision) + "+++++++++++++++++++++++")
                print("Table_Name :  ------ " + str(t.bonatablemodel.table_title) + "--------")
                print('My cards :   ' + str(t.mycards))
                print('BigBlind :   ' + str(t.bigBlind))
                print('initialFunds :   ' + str(t.bonatablemodel.initialFunds))
                print("My Funds :   " + str(t.myFunds))
                print("Game Stage :   " + str(t.gameStage))
                print("Table cards :   " + str(t.cardsOnTable))
                
                print(
                    "Pot size: " + str((t.totalPotValue)))
                print("Call value :   " + str(t.minCall))
                print("Betting values :   " + str(list(i['pot'] for i in t.current_betbtn_value)))
                print("other players Funds :   " + str(list(i['funds'] for i in t.other_players)))
                print("other players pot size :   " + str(list(i['pot'] for i in t.other_players)))
                print("other players status :   " + str(list(i['status'] for i in t.other_players)))
                print("playing players empty :   " + str(list(i['empty'] for i in t.other_players)))
                print(
                    "Equity: " + str(t.equity * 100) + "% -> " + str(int(t.assumedPlayers)) + " (" + str(
                        int(t.other_active_players)) + "-" + str(int(t.playersAhead)) + "+1) Plr")
                print("Final Call Limit :  " + str(d.finalCallLimit))
                print("Final Bet Limit :  " + str(d.finalBetLimit))
                print("+++++++++++++++++++++++   Decision :  " + str(d.decision) + "   +++++++++++++++++++++++")

                # time.sleep(mouse_delay_min + round(random.uniform(0, 1)* mouse_delay_gap))
                # if t.checkButton:
                #     d.decision = 'Check'
                # else:
                #     d.decision = 'Fold'

                
                    # mouse_target = d.decision
                    # mouse.mouse_action(mouse_target, t.tlc, t.potbetbutton)

                
                if t.allInCall:
                    mouse.bet_button = False

                mouse_target = d.decision
                if mouse_target == 'Call' and t.allInCall:
                    mouse_target = 'Call2'
                    # time.sleep(mouse_delay_min + round(random.uniform(0, 1)* mouse_delay_gap))
                
                if t.checkButton and d.decision == "Bet":
                    mouse_target = 'Bet3'
                # if d.decision != "Fold":
                time.sleep(mouse_delay_min + round(random.uniform(0, 1)* mouse_delay_gap))
                # elif t.bonatablemodel.type.value =='NORMALROOM' or t.bonatablemodel.type.value == 'TBT':
                #     time.sleep(mouse_delay_min + round(random.uniform(0, 1)* mouse_delay_gap))
                #     if d.outs > 4 and t.gameStage == "Flop":
                #         mouse_target = 'Call'
                #     elif d.outs > 8 and t.gameStage == "Turn":
                #         mouse_target = 'Call'
                if t.checkButton and d.decision == "Check" and h.histDecision == "Check":
                    mouse_target = "Bet"

                # mouse.mouse_action("All In", t.tlc, t.potbetbutton)

                print('outs :  ' + str(d.outs))

                if mouse_target == "All In" or mouse_target == "Precise bet":
                    mouse.mouse_action("Precise bet", t.tlc, t.myFunds)
                else:
                    mouse.mouse_action(mouse_target, t.tlc, t.potbetbutton)

                # if mouse_target == 'Bet Bluff':
                #     # time.sleep(mouse_delay_min + round(random.uniform(0, 1)* mouse_delay_gap))
                #     mouse.mouse_action(mouse_target, t.tlc, t.potbetbutton)
            
                    
                # set table staus
                t.table_model_data['decision'] = d.decision
                if d.decision != "Fold":
                    t.table_model_data['status'] = 1
                else:
                    t.table_model_data['status'] = 0
                # mouse.mouse_action("All In", t.tlc, t.potbetbutton)

                t.bonatablemodel.setIdle(True)
                # print("I finished my working :  " + t.bonatablemodel.table_title + str(t.table_model_data['whnd']) )
                # if not (mouse_target == 'Fold' or mouse_target == 'Call' or mouse_target == 'Check' or mouse_target == 'Call2'):
                #     mouse_target = 'Precise bet'
                # if not mouse_target == 'Precise bet':
                #     mouse.mouse_action(mouse_target, t.tlc, t.potbetbutton)
                # else:
                #     mouse.mouse_action('Precise bet', t.tlc, d.finalBetLimit)
                
                #  4/9/2020 del
                # t.time_action_completed = datetime.utcnow()
                if screenshot_mode:
                    filename = str(t.mycards) + str(d.decision) + str(t.bonatablemodel.table_title).replace("/", "_") + "_" + str(t.gameStage) + "_" + str(h.round_number) + r'{}.png'.format(datetime.now().strftime("%d%m%Y%H%M%S"))
                    t.entireScreenPIL.save(image_backup_filepath + "\\" + filename)
                    # print("Saving screenshot:  " + filename)
                    # self.gui_signals.signal_status.emit("Saving screenshot")


                # t_log_db = threading.Thread(name='t_log_db', target=self.game_logger.write_log_file, args=[p, h, t, d])
                # t_log_db.daemon = True
                # t_log_db.start()
                # self.game_logger.write_log_file(p, h, t, d)

                h.previousPot = t.totalPotValue
                h.histGameStage = t.gameStage
                h.histDecision = d.decision
                h.histEquity = t.equity
                h.histMinCall = t.minCall
                h.histMinBet = t.minBet
                h.hist_other_players = t.other_players
                h.first_raiser = t.first_raiser
                h.first_caller = t.first_caller
                h.previous_decision = d.decision
                h.lastRoundGameID = h.GameID
                h.previous_round_pot_value=t.round_pot_value
                h.last_round_bluff = False if t.currentBluff == 0 else True
                if t.gameStage == 'PreFlop':
                    preflop_state.update_values(t, d.decision, h, d)
                # self.logger.info("=========== round end ===========")


class WindowsManager(threading.Thread):
    def __init__(self, gui_signals):
        threading.Thread.__init__(self)
        self.bona_bot_tread_list = {}
        self.old_window_handles = []
        self.gui_signals = gui_signals
        self.window_num = 0
        self.tabletestmodel_controller = BonaTableModelController()
    def run(self): 
        while True:
            try:
                bona_windows_list = gw.getWindowsWithTitle(Bonapoker_title_string_general)
                # if len(gw.getWindowsWithTitle(Bonapoker_title_string2)) > 0:
                #     bona_windows_list.extend(gw.getWindowsWithTitle(Bonapoker_title_string2))
                if len(gw.getWindowsWithTitle(Bonapoker_title_string3)) > 0:
                    bona_windows_list.extend(gw.getWindowsWithTitle(Bonapoker_title_string3))
                # if len(gw.getWindowsWithTitle(Bonapoker_title_string_general)) > 0:
                #     bona_windows_list.extend(gw.getWindowsWithTitle(Bonapoker_title_string_general))
                
                if len(bona_windows_list) == 0:
                    new_model = BonaTableModel()
                    new_model = self.tabletestmodel_controller.add(Bonapoker_title_string1 + r'100 Level: 4 Blinds: 100/200 Next blinds: 150/300',0)
                    t1 = ThreadManager(1, "Test_Thread1", 1, gui_signals, 0 ,new_model)
                    screenshot_mode = False
                    t1.start()
                else: 
                    
                    if len(bona_windows_list) > 1:
                        bona_windows_gap = int((display_width - bona_window_width) / (len(bona_windows_list) - 1))
                    else:
                        bona_windows_gap = bona_windows_gap_max
                    if bona_windows_gap > bona_windows_gap_max:
                        bona_windows_gap = bona_windows_gap_max  
                    bots_num = 0
                    for bona_window in sorted(bona_windows_list, key=lambda x: x.left):

                        bona_window.resizeTo(bona_window_width, bona_window_height)
                        
                        # bona_window.moveTo(display_left + bots_num * bona_windows_gap, 0) 
                        
                        current_whnd = bona_window._hWnd
                        # add thread
                        if current_whnd not in self.bona_bot_tread_list:
                            # table_name_CN = re.split('- Holdem NL', bona_window.title)[0]
                            # table_name_EN = re.sub(Bonapoker_title_string1, 'Bona Table', table_name_CN)
                            new_model = BonaTableModel()
                            new_model = self.tabletestmodel_controller.add(bona_window.title,current_whnd)
                            self.bona_bot_tread_list[current_whnd] = ThreadManager(bots_num, bona_window.title, bots_num, self.gui_signals, current_whnd, new_model)
                            self.bona_bot_tread_list[current_whnd].daemon = True
                            self.bona_bot_tread_list[current_whnd].start()
                            print('Start Process Window :  ' + bona_window.title)
                            # self.bona_bot_tread_list[current_whnd].join()
                        elif current_whnd in self.old_window_handles:
                            self.bona_bot_tread_list[current_whnd].bonatablemodel.init_tablename(bona_window.title)
                            self.old_window_handles.remove(current_whnd)
                        else:
                            self.bona_bot_tread_list[current_whnd].bonatablemodel.init_tablename(bona_window.title)
                            
                        bots_num += 1
                    self.window_num = bots_num
                # delete thread
                for closed_whnd in self.old_window_handles:
                    self.bona_bot_tread_list[closed_whnd].stop()
                    self.tabletestmodel_controller.delete(self.bona_bot_tread_list[closed_whnd].name, closed_whnd)
                    print('End Process Window : ' + self.bona_bot_tread_list[closed_whnd].name)
                    del self.bona_bot_tread_list[closed_whnd]

                # update old windows
                self.old_window_handles = list(self.bona_bot_tread_list.keys())
            except Exception as e:
                print(e)
            time.sleep(windows_update_time)
            


# ==== MAIN PROGRAM =====
if __name__ == '__main__':
    fh = logging.handlers.RotatingFileHandler('log/pokerprogram.log', maxBytes=1000000, backupCount=10)
    fh.setLevel(logging.DEBUG)
    fh2 = logging.handlers.RotatingFileHandler('log/pokerprogram_info_only.log', maxBytes=1000000, backupCount=5)
    fh2.setLevel(logging.INFO)
    er = logging.handlers.RotatingFileHandler('log/errors.log', maxBytes=2000000, backupCount=2)
    er.setLevel(logging.WARNING)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    fh2.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    er.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    ch.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

    root = logging.getLogger()
    root.addHandler(fh)
    root.addHandler(fh2)
    root.addHandler(ch)
    root.addHandler(er)

    print(
        "This is a testversion and error messages will appear here. The user interface has opened in a separate window.")
    # Back up the reference to the exceptionhook
    sys._excepthook = sys.excepthook
    u = UpdateChecker()
    # u.check_update(version)


    def exception_hook(exctype, value, traceback):
        # Print the error and traceback
        logger = logging.getLogger('main')
        logger.setLevel(logging.DEBUG)
        print(exctype, value, traceback)
        logger.error(str(exctype))
        logger.error(str(value))
        logger.error(str(traceback))
        # Call the normal Exception hook after
        sys.__excepthook__(exctype, value, traceback)
        sys.exit(1)


    # Set the exception hook to our wrapping function
    sys.__excepthook__ = exception_hook

    # check for tesseract # add zq this
    pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'
    try:
        pytesseract.image_to_string(Image.open('pics/SN/mycards/3h.png'))
    except Exception as e:
        print(e)
        print(
            "Tesseract not installed. Please install it into the same folder as the pokerbot or alternatively set the path variable.")
        # subprocess.call(["start", 'tesseract-installer/tesseract-ocr-setup-3.05.00dev.exe'], shell=True)
        sys.exit()

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    ui = Ui_Pokerbot()
    ui.setupUi(MainWindow)
    MainWindow.setWindowIcon(QtGui.QIcon('resources/icon.ico'))

    gui_signals = UIActionAndSignals(ui)

    # t1 = ThreadManager(1, "Thread-1", 1, gui_signals, whnd)
    # t1.start()
    # bonapoker process thread
    
    
    windows_manager = WindowsManager(gui_signals)
    windows_manager.daemon = True
    windows_manager.start()

    MainWindow.show()
    try:
        sys.exit(app.exec_())
    except:
        print("Preparing to exit...")
        gui_signals.exit_thread = True



