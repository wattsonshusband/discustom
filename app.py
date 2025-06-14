import threading 
import os
import customtkinter as ctk
import tkinter as tk
import sv_ttk
import glob
import json
import requests
import pywinstyles, sys
import pystray
import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename=os.path.join(os.getenv('APPDATA'), "discustom", "discustom.log"), level=logging.INFO)
time_data = time.localtime()
logger.info(f"{time_data.tm_mday}/{time_data.tm_mon}/{time_data.tm_year} : {time_data.tm_hour}-{time_data.tm_min}:{time_data.tm_sec}")

from pypresence import Presence
from CTkMessagebox import CTkMessagebox
from customtkinter import CTkImage
from tkinter import ttk
from PIL import ImageTk, Image
from pystray import MenuItem as item

base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
icon_path = os.path.join(base_path, 'assets', 'icon.ico')

class fs:
 def __init__(self):
  logger.info("starting file system")

  self.appdata_file_path = os.path.join(os.getenv('APPDATA'), "discustom")
  self.data_file_path = os.path.join(os.getenv('APPDATA'), "discustom", "data")
  self.settings_file_path = os.path.join(self.data_file_path, 'settings.json')
  self.status_file_path = os.path.join(self.data_file_path, 'status.json')
  self.presence_file_path = os.path.join(self.data_file_path, 'presence.json')
  self.startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

  if not self.check_appdata():
   self.create_appdata_folder()

 def check_appdata(self):
  return os.path.exists(self.appdata_file_path)
 
 def create_appdata_folder(self):
  os.mkdir(self.appdata_file_path)
  os.mkdir(self.data_file_path)

 def remove_appdata_folder(self):
  os.rmdir(self.data_file_path)
  os.rmdir(self.appdata_file_path) # I don't if I will ever use it

 def save_presence(self, presence_data):
  with open(self.presence_file_path, 'w') as file:
   json.dump(presence_data, file, indent=1)

 def save_config(self, config_data):
  with open(self.settings_file_path, 'w') as file:
   json.dump(config_data, file, indent=1)

 def save_status(self, status_data):
  with open(self.status_file_path, 'w') as file:
   json.dump(status_data, file, indent=1)

 def load_presence(self):
  try:
   with open(self.presence_file_path, 'r') as file:
    return json.load(file)
  except FileNotFoundError:
   default_data = { "enabled": False, "data": { "state": "Using Discustom", "details": "made by @nero", "large_image": "https://i.redd.it/tioihi08gd5f1.jpeg", "large_image_text": ":D", "small_image": "https://i.redd.it/tioihi08gd5f1.jpeg", "small_image_text": ":(" }}
   with open(self.presence_file_path, 'x') as file:
    json.dump(default_data, file, indent=1)
   
   return default_data

 def load_config(self):
  try:
   with open(self.settings_file_path, 'r') as file:
    return json.load(file)
  except FileNotFoundError:
   default_data = { "client_token": "", "client_id": "", "time_cycle": 60, "on_start_up": False, "start_minimized": False }
   with open(self.settings_file_path, 'x') as file:
    json.dump(default_data, file, indent=1)
   
   return default_data

 def add_to_startup(self):
  file_path = os.getcwd() + '\\discustom.exe'
  shortcut_path = os.path.join(self.startup_path, 'discustom.lnk')

  try:
    import pythoncom
    from win32com.shell import shell, shellcon

    shell_link = pythoncom.CoCreateInstance(
      shell.CLSID_ShellLink, None,
      pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    shell_link.SetPath(file_path)
    shell_link.SetDescription('Start Discustom')
    shell_link.SetWorkingDirectory(os.path.dirname(file_path))
    persist_file = shell_link.QueryInterface(pythoncom.IID_IPersistFile)
    persist_file.Save(shortcut_path, 0)
    logger.info(f"Shortcut created at {shortcut_path}")
  except ImportError:
    logger.error("pywin32 is required to create shortcut. You can install it with 'pip install pywin32'")

 def remove_from_startup(self):
  logger.info(f"Startup path: {self.startup_path}")
  shortcut_path = os.path.join(self.startup_path, 'discustom.lnk')

  try:
    if os.path.exists(shortcut_path):
      os.remove(shortcut_path)
      print(f"Shortcut removed from {shortcut_path}")
    else:
      print("No startup shortcut found.")
  except Exception as e:
    print(f"Error removing shortcut: {e}")

 def check_startup(self):
  shortcut_path = os.path.join(self.startup_path, 'discustom.lnk')
  return os.path.exists(shortcut_path)

 def load_status(self):
  try:
   with open(self.status_file_path, 'r') as file:
    return json.load(file)
  except FileNotFoundError:
   with open(self.status_file_path, 'x') as file:
    json.dump({ "enabled": False, "statuses": [] }, file, indent=1)
   
   return { "enabled": False, "statuses": [] }

 def settings_path(self):
  return self.settings_file_path
 
 def presence_path(self):
  return self.presence_file_path
 
 def status_path(self):
  return self.status_file_path
   
FS = fs()

class App():
 def __init__(self):
  logger.info("starting gui")

  self.root = tk.Tk()
  self.root.geometry("600x320")
  self.root.title('Discustom v1.21 by @nero')
  self.root.resizable(False, False)

  self.presence_enabled = False
  self.status_enabled = False

  self.presence_manager = presence_manager()
  self.status_manager = status_manager()

  self.config_data = FS.load_config()
  self.status_data = FS.load_status()
  self.presence_data = FS.load_presence()

  self.root.iconbitmap(icon_path)

  self.root.protocol("WM_DELETE_WINDOW", self.minimise)
  if self.config_data['start_minimized'] == True:
   self.minimise()

  self.cur_status_msg = self.status_manager.cur_line

  self.tab_frame = ttk.Frame(self.root, width=100)
  self.tab_frame.pack(
   side='left',
   fill='y'
  )

  self.content_frame = ttk.Frame(self.root)
  self.content_frame.pack(
   side='right',
   fill='both',
   expand=True
  )

  self.icons = [
   { "image": ImageTk.PhotoImage(Image.open('./assets/home.png').resize((30, 30))), "label": "Home" },
   { "image": ImageTk.PhotoImage(Image.open('./assets/presence.png').resize((30, 30))), "label": "Presence" },
   { "image": ImageTk.PhotoImage(Image.open('./assets/status.png').resize((30, 30))), "label": "Status" },
   { "image": ImageTk.PhotoImage(Image.open('./assets/settings.png').resize((30, 30))), "label": "Settings" }
  ]

  self.remove_image = ctk.CTkImage(light_image=Image.open(os.path.join('assets', 'remove.png')), size=(10, 10))
  self.add_image = ctk.CTkImage(light_image=Image.open(os.path.join('assets', 'add.png')), size=(10, 10))
  self.save_image = ctk.CTkImage(light_image=Image.open(os.path.join('assets', 'save.png')), size=(10, 10))

  self.tabs = []
  for i, icon in enumerate(self.icons):
   appendable_btn = ttk.Button(self.tab_frame, image=icon['image'], text=icon['label'], compound='left', command=lambda i=i: self.show_tab(i), width=10)
   appendable_btn.pack(pady=15, anchor='w')

   ttk.Separator(self.tab_frame, orient='horizontal').pack(fill='x', padx=5, pady=(5, 5))
   self.tabs.append(appendable_btn)

  self.tab_contents = [
   self.main_page,
   self.presence_page,
   self.status_page,
   self.settings_page
  ]

  self.show_tab(0)

  sv_ttk.set_theme('dark', self.root)

  self.apply_theme_to_titlebar()

 def apply_theme_to_titlebar(self):
  version = sys.getwindowsversion()

  if version.major == 10 and version.build >= 22000:
   pywinstyles.change_header_color(self.root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
  elif version.major == 10:
   pywinstyles.apply_style(self.root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

   self.root.wm_attributes("-alpha", 0.99)
   self.root.wm_attributes("-alpha", 1)

 def find_icons(self):
  assets_path = os.path.join(os.getcwd(), 'assets')
  assets_path_files = glob.glob(assets_path + '/*.jpg')
  self.icon_paths = []
  for file in assets_path_files:
   self.icon_paths.append(file)

 def show_tab(self, index):
  for widget in self.content_frame.winfo_children():
    widget.pack_forget()

  self.tab_contents[index]()

 def bring_to_front(self):
  self.root.deiconify()
  self.root.lift()
  self.root.focus_force()

 def open_window(self):
  self.icon.stop()
  self.root.after(10, self.bring_to_front())

 def close(self):
  if self.icon:
    self.icon.stop()

  self.status_manager.stop_all_threads()
  self.presence_manager.stop_all_threads()

  logger.info('closing.')

  time.sleep(2)

  for thread in threading.enumerate():
   if thread.name != "MainThread":
    thread.join(timeout=1)

  self.root.destroy()

 def minimise(self):
  self.root.withdraw()
  self.image = Image.open(icon_path)
  self.menu = (item('Open', self.open_window), item('Exit', self.close))
  self.icon = pystray.Icon("discustom", self.image, "discustom", self.menu)
  self.icon.run()

 def main_page(self):
  main_frame = ctk.CTkScrollableFrame(self.content_frame, label_anchor='w', label_text='Home', width=450, height=300)
  main_frame.pack(padx=5, pady=3)

  ctk.CTkLabel(main_frame, text="You're actually stupid, James", font=('Verdana', 9)).pack(padx=5, pady=2, anchor='w')
  ctk.CTkLabel(main_frame, text="I was going todo more but I don't know what to put", font=('Verdana', 9)).pack(padx=5, pady=2, anchor='w')

 def presence_page(self):
  scroll_frame = ctk.CTkScrollableFrame(self.content_frame, label_anchor='w', label_text='Presence', width=450, height=300)
  scroll_frame.pack(padx=5, pady=3)

  # don't ask, i can't be bothered to change them all
  self.scroll_frame = scroll_frame

  self.pre_enabled_var = ctk.BooleanVar(self.root, value=self.presence_data['enabled'])
  self.pre_enabled = ctk.CTkCheckBox(scroll_frame, width=20, text="Enable Presence", variable=self.pre_enabled_var, command=self.toggle_presence, offvalue=False, onvalue=True)
  self.pre_enabled.pack(padx=5, pady=10, anchor='w')

  self.separator(scroll_frame)

  ctk.CTkLabel(scroll_frame, text="State", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.state_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['state'])
  self.state_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.state_var)
  self.state_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.state_entry, "The text just above the time amount.")

  ctk.CTkLabel(scroll_frame, text="Details", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.details_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['details'])
  self.details_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.details_var)
  self.details_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.details_entry, "The text just below the App name")

  ctk.CTkLabel(scroll_frame, text="Large Image", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.large_img_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['large_image'])
  self.large_img_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.large_img_var)
  self.large_img_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.large_img_entry, "Well, I mean it's kinda obvious")

  ctk.CTkLabel(scroll_frame, text="Large Image Text", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.large_img_text_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['large_image_text'])
  self.large_img_text_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.large_img_text_var)
  self.large_img_text_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.large_img_text_entry, "The text that shows when you hover over the image, kinda like this.")

  ctk.CTkLabel(scroll_frame, text="Small Image", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.small_img_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['small_image'])
  self.small_img_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.small_img_var)
  self.small_img_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.small_img_entry, "the url of the small image you want.")

  ctk.CTkLabel(scroll_frame, text="Small Image Text", font=('Verdana', 11)).pack(padx=5, pady=(5, 2), anchor='w')
  self.small_img_text_var = tk.StringVar(scroll_frame, value=self.presence_data['data']['small_image_text'])
  self.small_img_text_entry = ctk.CTkEntry(scroll_frame, width=400, textvariable=self.small_img_text_var)
  self.small_img_text_entry.pack(padx=5, pady=(2, 10), anchor='w')

  tooltip(self.small_img_text_entry, "The text that shows when you hover over the small image.")

  self.separator(scroll_frame)
  
  ctk.CTkButton(scroll_frame, width=200, image=self.save_image, compound='left', text="Save Presence", command=self.save_presence_data).pack(pady=(15, 15), anchor='center')

 def status_page(self):
  status_frame = ctk.CTkScrollableFrame(self.content_frame, label_anchor='w', label_text='Status', width=450, height=300)
  status_frame.pack(padx=5, pady=2)

  self.sta_enabled_var = ctk.BooleanVar(self.root, value=self.status_data['enabled'])
  self.sta_enabled = ctk.CTkCheckBox(status_frame, width=20, text="Enable Status", variable=self.sta_enabled_var, command=self.toggle_status, offvalue=False, onvalue=True)
  self.sta_enabled.pack(padx=5, pady=10, anchor='w')

  tooltip(self.sta_enabled, "Need I say less.")

  self.separator(status_frame)

  ctk.CTkLabel(status_frame, text="Status Message", font=('Verdana', 9)).pack(padx=5, pady=(5, 2), anchor='w')
  self.status_msg_var = tk.StringVar(status_frame)
  self.status_entry = ctk.CTkEntry(status_frame, width=400, textvariable=self.status_msg_var)
  self.status_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.status_entry, "the message that shows on the status")

  ctk.CTkLabel(status_frame, text="Emoji Name", font=('Verdana', 9)).pack(padx=5, pady=(5, 2), anchor='w')
  self.emoji_name_var = tk.StringVar(status_frame)
  self.emoji_name_entry = ctk.CTkEntry(status_frame, width=400, textvariable=self.emoji_name_var)
  self.emoji_name_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.emoji_name_entry, "the emoji name")

  ctk.CTkLabel(status_frame, text="Emoji ID", font=('Verdana', 9)).pack(padx=5, pady=(5, 2), anchor='w')
  self.emoji_id_var = tk.StringVar(status_frame)
  self.emoji_id_entry = ctk.CTkEntry(status_frame, width=400, textvariable=self.emoji_id_var)
  self.emoji_id_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.emoji_id_entry, "the id of the emoji")
  
  ctk.CTkButton(status_frame, width=200, image=self.add_image, compound='left', text="Add Status", command=self.pass_to_status_manager).pack(pady=(15, 15), anchor='center')

  self.separator(status_frame)

  self.remove_combo = ctk.CTkComboBox(status_frame, values=[status['msg'] for status in self.status_manager.status_lines['statuses']], width=450, state="readonly")
  self.remove_combo.pack(padx=5, pady=25, anchor='w')

  ctk.CTkButton(status_frame, width=200, image=self.remove_image, compound='left', text="Remove Status", command=self.remove_pass_to_status_manager).pack(pady=(15, 15), anchor='center')

 def settings_page(self):
  settings_frame = ctk.CTkScrollableFrame(self.content_frame, label_anchor='w', label_text='Settings', width=450, height=300)
  settings_frame.pack(padx=5, pady=2)

  ctk.CTkLabel(settings_frame, text="Client ID", font=('Verdana', 9)).pack(padx=5, pady=(5, 2), anchor='w')
  self.client_id_var = tk.StringVar(settings_frame, value=self.config_data['client_id'])
  self.client_id_entry = ctk.CTkEntry(settings_frame, width=400, textvariable=self.client_id_var)
  self.client_id_entry.pack(padx=5, pady=2, anchor='w')

  self.separator(settings_frame)

  ctk.CTkLabel(settings_frame, text="Token", font=('Verdana', 9)).pack(padx=5, pady=2, anchor='w')
  self.token_var = tk.StringVar(settings_frame, value=self.config_data['client_token'])
  self.token_entry = ctk.CTkEntry(settings_frame, width=400, textvariable=self.token_var, show="*")
  self.token_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.token_entry, 'Discord Token, this is locally stored and not consumed anywhere else.')

  ctk.CTkLabel(settings_frame, text="Time cycle", font=('Verdana', 9)).pack(padx=5, pady=2, anchor='w')
  self.time_cycle_var = tk.IntVar(settings_frame, value=self.config_data['time_cycle'])
  self.time_cycle_entry = ctk.CTkEntry(settings_frame, width=400, textvariable=self.time_cycle_var)
  self.time_cycle_entry.pack(padx=5, pady=2, anchor='w')

  tooltip(self.time_cycle_entry, 'Time for each status line.')

  self.separator(settings_frame)

  self.on_start_var = ctk.BooleanVar(settings_frame, value=self.config_data['on_startup'])
  self.on_minimized_var = ctk.BooleanVar(settings_frame, value=self.config_data['start_minimized'])

  self.on_start_box = ctk.CTkCheckBox(settings_frame, width=20, text="Run on Startup", variable=self.on_start_var, offvalue=False, onvalue=True)
  self.on_minimized = ctk.CTkCheckBox(settings_frame, width=20, text="Start Minimized", variable=self.on_minimized_var, offvalue=False, onvalue=True)

  self.on_start_box.pack(padx=5, pady=(8, 8), anchor='w')
  self.on_minimized.pack(padx=5, pady=(8, 8), anchor='w')

  ctk.CTkButton(settings_frame, width=200, image=self.save_image, compound='left', text="Save Settings", command=self.save_config_data).pack(pady=(15, 15), anchor='center')

 def separator(self, frame):
  ttk.Separator(frame, orient='horizontal').pack(fill='x', padx=5, pady=(5, 5))

 def pass_to_status_manager(self):
  self.status_manager.add_status(self.root, self.remove_combo, self.status_msg_var, self.emoji_id_var, self.emoji_name_var)

 def remove_pass_to_status_manager(self):
  self.status_manager.remove_status(self.root, self.remove_combo)

 def save_presence_data(self):
  state = self.state_var.get()
  details = self.details_var.get()
  large_image = self.large_img_var.get()
  large_text = self.large_img_text_var.get()
  small_image = self.small_img_var.get()
  small_text = self.small_img_text_var.get()

  if large_image == "" or large_text == "" or small_image == "" or small_text == "":
   CTkMessagebox(self.scroll_frame, message="You need to ensure image fields are filled.", icon='cancel')
   return
  
  if state == "" and details == "":
   CTkMessagebox(self.scroll_frame, message="You need to have either State or Details entry filled.", icon='cancel')
   return

  save_presence_data = {  
   "enabled": self.pre_enabled_var.get(),
   "data": {
    "state": state,
    "details": details,
    "large_image": large_image,
    "large_image_text": large_text,
    "small_image": small_image, 
    "small_image_text": small_text
   }
  }

  FS.save_presence(save_presence_data)

 def save_config_data(self):
  save_data = {
   "client_token": self.token_var.get(),
   "client_id": self.client_id_var.get(),
   "time_cycle": self.time_cycle_var.get(),
   "on_startup": self.on_start_var.get(),
   "start_minimized": self.on_minimized_var.get()
  }

  if self.on_start_var.get():
    if not FS.check_startup():
     FS.add_to_startup()
  else:
   if FS.check_startup():
    FS.remove_from_startup()

  FS.save_config(save_data)

 def toggle_status(self):
  self.status_data['enabled'] = self.sta_enabled_var.get()
  FS.save_status(self.status_data)

 def toggle_presence(self):
  self.presence_data['enabled'] = self.pre_enabled_var.get()
  FS.save_presence(self.presence_data)

class tooltip():
 def __init__(self, widget: any, text: str):
  self.widget = widget
  self.text = text
  self.tooltip_window = None

  self.widget.bind('<Enter>', self.show_tooltip)
  self.widget.bind('<Leave>', self.hide_tooltip)

 def show_tooltip(self, event=None):
  if self.tooltip_window or not self.text:
   return
  
  x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
  x += self.widget.winfo_rootx() + 25
  y += self.widget.winfo_rooty() + 20

  self.tooltip_window = tw = tk.Toplevel(self.widget)
  tw.wm_overrideredirect(True)
  tw.wm_geometry(f"+{x}+{y}")
  tw.attributes("-alpha", 0.7)

  label = ctk.CTkLabel(
   tw,
   text=self.text,
   corner_radius=20,
   bg_color="black",
   font=("Segoe UI", 12)
  )
  label.pack(ipadx=5, ipady=2)

 def hide_tooltip(self, event=None):
  if self.tooltip_window:
   self.tooltip_window.destroy()
   self.tooltip_window = None

class presence_manager:
 def __init__(self):
  logger.info('starting presence manager')
  self.config_data = FS.load_config()
  self.presence_data = FS.load_presence()
  self.settings_file = FS.settings_file_path
  self.presence = None

  self.check_client_id_stop_event = threading.Event()
  self.update_presence_stop_event = threading.Event()
  self.connect_presence_event = threading.Event()
  
  self.check_client_id_thread = threading.Thread(target=self.check_client_id, name='check_client_id', daemon=True)
  self.check_client_id_thread.start()

 def stop_all_threads(self):
  # stop all threads
  if hasattr(self, 'check_client_id_stop_event'):
    self.check_client_id_stop_event.set()
  if hasattr(self, 'update_presence_stop_event'):
    self.update_presence_stop_event.set()
  if hasattr(self, 'connect_presence_event'):
    self.connect_presence_event.set()
  if self.presence != None:
    self.presence.close()

 def difference(self):
  if hasattr(self, 'old_presence_data'):
    new_presence_data = FS.load_presence()
    if new_presence_data == self.old_presence_data and new_presence_data['data'] == self.old_presence_data['data']:
     return False
    else: 
     self.old_presence_data = new_presence_data
     return True
  else:
   self.old_presence_data = FS.load_presence()
   return True

 def update_presence(self):
  while not self.update_presence_stop_event.is_set():
   is_difference = self.difference()
   if not self.old_presence_data['enabled']:
    logger.info('presence closed.')
    self.presence.close()
    self.presence = None
    self.connect_presence_event.clear()
    self.update_presence_stop_event.set()
    self.check_client_id_stop_event.clear()
    self.check_client_id_thread = None
    self.check_client_id_thread = threading.Thread(target=self.check_client_id, name="check_client_id", daemon=True)
    self.check_client_id_thread.start()
    break

   if is_difference:
    logger.info("presence updated")
    presence_data = {
      "large_image": self.old_presence_data['data']['large_image'],
      "large_text": self.old_presence_data['data']['large_image_text'],
      "small_image": self.old_presence_data['data']['small_image'],
      "small_text": self.old_presence_data['data']['small_image_text'],
    }

    if self.old_presence_data['data']['state'] != "":
      presence_data['state'] = self.old_presence_data['data']['state']

    if self.old_presence_data['data']['details'] != "":
      presence_data['details'] = self.old_presence_data['data']['details']

    self.presence.update(**presence_data)

   self.update_presence_stop_event.wait(15)

 def connect(self):
  self.check_client_id_stop_event.set()
  self.config_data = FS.load_config()
  if hasattr(self, "presence") and self.presence == None:
   try:
    self.presence = Presence(self.config_data['client_id'])
   except:
    logger.error("failed presence init")

  attempt_amount = 0
  while not self.connect_presence_event.is_set():
   self.check_presence()
   if not self.presence_data['enabled']:
    self.connect_presence_event.set()
    self.update_presence_stop_event.set()
    self.check_client_id_stop_event.clear()
    self.check_client_id_thread = None
    self.check_client_id_thread = threading.Thread(target=self.check_client_id, name="check_client_id", daemon=True)
    self.check_client_id_thread.start()
    break
  
   self.update_presence_stop_event.clear()
   try:
    self.presence.connect()
    logger.info("connection established")
    self.update_presence_thread = threading.Thread(target=self.update_presence, name="update_presence_thread", daemon=True)
    self.update_presence_thread.start()
    self.connect_presence_event.set()
    continue
   except:
    if attempt_amount == 4:
     logger.error("failed connection, 4 attempts have been made and failed. Closing.")
     self.connect_presence_event.set()
     break

    logger.error(f"failed connection, retrying in 5 seconds. attempt: {attempt_amount}")
    attempt_amount += 1

   self.connect_presence_event.wait(5)

 def start_presence(self):
  if hasattr(self, 'update_presence_thread'):
   if self.update_presence_thread != None and self.update_presence_thread.is_alive():
    logger.info("thread already alive.")
    return
   
  logger.info("attempting connection...")
  try:
   self.connect()
  except:
   logger.error("connection failed...")
   self.check_client_id_stop_event.set()
   return

 def check_presence(self):
  self.presence_data = FS.load_presence()

 def check_client_id(self):
  self.check_presence()
  while not self.check_client_id_stop_event.is_set():
   try:
    if not self.presence_data['enabled']:
      self.check_client_id_stop_event.wait(10)
      self.check_presence()
      continue

    with open(self.settings_file, 'r') as configFile: 
     self.data = json.load(configFile)
     if self.data['client_id'] is not None and self.data['client_id'] != "":
       self.start_presence()
   except FileNotFoundError:
    FS.load_config()
    
   self.check_client_id_stop_event.wait(5)

class status_manager:
 def __init__(self):
  logger.info('starting status manager')

  self.check_token_stop_event = threading.Event()
  self.update_status_stop_event = threading.Event()

  self.settings_file = FS.settings_path()
  self.status_file = FS.status_path()
  self.headers = { "authorization": "" }

  self.status_lines = FS.load_status()
  self.cur_line = ""

  self.check_token_proc = threading.Thread(target=self.check_token, name="check_token", daemon=True)
  self.check_token_proc.start()

 def stop_all_threads(self):
  if hasattr(self, 'check_token_stop_event'):
    self.check_token_stop_event.set()
  if hasattr(self, 'update_status_stop_event'):
    self.update_status_stop_event.set()

 def is_enabled(self):
  return FS.load_status()['enabled']

 def update_status(self):
  while not self.update_status_stop_event.is_set():
    self.check_status()
    if not self.status_lines['enabled']:
      print('status has been disabled. returning back to check_token')
      self.check_token_stop_event.clear()
      self.check_token_proc = None
      self.check_token_proc = threading.Thread(target=self.check_token, name="check_token", daemon=True)
      self.check_token_proc.start()
      self.update_status_stop_event.set()
      continue
    
    if self.status_lines['statuses'] == []:
      self.update_status_stop_event.wait(self.data['time_cycle'])
      continue

    for statusLine in self.status_lines['statuses']:
      if not self.is_enabled():
       break

      if self.update_status_stop_event.is_set():
        break

      jsonData = {
        "custom_status": { "text": statusLine['msg'] }
      }

      if statusLine['emoji_name'] != "" and statusLine['emoji_id'] != "":
        jsonData['custom_status'].update({ "emoji_name": statusLine['emoji_name'], "emoji_id": statusLine['emoji_id'] })

      self.cur_line = statusLine['msg']

      try:
        resp = requests.patch('https://discord.com/api/v10/users/@me/settings', headers=self.headers, json=jsonData)
        if resp.status_code == 401:
          return
      except Exception as e:
        logger.error(f"Error updating status: {e}")
        continue

      self.update_status_stop_event.wait(self.data['time_cycle'])

 def start_update_status(self):
  self.update_status_stop_event.clear()

  if "update_status" in threading.enumerate():
   if self.update_status_proc and self.update_status_proc.is_alive():
    return

  if not self.token:
   return

  self.update_status_proc = threading.Thread(target=self.update_status, name="update_status", daemon=True)
  self.update_status_proc.start()

  self.check_token_stop_event.set()

 def remove_status(self, root, widget):
  option = widget.get()
  if not option:
   CTkMessagebox(title="Error", message="Please select a status line to remove.", icon="cancel")
   return
  
  for status in self.status_lines['statuses']:
   if status['msg'] == option:
    self.status_lines['statuses'].remove(status)
    with open(self.status_file, 'w') as status_file:
     json.dump(self.status_lines, status_file, indent=1)
    
    CTkMessagebox(title="Success", message="Status line removed successfully.", icon="check")

  self.check_status()
  root.after(0, lambda: widget.configure(values=[status['msg'] for status in self.status_lines['statuses']]))
  widget.set('')

 def add_status(self, root, widget, msg, emojiID, emojiName):
  if not msg.get():
    CTkMessagebox(title="Error", message="Please fill the message field.", icon="cancel")
    return
  
  if (emojiName.get() == "" and emojiID.get() != "") or (emojiName.get() != "" and emojiID.get() == ""):
    CTkMessagebox(title="Error", message="Please fill both emoji fields or leave both empty.", icon="cancel")
    return
  
  new_status = {
   "msg": msg.get(),
   "emoji_id": emojiID.get(),
   "emoji_name": emojiName.get()
  }

  self.status_lines['statuses'].append(new_status)
  with open(self.status_file, 'w') as status_file:
   json.dump(self.status_lines, status_file, indent=1)

  CTkMessagebox(title="Success", message="Status line added successfully.", icon="check")

  self.check_status()
  root.after(0, lambda: widget.configure(values=[status['msg'] for status in self.status_lines['statuses']]))

 def check_token(self):
  foundToken = False
  
  while not foundToken and not self.check_token_stop_event.is_set():
   try:
    if not self.status_lines['enabled']:
      self.check_token_stop_event.wait(10)
      self.check_status()
      continue

    with open(self.settings_file, 'r') as configFile: 
     self.data = json.load(configFile)
     if self.data['client_token'] is not None and self.data['client_token'] != "":
       foundToken = True
       self.token = self.data['client_token']
       self.headers["authorization"] = self.token
       self.start_update_status()
   except FileNotFoundError:
    FS.load_config()
    
   self.check_token_stop_event.wait(5)

 def check_status(self):
  self.status_lines = json.load(open(self.status_file, 'r'))

if __name__ == "__main__":
 app = App()
 try:
  app.root.mainloop()
 except KeyboardInterrupt:
  app.root.destroy()
 except Exception as e:
  logger.error(e)
  app.root.destroy()
