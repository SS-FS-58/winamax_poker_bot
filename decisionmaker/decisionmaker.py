""""
Strategy Definition
t contains variables that have been scraped from the table
h contains values from the historical (last) decision
p contains values from the Strategy as defined in the xml file
"""

import logging
from enum import Enum
import random

from decisionmaker.base import DecisionBase, Collusion
from decisionmaker.curvefitting import *
from decisionmaker.montecarlo_python import *
from decisionmaker.outs_calculator import Outs_Calculator
import playsound


class DecisionTypes(Enum):
    i_am_back, fold, check, call, bet1, bet2, bet3, bet4, bet5, bet6, bet_bluff, call_deception, check_deception = ['Imback',
                                                                                                        'Fold', 'Check',
                                                                                                        'Call', 'Bet',
                                                                                                        'Bet 1/2 POT',
                                                                                                        'Bet 2/3 POT',
                                                                                                        'Bet 3/4 POT',
                                                                                                        'Bet pot',
                                                                                                        'All In',
                                                                                                        'Bet Bluff',
                                                                                                        'Call Deception',
                                                                                                        'Check Deception']


class GameStages(Enum):
    PreFlop, Flop, Turn, River = ['PreFlop', 'Flop', 'Turn', 'River']




class Decision(DecisionBase):
    def __init__(self, t, h, p, l):
        self.logger = logging.getLogger('decision')
        self.logger.setLevel(logging.DEBUG)
        # t.bigBlind = float(p.selected_strategy['bigBlind'])
        # t.smallBlind = float(p.selected_strategy['smallBlind'])
        # t.bigBlind = t.bonatablemodel.
        self.decision = DecisionTypes.fold
        t.update_table()
        t.bigBlindMultiplier = t.bigBlind / 0.02
        self.collusion_bluff_fold_mode = False
        pots = [player['pot'] for player in t.other_players if type(player['pot']) != str]
        try:
            self.max_player_pot = max(pots)
            # self.logger.debug("Highest player pot: %s",self.max_player_pot)
        except:
            self.max_player_pot = 0
        # self.logger.debug("Round pot: "+str(t.round_pot_value))
        if t.round_pot_value==0:
            t.round_pot_value=t.bigBlind*4
            # self.logger.debug("Assuming round pot is 4*bigBlind")
        self.pot_multiple = self.max_player_pot / t.round_pot_value
        if self.pot_multiple == '':
            self.pot_multiple = 0

        if p.selected_strategy['use_pot_multiples']:
            # self.logger.info("Using pot multiple: Replacing mincall and minbet: " + str(self.pot_multiple))
            t.minCall = self.pot_multiple
            t.minBet = self.pot_multiple
        else:
            try:
                # temp add by zq 2020/3/30
                t.minCall = float(t.currentCallValue)
                # print('--------------MinCall---------------')
                # print(t.minCall)
                # t.minCall = float(50.0)
            except:
                t.minCall = float(0.0)
                if t.checkButton == False:
                    # self.logger.warning(
                    #     "Failed to convert current Call value, saving error.png, deriving from bet value, result:")
                    self.DeriveCallButtonFromBetButton = True
                    # add by zq 2020/3/24
                    t.minCall = np.round(10 / 2, 2)
                    # t.minCall = np.round(float(t.get_current_bet_value(p)) / 2, 2)
                    # self.logger.info("mincall: " + str(t.minCall))
                    # adjMinCall=minCall*c1*c2

            try:
                t.minBet = float(t.currentBetValue)
                t.opponentBetIncreases = t.minBet - h.myLastBet
            except:
                # self.logger.warning("Betvalue not recognised!")
                t.minBet = float(100.0)
                t.opponentBetIncreases = 0

        if t.gameStage != 'PreFlop' and p.selected_strategy['use_relative_equity']:
            # self.logger.info("Replacing equity with relative equity")
            t.equity = t.relative_equity
        else:
            t.equity = t.abs_equity
            # self.logger.info("Use absolute equity")
            

        out_multiplier = p.selected_strategy['out_multiplier']
        oc = Outs_Calculator()
        if 3 <= len(t.cardsOnTable) <= 4:  #
            try:
                outs = oc.evaluate_hands(t.mycards, t.cardsOnTable, oc)
                print(" Current hand result :   " + oc.hand_result)
                print()
            except:
                outs = 0
                # self.logger.critical("Error in outs calculation!")
        else:
            outs = 0
        self.out_adjustment = outs * out_multiplier * .01

        self.outs = outs

        # if outs > 0:
            # self.logger.info("Minimum equity is reduced because of outs by percent: %s", int(self.out_adjustment * 100))

        self.preflop_adjustment = -float(
            p.selected_strategy['pre_flop_equity_reduction_by_position']) * t.position_utg_plus

        if not np.isnan(t.first_raiser_utg):
            self.preflop_adjustment += float(p.selected_strategy['pre_flop_equity_increase_if_bet']) + (
                (5 - t.first_raiser_utg) * 0.01)

        if not np.isnan(t.first_caller_utg):
            self.preflop_adjustment += float(p.selected_strategy['pre_flop_equity_increase_if_call']) + (
                (5 - t.first_caller_utg) * 0.01)

        # in case the other players called my bet become less aggressive and make an adjustment for the second round
        if (h.histGameStage == t.gameStage and h.lastRoundGameID == h.GameID) or h.lastSecondRoundAdjustment > 0:
            if t.gameStage == 'PreFlop':
                self.secondRoundAdjustment = float(p.selected_strategy['secondRoundAdjustmentPreFlop'])
            else:
                self.secondRoundAdjustment = float(p.selected_strategy['secondRoundAdjustment'])

            secondRoundAdjustmentPowerIncrease = int(p.selected_strategy['secondRoundAdjustmentPowerIncrease'])
        else:
            self.secondRoundAdjustment = 0
            secondRoundAdjustmentPowerIncrease = 0

        P = float(t.totalPotValue)
        self.maxCallEV = self.calc_EV_call_limit(t.equity, P)
        print( " Max Call Limit :   " + str(self.maxCallEV))
        # self.maxBetEV = self.calc_bet_limit(t.equity, P, float(p.selected_strategy['c']), t, logger)
        # self.logger.debug("Max call EV: " + str(self.maxCallEV))

        self.DeriveCallButtonFromBetButton = False

        self.potAdjustmentPreFlop = t.totalPotValue / t.bigBlind / 250 * float(
            p.selected_strategy['potAdjustmentPreFlop'])
        self.potAdjustmentPreFlop = min(self.potAdjustmentPreFlop,
                                        float(p.selected_strategy['maxPotAdjustmentPreFlop']))

        self.potAdjustment = t.totalPotValue / t.bigBlind / 250 * float(p.selected_strategy['potAdjustment'])
        self.potAdjustment = min(self.potAdjustment, float(p.selected_strategy['maxPotAdjustment']))

        if t.gameStage == GameStages.PreFlop.value:
            t.power1 = float(p.selected_strategy['PreFlopCallPower'])
            t.minEquityCall = float(
                p.selected_strategy[
                    'PreFlopMinCallEquity']) + self.secondRoundAdjustment - self.potAdjustmentPreFlop + self.preflop_adjustment
            t.minCallAmountIfAboveLimit = t.bigBlind * 2
            t.potStretch = 1
            t.maxEquityCall = 1
        elif t.gameStage == GameStages.Flop.value:
            # t.power1 = int(round(float(p.selected_strategy['FlopCallPower']))) + secondRoundAdjustmentPowerIncrease
            t.power1 = float(p.selected_strategy['FlopCallPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityCall = float(
                p.selected_strategy[
                    'FlopMinCallEquity']) + self.secondRoundAdjustment - self.potAdjustment - self.out_adjustment
            t.minCallAmountIfAboveLimit = t.bigBlind * 2
            t.potStretch = 1
            t.maxEquityCall = 1
        elif t.gameStage == GameStages.Turn.value:
            # t.power1 = int(round(float(p.selected_strategy['TurnCallPower']))) + secondRoundAdjustmentPowerIncrease
            t.power1 = float(p.selected_strategy['TurnCallPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityCall = float(
                p.selected_strategy[
                    'TurnMinCallEquity']) + self.secondRoundAdjustment - self.potAdjustment - self.out_adjustment
            t.minCallAmountIfAboveLimit = t.bigBlind * 2
            t.potStretch = 1
            t.maxEquityCall = 1
        elif t.gameStage == GameStages.River.value:
            # t.power1 = int(round(float(p.selected_strategy['RiverCallPower']))) + secondRoundAdjustmentPowerIncrease
            t.power1 = float(p.selected_strategy['RiverCallPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityCall = float(
                p.selected_strategy['RiverMinCallEquity']) + self.secondRoundAdjustment - self.potAdjustment
            t.minCallAmountIfAboveLimit = t.bigBlind * 2
            t.potStretch = 1
            t.maxEquityCall = 1
        t.power1 = round(t.power1)
        if t.power1 == 0:
            t.power1 = 1
        # t.maxValue_call = float(p.selected_strategy['initialFunds']) * t.potStretch
        t.maxValue_call = float(t.bonatablemodel.initialFunds) * t.potStretch
        minimum_curve_value = 0 if p.selected_strategy['use_pot_multiples'] else t.smallBlind
        # minimum_curve_value = 0
        minimum_curve_value2 = 0 if p.selected_strategy['use_pot_multiples'] else t.minCallAmountIfAboveLimit
        d = Curvefitting(np.array([t.equity]), minimum_curve_value, minimum_curve_value2, t.maxValue_call, t.minEquityCall,
                         t.maxEquityCall, t.max_X, t.power1)
        self.maxCallE = round(d.y[0], 2)

        if not t.other_player_has_initiative and not t.checkButton:
            opponent_raised_without_initiative = 1
            # self.logger.info(
                # "Other player has no initiative and there is no check button. Activate increased required equity for betting")
        else:
            opponent_raised_without_initiative = 0
            # self.logger.debug("Increase required equity for betting not acviated")

        opponent_raised_without_initiative_flop = 0.1 * p.selected_strategy[
            'opponent_raised_without_initiative_flop'] * opponent_raised_without_initiative
        opponent_raised_without_initiative_turn = 0.1 * p.selected_strategy[
            'opponent_raised_without_initiative_turn'] * opponent_raised_without_initiative
        opponent_raised_without_initiative_river = 0.1 * p.selected_strategy[
            'opponent_raised_without_initiative_river'] * opponent_raised_without_initiative

        if t.gameStage == GameStages.PreFlop.value:
            # t.power2 = int(round(float(p.selected_strategy['PreFlopBetPower']))) + secondRoundAdjustmentPowerIncrease
            t.power2 = float(p.selected_strategy['PreFlopBetPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityBet = float(
                p.selected_strategy[
                    'PreFlopMinBetEquity']) + self.secondRoundAdjustment - self.potAdjustment + self.preflop_adjustment
            t.maxEquityBet = float(p.selected_strategy['PreFlopMaxBetEquity'])
            t.minBetAmountIfAboveLimit = t.bigBlind * 2
        elif t.gameStage == GameStages.Flop.value:
            # t.power2 = int(round(float(p.selected_strategy['FlopBetPower']))) + secondRoundAdjustmentPowerIncrease
            t.power2 = float(p.selected_strategy['FlopBetPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityBet = float(
                p.selected_strategy[
                    'FlopMinBetEquity']) + self.secondRoundAdjustment - self.out_adjustment + opponent_raised_without_initiative_flop
            t.maxEquityBet = 1
            t.minBetAmountIfAboveLimit = t.bigBlind * 2
        elif t.gameStage == GameStages.Turn.value:
            # t.power2 = int(round(float(p.selected_strategy['TurnBetPower']))) + secondRoundAdjustmentPowerIncrease
            t.power2 = float(p.selected_strategy['TurnBetPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityBet = float(
                p.selected_strategy[
                    'TurnMinBetEquity']) + self.secondRoundAdjustment - self.out_adjustment + opponent_raised_without_initiative_turn
            t.maxEquityBet = 1
            t.minBetAmountIfAboveLimit = t.bigBlind * 2
        elif t.gameStage == GameStages.River.value:
            # t.power2 = int(round(float(p.selected_strategy['RiverBetPower']))) + secondRoundAdjustmentPowerIncrease
            t.power2 = float(p.selected_strategy['RiverBetPower']) + secondRoundAdjustmentPowerIncrease
            t.minEquityBet = float(
                p.selected_strategy[
                    'RiverMinBetEquity']) + self.secondRoundAdjustment + opponent_raised_without_initiative_river
            t.maxEquityBet = 1
            t.minBetAmountIfAboveLimit = t.bigBlind * 2

        # adjustment for player profile
        if t.isHeadsUp and t.gameStage != GameStages.PreFlop.value:
            try:
                self.flop_probability_player = l.get_flop_frequency_of_player(t.PlayerNames[0])
                # self.logger.info(
                #     "Probability profile of : " + t.PlayerNames[0] + ": " + str(self.flop_probability_player))
            except:
                self.flop_probability_player = np.nan

            if self.flop_probability_player < 0.30:
                # self.logger.info("Defensive play due to probability profile")
                t.power1 += 2
                t.power2 += 2
                self.player_profile_adjustment = 2
            elif self.flop_probability_player > 0.60:
                # self.logger.info("Agressive play due to probability profile")
                t.power1 -= 2
                t.power2 -= 2
                self.player_profile_adjustment = -2
            else:
                self.player_profile_adjustment = 0
        t.power2 = round(t.power2)
        if t.power2 == 0:
            t.power2 = 1
        # t.maxValue_bet = float(p.selected_strategy['initialFunds2']) * t.potStretch
        t.maxValue_bet = float(t.bonatablemodel.initialFunds) * t.potStretch
        # minimum_curve_value = 0
        d = Curvefitting(np.array([t.equity]), minimum_curve_value, t.minBetAmountIfAboveLimit, t.maxValue_bet, t.minEquityBet,
                         t.maxEquityBet, t.max_X, t.power2)
        self.maxBetE = round(d.y[0], 2)

        self.finalCallLimit = self.maxCallE  # min(self.maxCallE, self.maxCallEV)
        self.finalBetLimit = self.maxBetE  # min(self.maxBetE, self.maxCallEV)
        self.invest = 0
        # print('--------------final Bet and Call Limit---------------')
        # print(self.finalBetLimit)
        # print(self.finalCallLimit)

    def preflop_table_analyser(self, t, logger, h, p):
        if t.gameStage == GameStages.PreFlop.value and len(t.mycards) == 2:
            m = MonteCarlo()
            crd1, crd2 = m.get_two_short_notation(t.mycards)
            crd1 = crd1.upper()
            crd2 = crd2.upper()

            limpin_range = 0.86 - t.minEquityCall
            raise_call_range = 0.1
            bet_range = 0.09
            raise_range = 0.03

            
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
            preflop_range = [
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", \
                "AKS", "AQS", "AJS", "ATS", "KQS", "KJS", "QJS", \
                "AKO", "AQO" ],
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", \
                "AKS", "AQS", "AJS", "ATS",  "KQS", "KJS", "KTS", "QJS", "QTS", "JTS", \
                "AKO", "AQO"],
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", 
                "AKS", "AQS", "AJS", "ATS",  "A9S", "A5S", "KQS", "KJS", "KTS", "QJS", "QTS", "JTS", "T9S", "98S", "87S", \
                "AKO", "AQO", "AJ0", "KQO"], 
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", \
                "AKS", "AQS", "AJS", "ATS",  "A9S", "A8S", "A7S", "A6S", "A5S", "A4S", "A3S", "A2S", \
                "KQS", "KJS", "KTS", "QJS", "QTS", "JTS", "T9S", "98S", "87S", "76S", "65S", \
                "AKO", "AQO", "AJ0", "KQO"],
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", \
                "AKS", "AQS", "AJS", "ATS",  "A9S", "A8S", "A7S", "A6S", "A5S", "A4S", "A3S", "A2S", \
                "KQS", "KJS", "KTS", "K9S", "K8S", "K7S",  "QJS", "QTS", "Q9S", "JTS", "J9S", "T9S", "T8S", \
                "98S", "87S", "76S", "65S", "54S", \
                "AKO", "AQO", "AJ0", "ATO", "KQO", "KJO", "QJO"],
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", \
                "AKS", "AQS", "AJS", "ATS",  "A9S", "A8S", "A7S", "A6S", "A5S", "A4S", "A3S", "A2S", \
                "KQS", "KJS", "KTS", "K9S", "K8S", "K7S",  "K6S", "K5S", "QJS", "QTS", "Q9S", "Q8S", "Q7S", "Q6S", \
                "JTS", "J9S", "JTS", "J9S", "J8S", "J7S", "T9S", "T8S", "T7S", "98S", "97S", "87S", "86S", "76S", "65S", "54S", \
                "AKO", "AQO", "AJ0", "ATO", "A9O", "A8O", "A5O", "KQO", "KJO", "KTO", "QJO", "JTO"],
                ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", \
                "AKS", "AQS", "AJS", "ATS",  "A9S", "A8S", "A7S", "A6S", "A5S", "A4S", "A3S", "A2S", \
                "KQS", "KJS", "KTS", "K9S", "K8S", "K7S",  "K6S", "K5S", "K4S", "K3S", "K2S", \
                "QJS", "QTS", "Q9S", "Q8S", "Q7S", "Q6S", "Q5S", "Q4S", "Q3S", "Q2S", \
                "JTS", "J9S", "JTS", "J9S", "J8S", "J7S", "J6S", "J5S", "J4S", "J3S", \
                "T9S", "T8S", "T7S", "T8S", "T7S", "98S", "97S", "96S", "95S", "87S", "86S", "85S", \
                "76S", "75S", "74S", "65S", "64S", "63S", "54S", "53S", "43S", "32S", \
                "AKO", "AQO", "AJ0", "ATO", "A9O", "A8O", "A7O", "A6O", "A5O", "A4O", "A3O", "A2O", \
                "KQO", "KJO", "KTO", "K9O", "K8O", "K7O", "QJO", "QTO", "Q9O", "Q8O", "JTO", "J9O", "J8O", \
                "T9O", "T8O", "98O", "87O"],
                ]
            # Limpin card set
            print("table_count" + str(t.playing_players))
            limpin_range_level = round(5 + t.position_utg_plus / 3)
            if(t.playing_players==2):
                limpin_range_level = 7 + round(t.position_utg_plus / 2)
            elif(t.playing_players == 3):
                limpin_range_level = 6 + round(t.position_utg_plus / 3)
            
            limpin_cards = set()
            for i in range(limpin_range_level):
                limpin_cards.update(tier[i])
            
            # Raise Call card set
            raise_call_level = round(2 + t.position_utg_plus / 4)
            raise_call_cards = set()
            if(t.playing_players==2):
                raise_call_level = 6 + round(t.position_utg_plus / 2)
            elif(t.playing_players == 3):
                raise_call_level = 5 + round(t.position_utg_plus / 3)
            
            for i in range(raise_call_level):
                raise_call_cards.update(tier[i])

            # bet card set
            bet_range_level = round(4 + t.position_utg_plus / 3)
            if(t.playing_players==2):
                bet_range_level = 6 + round(t.position_utg_plus / 2)
            elif(t.playing_players == 3):
                bet_range_level = 5 + round(t.position_utg_plus / 3)
            
            bet_cards = set()
            for i in range(bet_range_level):
                bet_cards.update(tier[i])
            
            # 3-bet card set
            # bet3_range_level = round(1 + random.uniform(0, 1))
            bet3_range_level = round(1 + t.position_utg_plus / 8)

            if(t.playing_players==2):
                bet3_range_level = 1 + round(t.position_utg_plus / 2)
            elif(t.playing_players == 3):
                bet3_range_level = 2 + round(t.position_utg_plus / 3)
            
            bet3_cards = set()
            for i in range(1):
                bet3_cards.update(tier[i])
            
            # 3-bet call set
            bet3_call_card = set()
            bet3_call_card.update(tier[0])


            # limpin_cards = m.get_opponent_allowed_cards_list(limpin_range)
            # raise_call_cards = m.get_opponent_allowed_cards_list(raise_call_range)
            # bet_cards = m.get_opponent_allowed_cards_list(bet_range)
            # raise_range = m.get_opponent_allowed_cards_list(raise_range)
            # bet4_range = set(["AA", "KK", "AKS", "AKO", "QQ"])

            # limpin_cards.add("33")
            # limpin_cards.add("22")

            # print(call_cards)
            # print(raise_call_cards)
            # call_cards = m.get_opponent_allowed_cards_list(0.5)
            # bet_cards = m.get_opponent_allowed_cards_list(0.2)
            
            # decision Call

            if t.minCall < t.bigBlind * 3:
                #call
                if t.callButton and (crd1 in limpin_cards or crd2 in limpin_cards or crd1[0:2] in limpin_cards):
                    self.decision = DecisionTypes.call
                    self.invest = t.minCall
                if t.raiseButton and (crd1 in bet_cards or crd2 in bet_cards or crd1[0:2] in bet_cards):
                    self.decision = DecisionTypes.bet2
                    # self.decision = DecisionTypes.call
                    self.invest = t.minCall
                else:
                    self.decision = DecisionTypes.fold
                
            elif t.bigBlind * 10 >= t.minCall and t.minCall >= t.bigBlind * 3:
                
                if (t.allInCall or t.callButton) and (crd1 in raise_call_cards or crd2 in raise_call_cards or crd1[0:2] in raise_call_cards):
                    if t.minCall <= t.bigBlind * 10:
                        self.decision = DecisionTypes.call
                        self.invest = t.minCall
                    elif (crd1 in bet3_cards or crd2 in bet3_cards or crd1[0:2] in bet3_cards):
                        self.decision = DecisionTypes.call
                        self.invest = t.minCall
                        self.decision = DecisionTypes.bet2
                        self.invest = t.current_betbtn_value[0]["pot"]
                    else:
                        self.decision = DecisionTypes.call
                        self.invest = t.minCall
                if t.raiseButton and (crd1 in bet3_cards or crd2 in bet3_cards or crd1[0:2] in bet3_cards):
                    if t.minCall <= t.bigBlind * 10:
                        self.decision = DecisionTypes.bet2
                        self.invest = t.current_betbtn_value[0]["pot"]
                    elif (crd1 in bet3_call_card or crd2 in bet3_call_card or crd1[0:2] in bet3_call_card):
                        self.decision = DecisionTypes.bet2
                        self.invest = t.current_betbtn_value[0]["pot"]
                    else:
                        self.decision = DecisionTypes.call
            
            else:
                if t.raiseButton and (crd1 in bet3_call_card or crd2 in bet3_call_card or crd1[0:2] in bet3_call_card):
                    self.decision = DecisionTypes.bet3
                    self.invest = t.current_betbtn_value[1]["pot"]
                elif (t.allInCall or t.callButton) and (crd1 in bet3_call_card or crd2 in bet3_call_card or crd1[0:2] in bet3_call_card):
                    self.decision = DecisionTypes.call
                    self.invest = t.minCall
                else:
                    self.decision = DecisionTypes.fold



            # if t.callButton and (crd1 in limpin_cards or crd2 in limpin_cards or crd1[0:2] in limpin_cards) and np.isnan(t.first_raiser_utg):
            #     self.decision = DecisionTypes.call
            # elif t.callButton and (crd1 in raise_call_cards or crd2 in raise_call_cards or crd1[0:2] in raise_call_cards) and not np.isnan(t.first_raiser_utg):
            #     self.decision = DecisionTypes.call
            # else:
            #     self.decision = DecisionTypes.fold
            # # decision bet1
            # if t.betButton and (crd1 in bet_cards or crd2 in bet_cards or crd1[0:2] in bet_cards):
            #     self.decision = DecisionTypes.bet1  
            # elif t.raiseButton and (crd1 in raise_range or crd2 in raise_range or crd1[0:2] in raise_range):
            #     self.decision = DecisionTypes.bet1
            # # decision bet2
            # if t.betButton and (crd1 in raise_range or crd2 in raise_range or crd1[0:2] in raise_range):
            #     self.decision = DecisionTypes.bet2   
            # # decision bet4
            # if t.betButton and (crd1 in bet4_range or crd2 in bet4_range or crd1[0:2] in bet4_range):
            #     self.decision = DecisionTypes.bet3     

            # sheet_name = t.derive_preflop_sheet_name(t, h, t.first_raiser_utg, t.first_caller_utg, t.second_raiser_utg)

            # # self.logger.info("Sheet name: " + sheet_name)
            # excel_file = h.preflop_sheet
            # info_sheet = excel_file['Info']
            # sheet_version = info_sheet['Version'].iloc[0]
            # # self.logger.info("Preflop Excelsheet Version: " + str(sheet_version))
            # if sheet_name in excel_file:
            #     sheet = excel_file[sheet_name]
            #     # self.logger.debug("Sheetname found")
            # elif sheet_name[:-2] in excel_file:
            #     # self.logger.warning("Sheetname " + sheet_name + " not found, cutting last element: " + sheet_name[:-2])
            #     sheet = excel_file[sheet_name[:-2]]
            # else:
            #     backup_sheet_name = '2R1'
            #     sheet = excel_file[backup_sheet_name]
            #     # self.logger.warning("Sheetname not found: " + sheet_name)
            #     # self.logger.warning("Backup sheet in use: " + backup_sheet_name)
            #     # t.entireScreenPIL.save('sheet_not_found.png')
            # sheet['Hand'] = sheet['Hand'].apply(lambda x: str(x).upper())

            # handlist = set(sheet['Hand'].tolist())
            # self.preflop_bot_ranges = handlist

            # found_card = ''

            # if crd1 in handlist:
            #     found_card = crd1
            # elif crd2 in handlist:
            #     found_card = crd2

            # # self.logger.debug("Looking in preflop table for: " + crd1 + ", " + crd2 + ", " + crd1[0:2])
            # # self.logger.debug("Found in preflop table: " + found_card)

            # if found_card != '':
            #     call_probability = sheet[sheet['Hand'] == found_card]['Call'].iloc[0]
            #     bet_probability = sheet[sheet['Hand'] == found_card]['Raise'].iloc[0]
            #     rnd = np.random.uniform(0, 100, 1)[0] / 100
            #     # self.logger.debug("Random number: " + str(rnd))
            #     # self.logger.debug("Call probability: " + str(call_probability))
            #     # self.logger.debug("Raise probability: " + str(bet_probability))
            #     print("Random number: " + str(rnd))
            #     print("Call probability: " + str(call_probability))
            #     print("Raise probability: " + str(bet_probability))
                                
            #     if rnd < call_probability:
            #         self.decision = DecisionTypes.call
            #         # self.logger.info('Preflop calling activated from preflop table')

            #     elif rnd >= call_probability and rnd <= bet_probability + call_probability:
            #         if sheet_name in ['1', '2', '3', '4', '5']:
            #             # self.decision = DecisionTypes.bet1
            #             self.decision = DecisionTypes.call
            #             # self.logger.info('Preflop betting 3 activated from preflop table')
            #         else:
            #             self.decision = DecisionTypes.bet1
            #             # self.logger.info('Preflop betting 4 activated from preflop table')
            #             # 1, 2, 3, 4 = half pot
            #             # 5 = pot and the
            #             # rest POT
            #     else:
            #         self.decision = DecisionTypes.fold
            #         # self.logger.info('Preflop folding from preflop table')
            # else:
            #     self.decision = DecisionTypes.fold
            #     # self.logger.info('Preflop folding, hands not found in preflop table')

            t.currentBluff = 0

    def calling(self, t, p, h):
        # print('finalCalllimit :  ' + str(self.finalCallLimit))
        # print('minCall :  ' + str(t.minCall))
        if self.finalCallLimit < t.minCall:
            self.decision = DecisionTypes.fold
            
            # self.logger.debug("Call limit exceeded: suggest folding")
        if self.finalCallLimit >= t.minCall:
            self.decision = DecisionTypes.call
            self.invest = t.minCall
            # self.logger.debug("Call limit ok: calling would be fine")

    def betting(self, t, p, h):
        # preflop
        # print('finalBetlimit :  ' + str(self.finalBetLimit))
        # print('minBet2 :  ' + str(t.current_betbtn_value[1]["pot"]))
        # print('minBet3 :  ' + str(t.current_betbtn_value[2]["pot"]))
        
        if t.gameStage == GameStages.PreFlop.value:
            if self.finalBetLimit > t.current_betbtn_value[1]["pot"]:#float(t.totalPotValue) / 2:
                # self.logger.info("Bet3 condition met")
                self.decision = DecisionTypes.bet2

            if (self.finalBetLimit > t.current_betbtn_value[2]["pot"]) and \
                    (t.first_raiser_utg >= 0 or t.first_caller_utg >= 0):
                # self.logger.info("Bet4 condition met")
                self.decision = DecisionTypes.bet3

        stage = t.gameStage.lower()
        # flop turn river
        if t.gameStage != GameStages.PreFlop.value:

            # multiple decision
            if p.selected_strategy['use_pot_multiples']:
                if self.finalBetLimit > t.minBet and \
                        (not t.checkButton or not t.other_player_has_initiative or
                        p.selected_strategy[stage + '_betting_condidion_1'] == 0):
                    self.decision = DecisionTypes.bet2
                    # self.logger.info("Bet3 activated (based on pot multiple decision)")


            # absolute value decision
            else:
                if not (h.round_number > 0 and h.previous_decision == DecisionTypes.check_deception.value):
                    # bet1
                    if(t.minBet == 0):
                        t.minBet = t.bigBlind
                    if self.finalBetLimit >= t.minBet and \
                            (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                                    stage + '_betting_condidion_1'] == 0):
                        self.decision = DecisionTypes.call
                        self.invest = t.minCall
                        # if float(self.invest) > float(t.myFunds*2/3):
                            # self.decision = DecisionTypes.bet5

                        # self.logger.info("Bet1 condition met")
                    # bet2
                    # if self.finalBetLimit >= (t.minBet + t.bigBlind * float(p.selected_strategy['BetPlusInc'])) and ((
                    # if t.current_betbtn_value[0]["pot"] > 0 and self.finalBetLimit >= t.current_betbtn_value[0]["pot"] and ((
                    #          t.gameStage == GameStages.Turn.value and t.totalPotValue > t.bigBlind * 3) or
                    #          t.gameStage == GameStages.River.value) and \
                    #         (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                    #                 stage + '_betting_condidion_1'] == 0):
                    #     self.decision = DecisionTypes.bet2
                    if t.current_betbtn_value[0]["pot"] > 0 and self.finalBetLimit >= t.current_betbtn_value[0]["pot"] and \
                            (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                                    stage + '_betting_condidion_1'] == 0):
                        self.decision = DecisionTypes.bet1
                        if t.checkButton:
                            self.invest = t.bigBlind * 3
                        else:
                            self.invest = t.minCall * 2 
                        # if float(self.invest) > float(t.myFunds* 2/3):
                            # self.decision = DecisionTypes.bet5
                        # self.logger.info("Bet2 condition met")
                    # bet3
                    # self.logger.debug(
                    #     "Checking for betting half pot: " + str(
                    #         float(t.totalPotValue) / 2) + " needs be be below or equal " + str(
                    #         self.finalBetLimit))
                    if t.current_betbtn_value[1]["pot"] > 0 and (self.finalBetLimit >= t.current_betbtn_value[1]["pot"]) \
                            and (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                                    stage + '_betting_condidion_1'] == 0):
                        # self.logger.info("Bet3 condition met")
                        self.decision = DecisionTypes.bet2
                        self.invest = t.current_betbtn_value[0]["pot"]
                        # if float(self.invest) > float(t.myFunds*2/3):
                            # self.decision = DecisionTypes.bet5
                    # bet4
                    # if t.allInCall == False and t.equity >= t.current_betbtn_value[2]["pot"] and \
                    #                 t.gameStage == GameStages.River.value and \
                    #                 float(t.totalPotValue) < t.bigBlind * float(
                    #             p.selected_strategy['betPotRiverEquityMaxBBM']) and \
                    #         (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                    #                 stage + '_betting_condidion_1'] == 0):
                    if t.current_betbtn_value[2]["pot"] > 0 and t.allInCall == False and self.finalBetLimit >= t.current_betbtn_value[2]["pot"] and \
                                (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                                    stage + '_betting_condidion_1'] == 0):
                        # self.logger.info("Bet4 condition met")
                        self.decision = DecisionTypes.bet3
                        self.invest = t.current_betbtn_value[1]["pot"]
                        # if float(self.invest) > float(t.myFunds*2/3):
                            # self.decision = DecisionTypes.bet5

                    if t.current_betbtn_value[2]["pot"] > 0 and t.allInCall == False and self.finalBetLimit >= t.current_betbtn_value[2]["pot"] * 2 and \
                                (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                                    stage + '_betting_condidion_1'] == 0):
                        # self.logger.info("Bet4 condition met")
                        self.decision = DecisionTypes.bet4
                        self.invest = t.current_betbtn_value[2]["pot"]
                        # if float(self.invest) > float(t.myFunds*2/3):
                            # self.decision = DecisionTypes.bet5
                    # if t.current_betbtn_value[2]["pot"] > 0 and t.allInCall == False and self.finalBetLimit >= t.bonatablemodel.initialFunds * 0.9 and \
                    #             (not t.checkButton or not t.other_player_has_initiative or p.selected_strategy[
                    #                 stage + '_betting_condidion_1'] == 0) and t.current_betbtn_value[2]["pot"] > float(t.myFunds/2):
                        # self.logger.info("Bet4 condition met")
                        # self.decision = DecisionTypes.bet5

    def bluff(self, t, p, h):
        t.currentBluff = 0

        # if t.isHeadsUp == True and h.round_number == 0:
        if h.round_number == 0:

            # flop
            if t.gameStage == GameStages.Flop.value and \
                                    float(p.selected_strategy['FlopBluffMaxEquity']) > t.equity > float(
                        p.selected_strategy['FlopBluffMinEquity']) and \
                            self.decision == DecisionTypes.check and \
                    (t.playersAhead == 0 or p.selected_strategy['flop_bluffing_condidion_1'] == 0):
                t.currentBluff = 1
                self.decision = DecisionTypes.bet_bluff
                # self.logger.debug("Bluffing activated")

            # turn
            elif t.gameStage == GameStages.Turn.value and \
                    not h.last_round_bluff and \
                    (not t.other_player_has_initiative or p.selected_strategy['turn_bluffing_condidion_2'] == 0) and \
                            self.decision == DecisionTypes.check and \
                                    float(p.selected_strategy['TurnBluffMaxEquity']) > t.equity > float(
                        p.selected_strategy['TurnBluffMinEquity']) and \
                    (t.playersAhead == 0 or p.selected_strategy['turn_bluffing_condidion_1'] == 0):
                t.currentBluff = 1
                self.decision = DecisionTypes.bet_bluff
                # self.logger.debug("Bluffing activated")

            # river
            elif t.gameStage == GameStages.River.value and \
                    not h.last_round_bluff and \
                    (not t.other_player_has_initiative or p.selected_strategy['river_bluffing_condidion_2'] == 0) and \
                            self.decision == DecisionTypes.check and \
                                    float(p.selected_strategy['RiverBluffMaxEquity']) > t.equity > float(
                        p.selected_strategy['RiverBluffMinEquity']) and \
                    (t.playersAhead == 0 or p.selected_strategy['river_bluffing_condidion_1'] == 0):
                t.currentBluff = 1
                self.decision = DecisionTypes.bet_bluff
                # self.logger.debug("Bluffing activated")

    def check_deception(self, t, p, h):
        # Flop
        if t.equity > float(
                p.selected_strategy['FlopCheckDeceptionMinEquity']) and t.gameStage == GameStages.Flop.value and (
                                self.decision == DecisionTypes.bet1 or self.decision == DecisionTypes.bet2 or self.decision == DecisionTypes.bet3 or self.decision == DecisionTypes.bet4):
            self.UseFlopCheckDeception = True
            self.decision = DecisionTypes.check_deception
            # self.logger.debug("Check deception activated")
        else:
            self.UseFlopCheckDeception = False

        # Turn
        if h.previous_decision == DecisionTypes.call.value and t.equity > float(
                p.selected_strategy['TurnCheckDeceptionMinEquity']) and t.gameStage == GameStages.Turn.value and (
                                self.decision == DecisionTypes.bet1 or self.decision == DecisionTypes.bet2 or self.decision == DecisionTypes.bet3 or self.decision == DecisionTypes.bet4):
            self.UseTurnCheckDeception = True
            self.decision = DecisionTypes.check_deception
            # self.logger.debug("Check deception activated")
        else:
            self.UseTurnCheckDeception = False

        # River
        if h.previous_decision == DecisionTypes.call.value and t.equity > float(
                p.selected_strategy['RiverCheckDeceptionMinEquity']) and t.gameStage == GameStages.River.value and (
                                self.decision == DecisionTypes.bet1 or self.decision == DecisionTypes.bet2 or self.decision == DecisionTypes.bet3 or self.decision == DecisionTypes.bet4):
            self.UseRiverCheckDeception = True
            self.decision = DecisionTypes.check_deception
            # self.logger.debug("Check deception activated")
        else:
            self.UseRiverCheckDeception = False

    def call_deception(self, t, p, h):
        pass

    def bully(self, t, p, h):
        if t.isHeadsUp:
            for i in range(t.sit_count):
                if t.other_players[i]['status'] == 1:
                    break
            opponentFunds = t.other_players[i]['funds']

            # if opponentFunds == '': opponentFunds = float(p.selected_strategy['initialFunds'])
            if opponentFunds == '': opponentFunds = float(t.bonatablemodel.initialFunds)

            self.bullyMode = opponentFunds > float(p.selected_strategy['bullyDivider'])

            if (t.equity >= float(p.selected_strategy['minBullyEquity'])) and (
                        t.equity <= float(p.selected_strategy['maxBullyEquity'])) and self.bullyMode:
                self.decision = DecisionTypes.bet_bluff
                # self.logger.info("Bullying activated")
                self.bullyDecision = True
            else:
                self.bullyDecision = False

    def admin(self, t, p, h):
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 2 and self.decision == DecisionTypes.bet1: self.decision = DecisionTypes.bet2
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 3 and self.decision == DecisionTypes.bet1: self.decision = DecisionTypes.bet3
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 3 and self.decision == DecisionTypes.bet2: self.decision = DecisionTypes.bet3
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 4 and self.decision == DecisionTypes.bet1: self.decision = DecisionTypes.bet4
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 4 and self.decision == DecisionTypes.bet2: self.decision = DecisionTypes.bet4
        if int(p.selected_strategy[
                   'minimum_bet_size']) == 4 and self.decision == DecisionTypes.bet3: self.decision = DecisionTypes.bet4
        
        # bet setting by bet button enables

        if t.potbetbutton == 2 and self.decision == DecisionTypes.bet4: self.decision = DecisionTypes.bet3
        elif t.potbetbutton == 1 and self.decision == DecisionTypes.bet4: self.decision = DecisionTypes.bet2
        elif t.potbetbutton == 1 and self.decision == DecisionTypes.bet3: self.decision = DecisionTypes.bet2
        elif t.potbetbutton == 0 and self.decision == DecisionTypes.bet4: self.decision = DecisionTypes.bet1
        elif t.potbetbutton == 0 and self.decision == DecisionTypes.bet3: self.decision = DecisionTypes.bet1
        elif t.potbetbutton == 0 and self.decision == DecisionTypes.bet2: self.decision = DecisionTypes.bet1
        

        if t.checkButton == False and t.minCall == 0.0 and p.selected_strategy['use_pot_multiples'] == 0:
            self.ErrCallButton = True
            # self.logger.error("Call button or pot multiple had no value")
        else:
            self.ErrCallButton = False

        if t.checkButton == True:
            if self.decision == DecisionTypes.fold: self.decision = DecisionTypes.check
            if self.decision == DecisionTypes.call: self.decision = DecisionTypes.check
            if self.decision == DecisionTypes.call_deception: self.decision = DecisionTypes.check_deception
        # allincall case ? 
        if t.allInCall and self.decision != DecisionTypes.fold:
            self.decision = DecisionTypes.call

        h.lastSecondRoundAdjustment = self.secondRoundAdjustment

        if self.decision == DecisionTypes.check or self.decision == DecisionTypes.check_deception: h.myLastBet = 0
        if self.decision == DecisionTypes.call or self.decision == DecisionTypes.check_deception:  h.myLastBet = t.minCall

        # if t.gameStage == GameStages.PreFlop.value:
        h.myLastBet = self.invest

        # if self.decision == DecisionTypes.bet1: h.myLastBet = t.minBet
        # if self.decision == DecisionTypes.bet2: h.myLastBet = t.minBet * float(
        #     p.selected_strategy['BetPlusInc']) + t.minBet
        
        # if self.decision == DecisionTypes.bet2: h.myLastBet = self.invest
        # if self.decision == DecisionTypes.bet_bluff: h.myLastBet = t.totalPotValue
        # if self.decision == DecisionTypes.bet3: h.myLastBet = t.totalPotValue / 2
        # if self.decision == DecisionTypes.bet4: h.myLastBet = t.totalPotValue
    def allin_decision(self, t, p, h):
        # if self.invest > t.myFunds / 2 and (t.myFunds - self.invest) < 5 * t.bigBlind:
            # self.decision = DecisionTypes.bet5
        if t.bonatablemodel.type.value =='TOUNAMENT1' or t.bonatablemodel.type.value =='TOUNAMENT2' or t.bonatablemodel.type.value =='NORMALROOM':
            # if t.myFunds < self.invest + self.invest/2 + t.bonatablemodel.bigBlind and not t.allInCall:
                # self.decision = DecisionTypes.bet5
                # print(" your funds is small more than call and bet value half so ALLIN ! ")
            if t.myFunds < self.invest + self.invest/2 + t.bonatablemodel.bigBlind and t.allInCall:
                self.decision = DecisionTypes.call
                print(" your funds is small more than call and bet value half so ALLINCALL ! ")
    def calc_out_call(self, t, p, h): 
        if self.decision == DecisionTypes.fold and t.bonatablemodel.type.value =='NORMALROOM' or t.bonatablemodel.type.value == 'TBT':
            if self.outs > 7 and t.gameStage == "Flop" and t.minCall < t.myFunds / 3:
                self.decision = DecisionTypes.call
                self.invest = t.minCall
            # elif self.outs > 8 and t.gameStage == "Flop" :
                # self.decision = DecisionTypes.bet5
                # self.invest = t.myFunds
            elif self.outs > 8 and t.gameStage == "Turn" and t.minCall < t.myFunds / 3:
                self.decision = DecisionTypes.call
                self.invest = t.minCall
    def collusion_bluff_fold(self, t, p, h):
        if t.bonatablemodel.get_No_users() and self.collusion_bluff_fold_mode:
            if t.bonatablemodel.get_minimum_whnd() == t.table_model_data['whnd'] and not t.allInCall:
                self.decision = DecisionTypes.bet_bluff
            elif t.checkButton:
                self.decision = DecisionTypes.check
            else:
                self.decision = DecisionTypes.fold
            print('Now Bots are playing themself so bluff and fold in collusion')
        elif not t.bonatablemodel.get_No_users():
            # playsound('sounds/alarm1.mp3')
            print("playing with a user now.")

        

       
    def make_decision(self, t, h, p, logger, l):
        self.preflop_sheet_name = ''
        if t.equity >= float(p.selected_strategy['alwaysCallEquity']):
            # self.logger.info("Equity is above the always call threshold")
            self.finalCallLimit = 99999999

        if t.myFunds * int(p.selected_strategy['always_call_low_stack_multiplier']) < t.totalPotValue:
            # self.logger.info("Low funds call everything activated")
            self.finalCallLimit = 99999999

        if t.gameStage == GameStages.PreFlop.value:
            self.preflop_table_analyser(t, logger, h, p)

        if not(p.selected_strategy['preflop_override'] and t.gameStage == GameStages.PreFlop.value):
            # self.logger.info('Make preflop decision based on non-preflop table')
            self.calling(t, p, h)
            self.betting(t, p, h)
            if t.checkButton:
                self.check_deception(t, p, h)

            if t.allInCall == False and t.equity >= float(p.selected_strategy['secondRiverBetPotMinEquity']) and t.gameStage == GameStages.River.value and h.histGameStage == GameStages.River.value:
                self.decision = DecisionTypes.bet4

                # self.bully(t,p,h,logger)
        # else:
            # self.logger.info('Preflop table not used for this decision')

        self.admin(t, p, h)
        self.bluff(t, p, h)
        self.calc_out_call(t, p, h)
        self.allin_decision(t, p, h)
        self.collusion_bluff_fold(t, p, h)
        self.decision = self.decision.value
