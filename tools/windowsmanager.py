import threading

# windows manager consts
Bonapoker_title_string1 = r'德州扑克'

class WindowsManager(threading.Thread):
    def __init__(self, gui_signals):
        threading.Thread.__init__(self)
        self.bona_bot_tread_list = {}
        self.old_window_handles = []
        self.gui_signals = gui_signals
        self.window_num = 0
    def run(self): 
        while True:
            try:
                bona_windows_list = gw.getWindowsWithTitle(Bonapoker_title_string1)

                # new_window_handles = []
                # for bona_window in sorted(bona_windows_list, key=lambda x: x.left):
                #     new_window_handles.append(bona_window._hWnd)
                # if set(new_window_handles) == set(self.old_window_handles):
                #     continue
                # display_width = win32api.GetSystemMetrics(0)
                
                if len(bona_windows_list) == 0:
                    t1 = ThreadManager(1, "Test_Thread1", 1, gui_signals, 0)
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
                        
                        bona_window.moveTo(display_left + bots_num * bona_windows_gap, 0) 
                        
                        current_whnd = bona_window._hWnd
                        # add thread
                        if current_whnd not in self.bona_bot_tread_list:
                            table_name_CN = re.split('- Holdem NL', bona_window.title)[0]
                            table_name_EN = re.sub(Bonapoker_title_string1, 'Bona Table', table_name_CN)
                            self.bona_bot_tread_list[current_whnd] = ThreadManager(bots_num, table_name_EN, bots_num, self.gui_signals, current_whnd)
                            self.bona_bot_tread_list[current_whnd].daemon = True
                            self.bona_bot_tread_list[current_whnd].start()
                            print('Start Process Window :  ' + table_name_EN)
                            # self.bona_bot_tread_list[current_whnd].join()
                        else:
                            self.old_window_handles.remove(current_whnd)
                            
                        bots_num += 1
                    self.window_num = bots_num
                # delete thread
                for closed_whnd in self.old_window_handles:
                    self.bona_bot_tread_list[closed_whnd].stop()
                    print('End Process Window : ' + self.bona_bot_tread_list[closed_whnd].name)
                    del self.bona_bot_tread_list[closed_whnd]

                # update old windows
                self.old_window_handles = list(self.bona_bot_tread_list.keys())
            except Exception as e:
                print(e)
            time.sleep(20)
            