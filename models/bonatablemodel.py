import re
from enum import Enum
from datetime import datetime
from datetime import timedelta

# const
Bonapoker_title_TexasHoldem_cn = r'BONA NLHE '
# Bonapoker_title_string1 = r'timeshow'
# Bonapoker_title_string1 = r'POKARA'
Bonapoker_title_Tounament2 = r'Freeroll'
Bonapoker_title_Tounament1 = r'Covid 19'
Name_Time_split_string = r' - Holdem NL'
Toney_split_name = r'Level:'
Toney_split_blinds = r'Blinds: '
Toney_split_blinds_next = r'Next blinds: '
Toney_split_blinds_ante = r'ante '
room_number_split_string = r' #'
blind_split_string = r'/'
Tbt_title_025051 = '025051'
Tbt_title_0512 = '0512'
Tbt_title_124 = '124'
Tbt_title_248 = '248'
Tbt_title_51020 = '51020'
# tbt_timeout_format = r'%H:%M:%S'

class TableTypes(Enum):
    tbt, normal, covid19, freeroll = ['TBT','NORMALROOM', 'TOUNAMENT1', 'TOUNAMENT2']
# BonaTableModels
class BonaTableModel(object):
    def __init__(self):
        
        self.remnent_time = timedelta(0)
        self.table_title = ''
        self.table_name = ''
        self.room_number = ''
        self.timeout = datetime.now()
        self.type = TableTypes.normal
        self.smallBlind = 0.01
        self.bigBlind = 0.02
        self.initialFunds = 2
        self.bots = []
        self.idle = True
        self.sit_count = 2
        self.other_players = []
        self.main_bot_whnd = 0
        self.bot_num = 0
        self.active_players = 0
        self.active_bots = 0
        self.playing_players = 0
        
    # Function Set and Get Idle status
    def setIdle(self, idle):
        self.idle = idle
    
    def getIdle(self):
        return self.idle
    # Function Set Active players
    def setActivePlayers(self, active_players):
        self.active_players = active_players
        self.active_bots = sum([v['status'] for v in self.bots])
        # self.minimum_funds_bot_whnd = 
        print('Active players :  ' + str(self.active_players))
        print('Active bots :  ' + str(self.active_bots))
    # Function Get there is or no other users
    def get_No_users(self):
        if self.active_bots == self.active_players and self.active_bots:
            return True
        else:
            return False
    # Function minimum Funds handles in Active bots
    def get_minimum_whnd(self):
        minimum_funds = 999999
        return_whnd = 0
        for i in self.bots:
            if i['status'] == 1 and minimum_funds > i['funds']:
                minimum_funds = i['funds']
                return_whnd = i['whnd']
        return return_whnd


    def get_sec(self, time_str):
        # """Get Seconds from time."""
        h, m, s = time_str.split(':')
        # print(time_str)
        return int(h) * 3600 + int(m) * 60 + int(float(s))

    def init_tablename(self, table_name):

        if self.table_name == table_name:
            return self.table_title

        self.table_name = table_name
        # TexasHoldem Cash Table
        if table_name.find(Bonapoker_title_TexasHoldem_cn) != -1 :
            table_name_cn = table_name.split(Name_Time_split_string)[0]
            self.table_title = re.split(Bonapoker_title_TexasHoldem_cn, table_name_cn)[1]
            
            [blinds, self.room_number] = self.table_title.split(room_number_split_string)
            
            self.smallBlind = re.split(blind_split_string, blinds)[0]
            if self.smallBlind.find('K') == len(self.smallBlind) - 1:
                self.smallBlind = float(self.smallBlind.split('K')[0]) * 1000
            else:
                self.smallBlind = float(self.smallBlind)
            # self.bigBlind = float(re.split(' ', re.split(blind_split_string, blinds)[1])[0])
            self.bigBlind = 2 * self.smallBlind
            blinds_num = len(re.findall(blind_split_string, blinds))
            if blinds_num == 2:
                table_timeout = table_name.split(Name_Time_split_string)[1]
                self.type = TableTypes.tbt
                self.remnent_time = timedelta(seconds = self.get_sec(table_timeout))
                self.timeout = datetime.now() + self.remnent_time
                self.initialFunds = self.bigBlind * 100
                self.sit_count = 8
            elif blinds_num == 1:
                self.type = TableTypes.normal
                self.initialFunds = self.bigBlind * 50
                self.sit_count = 6

            return self.table_title
        # TBT new title name Table 124, 248, 51020
        elif table_name.find(Tbt_title_124) != -1 or table_name.find(Tbt_title_248) != -1 or table_name.find(Tbt_title_51020) != -1 or table_name.find(Tbt_title_025051) != -1 :
            # Get Table tiltle
            self.table_title = table_name.split(Name_Time_split_string)[0]
            
            table_timeout = table_name.split(Name_Time_split_string)[1]
            self.remnent_time = timedelta(seconds = self.get_sec(table_timeout))
            self.timeout = datetime.now() + self.remnent_time

            # Get Big Blind and Small blind
            if table_name.find(Tbt_title_124) != -1:
                self.smallBlind = 1
            elif table_name.find(Tbt_title_025051) != -1:
                self.smallBlind = 0.25
            elif table_name.find(Tbt_title_248) != -1:
                self.smallBlind = 2
            elif table_name.find(Tbt_title_51020) != -1:
                self.smallBlind = 5

            self.bigBlind = 2 * self.smallBlind
            self.initialFunds = self.bigBlind * 100
           
            # Get Sitting count
            self.sit_count = 8
            # Get Table Type
            self.type = TableTypes.tbt

            return self.table_title
        
        # Covid 19 Tournaments Table
        elif (table_name.find(Bonapoker_title_Tounament1) != -1):
            # Get Table tiltle
            self.table_title = table_name.split(Toney_split_name)[0]
            # Get Big Blind and Small blind
            try:
                blinds_next = table_name.split(Toney_split_blinds)[1]
                blinds_ante = blinds_next.split(Toney_split_blinds_next)[0]
                blinds = blinds_ante.split(Toney_split_blinds_ante)[0]
                smallBlind = re.split(blind_split_string, blinds)[0]
                bigBlind = re.split(blind_split_string, blinds)[1]
                self.smallBlind = float(smallBlind.replace(',',''))
                self.bigBlind = float(bigBlind.replace(',',''))
            except:
                pass
            # Get Inistial Funds
            self.initialFunds = self.bigBlind * 5
            if self.initialFunds < 4000 : 
                self.initialFunds = 4000
            # Get Sitting count
            self.sit_count = 9
            # Get Table Type
            self.type = TableTypes.covid19

            return self.table_title

        # Freeroll Tournaments Table
        elif (table_name.find(Bonapoker_title_Tounament2) != -1):
            # Get Table tiltle
            self.table_title = table_name.split(Toney_split_name)[0]
            # Get Big Blind and Small blind
            try:
                blinds_next = table_name.split(Toney_split_blinds)[1]
                blinds_ante = blinds_next.split(Toney_split_blinds_next)[0]
                blinds = blinds_ante.split(Toney_split_blinds_ante)[0]
                smallBlind = re.split(blind_split_string, blinds)[0]
                bigBlind = re.split(blind_split_string, blinds)[1]
                self.smallBlind = float(smallBlind.replace(',',''))
                self.bigBlind = float(bigBlind.replace(',',''))
            except:
                pass
            # print(self.smallBlind)
            # Get Inistial Funds
            self.initialFunds = self.bigBlind * 5
            if self.initialFunds < 2000 : 
                self.initialFunds = 2000
            # Get Sitting count
            self.sit_count = 9
            # Get Table Type
            self.type = TableTypes.freeroll
            return self.table_title

    # Function Insert Handles
    def insert_handle(self, whnd):

        if whnd in list(i['whnd'] for i in self.bots):
            return False
        else:
            if self.bot_num == 0:
                self.main_bot_whnd = whnd
            bot_player = dict()
            bot_player['whnd'] = whnd
            bot_player['utg_position'] = 0
            bot_player['name'] = ''
            bot_player['status'] = 0
            bot_player['funds'] = 0
            bot_player['pot'] = ''
            bot_player['mycard'] = ''
            bot_player['decision'] = ''
            bot_player['equity'] = 0
            self.bots.append(bot_player)
            self.bot_num = len(self.bots)
            return True
    # Function delete Handles
    def delete_handle(self, whnd):
        if whnd not in list(i['whnd'] for i in self.bots):
            return False
        else:
            del self.bots[list(i['whnd'] for i in self.bots).index(whnd)]
            if self.main_bot_whnd == whnd:
                self.main_bot_whnd = self.bots[0]['whnd']
            self.bot_num = len(self.bots)
            return True

    def get_remnent_sec(self):
        self.remnent_time = self.timeout - datetime.now()
        return self.get_sec(str(self.remnent_time))

class BonaTableModelController(object):
    def __init__(self):

        # bonatablemodel = dict()
        # bonatablemodel['no'] = 0
        # bonatablemodel['title'] = ''
        # bonatablemodel['handle'] = ''
        # bonatablemodel['tablemodel'] = BonaTableModel()

        self.table_models_dic = {}
        self.table_models_num = 0

        # self.model.append(bonatablemodel)
    # Function Read Title
    def read_title(self, title):
        # Case of TexasHoldem
        if title.find(Bonapoker_title_TexasHoldem_cn) != -1 :
            table_name_cn = title.split(Name_Time_split_string)[0]
            re_title = table_name_cn.split(Bonapoker_title_TexasHoldem_cn)[1]
            return re_title
        # Case of Covid 19 Tournamnet
        elif (title.find(Bonapoker_title_Tounament1) != -1):
            table_name = title.split(Toney_split_name)[0]
            return table_name
        # Case of Freeroll Tournament   
        elif (title.find(Bonapoker_title_Tounament2) != -1):
            table_name = title.split(Toney_split_name)[0]
            return table_name
        # Case of TBT room 
        else:
            # Case of TBT 124 room
            if (title.find(Tbt_title_124) != -1):
                table_name = title.split(Name_Time_split_string)[0]
                return table_name
            # Case of TBT 025051 room
            elif (title.find(Tbt_title_025051) != -1):
                table_name = title.split(Name_Time_split_string)[0]
                return table_name
            # Case of TBT 248 room
            elif (title.find(Tbt_title_248) != -1):
                table_name = title.split(Name_Time_split_string)[0]
                return table_name
            # Case of TBT 51020 room
            elif (title.find(Tbt_title_51020) != -1):
                table_name = title.split(Name_Time_split_string)[0]
                return table_name
            # Case of TBT 248 room
    # Add In Model with title and handle   
    def add(self, title, handle):
        # new_tablemodel = BonaTableModel()
        current_title = self.read_title(title)
        
        if current_title not in self.table_models_dic:
            new_tablemodel = BonaTableModel()
            new_tablemodel.init_tablename(title)
            new_tablemodel.insert_handle(handle)
            self.table_models_dic[current_title] = new_tablemodel
            # print('I inserted new Table :   ' + title)
            return new_tablemodel        
        else:
            # del new_tablemodel
            self.table_models_dic[current_title].insert_handle(handle)
            return self.table_models_dic[current_title]
    # deleted In model by title and handle
    def delete(self, title, handle):

        del_title = self.read_title(title)
        if del_title in self.table_models_dic:
            if self.table_models_dic[del_title].delete_handle(handle):
                print("I deleted tiltle and windowhandle :  " + title +" ,  " + str(handle))
            if len(self.table_models_dic[del_title].bots) == 0:
                try:
                    del self.table_models_dic[del_title]
                    print('I deleted table_model :  ' + del_title)
                except Exception as e:
                    print(e)
            return True
        else: 
            return False






