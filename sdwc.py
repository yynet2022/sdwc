# -*- coding:utf-8 -*-
import sys
import time
from datetime import datetime
import threading
import json
import traceback
# from pprint import pprint
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import tkinter.simpledialog as tkSimpleDialog
import tkinter.messagebox as tkMessageBox
import pystray
from PIL import Image

CONFIGFILE = 'sdwc.in'
SSSCALE = 1.01

config = {
    'DATE_FONT': ('Gothic', 24),
    'TIME_FONT': ('Gothic', 42),
    'FOREGROUND': '#000000',
    'BACKGROUND': '#ffffff',
    'TRANSPARENTCOLOR': '#fff0f0',
    'TOPMOST': True,
    'OVERRIDEREDIRECT': True,
    'DEBUG': False
}


def save_config():
    try:
        with open(CONFIGFILE, 'w') as fd:
            json.dump(config, fd, indent=2)
    except Exception as e:
        tkMessageBox.showerror('Error message: save config', str(e))


def load_config():
    global config
    try:
        with open(CONFIGFILE, 'r') as fd:
            config = json.load(fd)
    except FileNotFoundError:
        pass


class wFontDialog(tkSimpleDialog.Dialog):
    def __init__(self, parent, title=None,
                 sample_string='Sample', init_font=('Helvetica', 42),
                 tag='_TAG'):
        self.__sample_string = sample_string
        self.__init_font = init_font
        self.__tag = tag
        super().__init__(parent, title)

    def body(self, bdfrw):
        ss = self.__sample_string

        fontnames = list(tkFont.families())
        fontnames.sort()

        tk.Label(bdfrw, text='Families:').pack(anchor='sw')

        v = tk.StringVar(value=fontnames)
        lw = tk.Listbox(bdfrw, listvariable=v)
        lw.pack(fill=tk.X, padx=10)
        lw.bind('<<ListboxSelect>>', self.__selected)
        lw.bind('<<ListboxSelect>>', self.__selected)
        lw.bind('<FocusIn>', self.__focusin)

        tk.Label(bdfrw, text='Size:').pack(anchor='sw', pady=(5, 0))

        s = tk.Spinbox(bdfrw, from_=1, to=255, command=self.__numbered)
        s.pack(fill=tk.X, padx=10)

        fn = tkFont.Font(self, self.__init_font)
        wf = int(fn.measure(ss) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)

        c = tk.Canvas(bdfrw, bg=config['BACKGROUND'], width=wf, height=hf)
        c.pack(fill=tk.X, padx=20, pady=20)
        c.create_text(0, 0, anchor='nw', text=ss,
                      tags=self.__tag, font=fn, fill=config['FOREGROUND'])

        n0 = c.itemcget(self.__tag, 'font')
        fn = tkFont.Font(font=n0)
        n1 = fn.cget('family')
        if n1 in fontnames:
            i = fontnames.index(n1)
            lw.see(i)
            lw.select_set(i)
            lw.activate(i)

        self.__l = lw
        self.__c = c
        self.__s = tk.IntVar(value=fn.cget('size'))
        s['textvariable'] = self.__s

        return lw

    def __numbered(self):
        v = self.__s.get()
        c = self.__c
        n0 = c.itemcget(self.__tag, 'font')
        fn0 = tkFont.Font(font=n0)

        fn = tkFont.Font(self, (fn0.cget('family'), v))
        wf = int(fn.measure(self.__sample_string) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)
        c.config(width=wf, height=hf)
        c.itemconfig(self.__tag, font=fn)

    def __focusin(self, e):
        lw = self.__l
        i = lw.index(tk.ACTIVE)
        if not lw.curselection() and i >= 0:
            lw.see(i)
            lw.select_set(i)

    def __selected(self, e):
        lw = self.__l
        i = lw.curselection()
        if not i:
            return
        n = lw.get(i[0])

        c = self.__c
        n0 = c.itemcget(self.__tag, 'font')
        fn0 = tkFont.Font(font=n0)

        fn = tkFont.Font(self, (n, fn0.cget('size')))
        wf = int(fn.measure(self.__sample_string) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)
        c.config(width=wf, height=hf)
        c.itemconfig(self.__tag, font=fn)
        lw.focus_set()

    def validate(self):
        lw = self.__l
        i = lw.index(tk.ACTIVE)
        if i < 0:
            return 0
        n = lw.get(i)

        c = self.__c
        n0 = c.itemcget(self.__tag, 'font')
        fn0 = tkFont.Font(font=n0)

        self.result = (n, fn0.cget('size'))
        return 1


class toggleButton(ttk.OptionMenu):
    def __init__(self, parent, init_value, callback, **ka):
        values = ('OFF', 'ON')
        val = values[int(init_value)]
        var = tk.StringVar()

        def selected(v):
            callback(bool(values.index(v)))

        super().__init__(parent, var, val, *values, command=selected)
        self.config(**ka)


class wMenu(tkSimpleDialog.Dialog):
    def __init__(self, parent, title=None):
        super().__init__(parent, title)

    def body(self, bfrm):
        w = -12

        r = 0
        lb = tk.Label(bfrm, text='Override-Redirect:')
        lb.grid(row=r, column=0)

        b = toggleButton(bfrm, config['OVERRIDEREDIRECT'],
                         self.__selected_overrideredirect, width=w)
        b.grid(row=r, column=1, padx=5, pady=5)

        r += 1
        lb = tk.Label(bfrm, text='Top-Most:')
        lb.grid(row=r, column=0, sticky=tk.W)

        b = toggleButton(bfrm, config['TOPMOST'],
                         self.__selected_topmost, width=w)
        b.grid(row=r, column=1, padx=5, pady=5)

        r += 1
        tk.Label(bfrm, text='Date:').grid(row=r, column=0, sticky=tk.W)

        b = tk.Button(bfrm, text='Font', width=w)
        b.grid(row=r, column=1, padx=5, pady=5)
        b['command'] = self.__setFont_date
        b.bind('<Return>', self.__setFont_date)
        ret = b

        b = tk.Button(bfrm, text='Color', width=w, state=tk.DISABLED)
        b.grid(row=r, column=2, padx=5, pady=5)

        r += 1
        tk.Label(bfrm, text='Time').grid(row=r, column=0, sticky=tk.W)

        b = tk.Button(bfrm, text='Font', width=w)
        b.grid(row=r, column=1, padx=5, pady=5)
        b['command'] = self.__setFont_time
        b.bind('<Return>', self.__setFont_time)

        b = tk.Button(bfrm, text='Color', width=w, state=tk.DISABLED)
        b.grid(row=r, column=2, padx=5, pady=5)

        return ret

    def buttonbox(self):
        box = tk.Frame(self)

        w = tk.Button(box, text="Close", width=10, command=self.cancel,
                      default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w.bind('<Return>', self.cancel)

        self.bind('<Escape>', self.cancel)
        box.pack()

    def __selected_topmost(self, v):
        config['TOPMOST'] = v
        self.parent.master.attributes('-topmost', config['TOPMOST'])
        save_config()
        self.focus_force()

    def __selected_overrideredirect(self, v):
        config['OVERRIDEREDIRECT'] = v
        self.parent.master.overrideredirect(config['OVERRIDEREDIRECT'])
        save_config()
        self.focus_force()

    def __setFont_date(self, event=None):
        c = self.parent.getCanvasDate()
        ss = c.itemcget('cdate', 'text')
        n0 = c.itemcget('cdate', 'font')
        f0 = tkFont.Font(font=n0)
        font = (f0.cget('family'), f0.cget('size'))
        f = wFontDialog(
                self, title='Font of date',
                sample_string=ss,
                init_font=font,
                tag='_date_tag')
        if f.result:
            self.parent.setDateFont(f.result)
            config['DATE_FONT'] = f.result
            save_config()

    def __setFont_time(self, event=None):
        c = self.parent.getCanvasTime()
        ss = c.itemcget('ctime', 'text')
        n0 = c.itemcget('ctime', 'font')
        f0 = tkFont.Font(font=n0)
        font = (f0.cget('family'), f0.cget('size'))
        f = wFontDialog(
                self, title='Font of time',
                sample_string=ss,
                init_font=font,
                tag='_time')
        if f.result:
            self.parent.setTimeFont(f.result)
            config['TIME_FONT'] = f.result
            save_config()


class SimpleDigitalWallClock(tk.Frame):
    def __init__(self, root, config):
        super().__init__(root)
        TP_COLOR = config['TRANSPARENTCOLOR']
        self.config(bg=TP_COLOR, relief=tk.FLAT, bd=0)

        n = datetime.now()
        ss = '{0:0>4d}/{1:0>2d}/{2:0>2d}'.format(n.year, n.month, n.day)
        fn = tkFont.Font(self.master, config['DATE_FONT'])
        wf = int(fn.measure(ss) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)

        c = tk.Canvas(self, width=wf, height=hf, bg=TP_COLOR)
        if config['DEBUG']:
            c.config(relief=tk.SOLID, bd=2)
        else:
            c.config(relief=tk.FLAT, bd=0, highlightthickness=0)
        c.pack(fill=tk.NONE, anchor=tk.E)
        c.create_text(0, 0, anchor='nw', text='D',
                      font=fn, tags='cdate', fill=config['FOREGROUND'])
        self.__cdate = c

        ss = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(n.hour, n.minute, n.second)
        fn = tkFont.Font(self.master, config['TIME_FONT'])
        wf = int(fn.measure(ss) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)

        c = tk.Canvas(self, width=wf, height=hf, bg=TP_COLOR)
        if config['DEBUG']:
            c.config(relief=tk.SOLID, bd=2)
        else:
            c.config(relief=tk.FLAT, bd=0, highlightthickness=0)
        c.pack(fill=tk.NONE, anchor=tk.E)
        c.create_text(0, 0, anchor='nw', text='T',
                      font=fn, tags='ctime', fill=config['FOREGROUND'])
        self.__ctime = c

        self.pack(padx=5, pady=5)
        self.updateGeometry()

    def run(self):
        self.__show_time()
        self.master.mainloop()

    def updateGeometry(self):
        __DEBUG = False
        m = self.master
        m.deiconify()
        m.update_idletasks()
        rw = m.winfo_screenwidth()
        if __DEBUG:
            print('wm screenwidth>', rw)
        # rh = m.winfo_screenheight()
        frmw = m.winfo_rootx() - m.winfo_x()
        if __DEBUG:
            print('wm rootx>', m.winfo_rootx())
            print('wm x>', m.winfo_x())
        # ttlh = m.winfo_rooty() - m.winfo_y()
        w0 = m.winfo_width()
        if __DEBUG:
            print('wm width>', m.winfo_width())
        # h0 = m.winfo_height()
        ww = w0 + frmw * 2
        # hh = h0 + ttlh + frmw
        # m.geometry('{}x{}+{}+{}'.format(w0, h0, rw-ww, 0))
        m.geometry('+{}+{}'.format(rw-ww, 0))
        if __DEBUG:
            print('geometry>', '+{}+{}'.format(rw-ww, 0))

    def getCanvasDate(self):
        return self.__cdate

    def setDateFont(self, font):
        cd = self.getCanvasDate()
        ss = cd.itemcget('cdate', 'text')
        fn = tkFont.Font(self, font)
        wf = int(fn.measure(ss) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)
        cd.config(width=wf, height=hf)
        cd.itemconfig('cdate', font=fn)
        self.updateGeometry()

    def getCanvasTime(self):
        return self.__ctime

    def setTimeFont(self, font):
        cd = self.getCanvasTime()
        ss = cd.itemcget('ctime', 'text')
        fn = tkFont.Font(self, font)
        wf = int(fn.measure(ss) * SSSCALE)
        hf = int(fn.metrics()['linespace'] * SSSCALE)
        cd.config(width=wf, height=hf)
        cd.itemconfig('ctime', font=fn)
        self.updateGeometry()

    def show_menu(self):
        wMenu(self)

    def __show_time(self):
        n = datetime.now()
        s = '{0:0>4d}/{1:0>2d}/{2:0>2d}'.format(n.year, n.month, n.day)
        self.__cdate.itemconfig('cdate', text=s)
        s = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(n.hour, n.minute, n.second)
        self.__ctime.itemconfig('ctime', text=s)

        t = time.time()
        tt = int((int(t)+1.05-t)*1000)
        self.master.after(tt, self.__show_time)
        # print(tt, n)


class winTray(threading.Thread):
    def __init__(self, app, **ka):
        self.__app = app

        def show_menu():
            app.master.after(0, app.show_menu)

        menu = (
            pystray.MenuItem('Menu', show_menu),
            pystray.MenuItem('Quit', self.quit0))
        image = Image.new("RGB", (32, 32), (2, 255, 255))
        n = 'Simple Digital Wall Clock'
        self.__icon = pystray.Icon(n, image, n, menu)
        super().__init__(**ka)

    def quit0(self):
        self.__icon.stop()

    def run(self):
        self.__icon.run()
        self.__app.master.after(0, self.__app.master.destroy)


def main():
    load_config()
    TP_COLOR = config['TRANSPARENTCOLOR']

    win = tk.Tk()
    win.config(bd=0, bg=TP_COLOR)

    if not config['DEBUG']:
        win.withdraw()
        # win.lower()
        win.wm_attributes('-transparentcolor', TP_COLOR)
        win.attributes('-topmost', config['TOPMOST'])
        win.overrideredirect(config['OVERRIDEREDIRECT'])

    app = SimpleDigitalWallClock(win, config)
    t = winTray(app)

    def show_error(self, *args):
        err = traceback.format_exception(*args)
        tkMessageBox.showerror('Exception', err)
        t.quit0()

    tk.Tk.report_callback_exception = show_error
    t.start()
    app.run()
    t.join()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        tkMessageBox.showerror('Error message', str(e))
        sys.exit(1)
