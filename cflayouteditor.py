# dependancies
import mechanize
from bs4 import BeautifulSoup

# standard library
import webbrowser
from base64 import b64encode
import re
import urllib2

try:
    from Tkinter import *
    from ttk import *
except ImportError:
    # python 3.1?
    from tkinter import *
    from tkinter.ttk import *
    # test this on 3.1, I don't have it
    
import tkFileDialog
from tkFileDialog import askopenfile, asksaveasfile

version = '0.3'

class Main(object):
    def __init__(self, master):
        self.master = master
        
        self.br = mechanize.Browser()
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        
        # construct menus
        self.menubar = Menu(root)
        self.filemenu = Menu(self.menubar, tearoff=0, activebackground="darkgreen", activeforeground="white")
        self.filemenu.add_command(label="New", command=self.new)
        self.opensubmenu = Menu(self.filemenu, tearoff=0, activebackground="darkgreen", activeforeground="white")
        self.opensubmenu.add_command(label="Load from computer", command=self.load)
        self.opensubmenu.add_command(label="Download from CF", command=self.download)
        self.filemenu.add_cascade(label="Load layout", menu=self.opensubmenu)

        self.exportsubmenu = Menu(self.filemenu, tearoff=0, activebackground="darkgreen", activeforeground="white")
        self.exportsubmenu.add_command(label="Upload to CF", command=self.upload)
        self.exportsubmenu.add_command(label="Save to PC", command=self.save)
        self.filemenu.add_cascade(label="Export", menu=self.exportsubmenu)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Logout from CF", command=self.logout)
        self.filemenu.add_command(label="Quit", command=root.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.insertmenu = Menu(self.menubar, tearoff=0, activebackground="darkgreen", activeforeground="white")
        self.insertmenu.add_command(label="CSS", command=lambda : self.insert('css'))
        self.insertmenu.add_command(label="Content", command=lambda : self.insert('content'))
        self.insertmenu.add_command(label="CF JS", command=lambda : self.insert('cfjs'))
        self.menubar.add_cascade(label="Insert", menu=self.insertmenu)
        
        master.config(menu=self.menubar) # add the menubar to the window

        self.nb = Notebook(master)
        self.nb.enable_traversal()
        self.nb.pack(fill='both', expand='yes', padx=10, pady=10)
        self.nb.bind('<<NotebookTabChanged>>', self.tabSwitch)
        
        self.frames = {}
        self.textboxes = {}
        for i in ['Overall', 'Blog', 'Comic', 'Archive', 'Overview', 'Errors', 'Search', 'CSS']:
            ii = i.lower()
            self.frames[ii] = Frame()
            self.nb.add(self.frames[ii], text=i)
            if i == "CSS":
                self.textboxes[ii] = self.Textbox(self.frames[ii], "CSS")
            else:
                self.textboxes[ii] = self.Textbox(self.frames[ii])
            self.textboxes[ii].frame.pack(fill='both', expand=True)
    def tabSwitch(self, event):
        tabname = self.nb.tab(self.nb.select(), "text")
        if tabname.lower() in self.textboxes:
            tb = self.textboxes[tabname.lower()]
            tb.text.focus_set()
    def new(self):
        for i in self.textboxes:
            i.delete('1.0', END)
    def load(self):
        f = askopenfile(filetypes=[("CF layout files", "*.cfl.xml")], mode='rU')
        if f:
            self.openLayoutFile(f.read())
            f.close()
    def openLayoutFile(self, string):
        soup = BeautifulSoup(string)
        # check valid file
        # later though
        # yup
        pairs = {'overall':'overall',
                 'blog':'overview',
                 'comic':'comic',
                 'archive':'archive',
                 'blogarchive':'blog',
                 'error':'errors',
                 'search':'search',
                 'layoutcss':'css'}
        for i in pairs:
            self.textboxes[pairs[i]].text.delete('1.0', END)
            contents = soup.find(i).string # recheck
            if contents:
                self.textboxes[pairs[i]].text.insert(END, contents.decode('base64'))
                self.textboxes[pairs[i]].text.updatetags(None)
    def download(self):
        self.selectComicAndRun(self.doDownload, self.download)
    def selectComicAndRun(self, function, caller):
        self.br.open('http://comicfury.com/comic.php?action=yourcomics')
        r = self.br.response().read()
        if 'You are not logged in' in r and '<div class="ehead">' in r:
            self.cf_login(caller=caller)
            return False
        else:
            s = BeautifulSoup(r)
            comicnames = [i.a.string for i in s('h3')]
            comicurls = [re.search('\d+$', i['href']).group() for i in s('a') if i['href'].startswith('managecomic.php') and
                         i.string == 'Manage']
            comics = dict(zip(comicnames, comicurls))
            topwindow = Toplevel(self.master, width=300, height=300)
            topwindow.title("Comic Select")
            topwindow.pack_propagate(False)
            top = Frame(topwindow)
            top.pack(fill=BOTH, expand=True, padx=5, pady=5)
            if comics:
                instruction = Label(top, text='Select a comic.')
                instruction.grid(columnspan=2)
                top.columnconfigure(0, weight=1) # expand!
                top.rowconfigure(1, weight=1)
                listbox = Listbox(top, selectmode=SINGLE)
                listbox.grid(row=1, column=0, sticky=N+E+W+S)
                for i in comicnames:
                    listbox.insert(END, i)
                scrollbar = Scrollbar(top, orient=VERTICAL)
                scrollbar.config(command=listbox.yview)
                listbox.config(yscrollcommand=scrollbar.set)
                scrollbar.grid(row=1, column=1, sticky=N+S)
                b = Button(top, text="I'm cool with this, yo", command=lambda t=topwindow, m=listbox, c=comics: function(m,t,c))
                b.grid(row=2, columnspan=2, sticky=S, pady=5)
            else:
                instruction = Label(top, text='You have no comics.')
                instruction.grid(row=0)
                b = Button(top, text='OK', command=topwindow.destroy)
                b.grid(row=1, columnspan=2)
    def doDownload(self, menu, top, comics):
        c = menu.get(menu.curselection())
        top.destroy()
        wcid = comics[c]
        # download the layout file
        cfl = self.downloadAComicLayout(wcid)
        if cfl:
            self.openLayoutFile(cfl)
        else:
            top = Toplevel(self.master)
            top.title("Error")
            instruction = Label(top, text='Error downloading layout.')
            instruction.grid(row=0)
            b = Button(top, text='OK', command=top.destroy)
            b.grid(row=1)
    def downloadAComicLayout(self, wcid):
        self.br.open('http://comicfury.com/managecomic.php?id=%s&action=exportlayout'%wcid)
        cfl = self.br.response().read()
        return cfl
    def doUpload(self, menu, top, comics):
        c = menu.get(menu.curselection())
        top.destroy()
        wcid = comics[c]
        # backup old layout file
        cflb = self.downloadAComicLayout(wcid)
        if cflb:
            f = open("_backup.cfl.xml.backup", 'w')
            f.write(cflb)
            f.close()
        # get the layout file
        cfl = self.makeLayoutFile()
        r = self.br.open('http://comicfury.com/managecomic.php?id=%s&action=importlayout'%wcid)
        self.br.select_form(nr=1)
        f = open("_temp.cfl.xml", "w")
        f.write(cfl)
        f.close()
        f = open("_temp.cfl.xml", "r")
        self.br.form.add_file(f, 'text/xml', 'layout.cfl.xml')
        self.br.submit()
    def upload(self):
        self.selectComicAndRun(self.doUpload, self.upload)
    def makeLayoutFile(self):
        tags = []
        tags.append('<?xml version="1.0" encoding="UTF-8"?>')
        tags.append('<!-- ComicFury layout XML 1.1, use import layout function to use this. -->')
        tags.append('<layout>')
        tags.append('<name>Exported ComicFury layout v%s</name>'%version)
        tags.append('<cfxml>1.1</cfxml>')
        tags.append('<spage>1</spage>')
        tags.append('<ldata>')
        # I could probably do a thing like I did in openLayoutFile but ehhh it's early
        tags.append('<overall>%s</overall>'%self.textboxes['overall'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<blog>%s</blog>'%self.textboxes['overview'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<comic>%s</comic>'%self.textboxes['comic'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<archive>%s</archive>'%self.textboxes['archive'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<blogarchive>%s</blogarchive>'%self.textboxes['blog'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<error>%s</error>'%self.textboxes['errors'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<search>%s</search>'%self.textboxes['search'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('<layoutcss>%s</layoutcss>'%self.textboxes['css'].text.get('1.0',END).encode('utf-8').encode('base64'))
        tags.append('</ldata>')
        tags.append('</layout>')
        return "\n".join(tags)
    def save(self):
        f = asksaveasfile(filetypes=[("CF layout files", "*.cfl.xml")])
        f.write(self.makeLayoutFile())
        f.close()
    def insert(self, name):
        data = {
            'css':'<!--layout:[css]-->',
            'content':'<!--layout:[content]-->',
            'cfjs':'<script type="text/javascript" src="http://comicfury.com/cflayoutjs.js.php?cc=inline&amp;wcid=[v:webcomicid]"></script>'
            }
        sel = self.nb.focus_get()
        if sel:
            # sel is the selected text box
            if name in data:
                try:
                    sel.insert(INSERT, data[name])
                except AttributeError: # SCREW YOU
                    pass

    # cf stuff
    def logout(self):
        r = self.br.open('http://comicfury.com/login.php')
        self.br.select_form(nr=1)
        self.br.submit()
    def cf_login(self, incorrect=False, caller=None):
        # get login data
        top = Toplevel(self.master)
        top.title("Login to CF")
        if incorrect:
            instruction = Label(top, text="Incorrect login data.")
        else:
            instruction = Label(top, text="Login to CF to access your comics.")
        instruction.grid(row=0, columnspan=2)
        usernamelabel = Label(top, text="Username: ")
        passwordlabel = Label(top, text="Password: ")
        usernameentry = Entry(top)
        passwordentry = Entry(top, show="*")
        usernamelabel.grid(row=1, column=0)
        usernameentry.grid(row=1, column=1)
        passwordlabel.grid(row=2, column=0)
        passwordentry.grid(row=2, column=1)

        run = (lambda u=usernameentry,p=passwordentry,b=top,c=caller:self._dologin(b,u,p,c))
        runbound = (lambda event,u=usernameentry,p=passwordentry,b=top,c=caller:self._dologin(b,u,p,c))
        usernameentry.bind('<Return>', runbound)
        passwordentry.bind('<Return>', runbound)
        
        submitbutton = Button(top, text="Login")
        submitbutton.configure(command = run)
        submitbutton.grid(row=3, columnspan=2)
    def _dologin(self, top, username, password, caller):
        u = username.get()
        p = password.get()
        top.destroy()
        # actually login. cf_login only handles the popup
        r = self.br.open('http://comicfury.com/login.php')
        self.br.select_form(nr=1)
        self.br.form['username'] = u
        self.br.form['password'] = p
        self.br.submit()
        # we good? we cool?
        if self.br.geturl().endswith('login.php'):
            self.cf_login(incorrect=True, caller=caller)
            return False
        else:
            # WE GOOD. WE COOL.
            if caller:
                caller()
            return True
    # custom textbox widget thing
    class Textbox(Text):
        updateperiod = 50
        editors = []
        updateId = None
        def __init__(self, master, mode="HTML"):
            self.__class__.editors.append(self)
            self.lineNumbers = ''
            self.frame = Frame(master, relief=SUNKEN)
            self.vScrollbar = Scrollbar(self.frame, orient=VERTICAL)
            self.vScrollbar.pack(fill='y', side=RIGHT)
            self.lnText = Text(self.frame,
                               width = 4,
                               padx = 4,
                               highlightthickness = 0,
                               takefocus = 0,
                               background = 'lightgrey',
                               foreground = 'white',
                               state = 'disabled')
            self.lnText.pack(side=LEFT, fill='y')
            self.text = self.SyntaxText(self.frame,
                             mode=mode,
                             padx=4,
                             undo=True,
                             relief=FLAT)
            self.text.config(yscrollcommand=self.vScrollbar.set)
            self.text.pack(fill='both', expand=True)
            self.vScrollbar.config(command=self.text.yview)
            if self.__class__.updateId is None:
                self.updateAllLineNumbers()
        def getLineNumbers(self):
            x = 0
            line = '0'
            col = ''
            ln = ''
            step = 6
            nl = '\n'
            lineMask = '    %s\r\n'
            indexMask = '@0,%d'
            for i in xrange(0, self.text.winfo_height(), step):
                ll, cc = self.text.index(indexMask%i).split('.')
                if line == ll:
                    if col != cc:
                        col = cc
                        ln += nl
                else:
                    line, col = ll, cc
                    ln += (lineMask % line)[-5:]
            return ln

        def updateLineNumbers(self):
            tt = self.lnText
            ln = self.getLineNumbers()
            if self.lineNumbers != ln:
                self.lineNumbers = ln
                tt.config(state='normal')
                tt.delete('1.0', END)
                tt.insert('1.0', self.lineNumbers)
                tt.config(state='disabled')
                
        @classmethod
        def updateAllLineNumbers(cls):
            if len(cls.editors) < 1:
                cls.updateId = None
                return
            for ed in cls.editors:
                ed.updateLineNumbers()

            cls.updateId = ed.text.after(
                cls.updateperiod,
                cls.updateAllLineNumbers)

        class SyntaxText(Text):
            # http://stackoverflow.com/a/3781773/1105803 http://forums.devshed.com/showpost.php?p=747094&postcount=2
            def __init__(self, *args, **kwargs):
                self.mode = kwargs['mode']
                del kwargs['mode']
                Text.__init__(self, *args, **kwargs)
                self.tag_configure("blue",foreground="#0000ff")
                self.tag_configure("red",foreground="#ff0000")
                self.tag_configure("cf_v",foreground="#2DA420")
                self.tag_configure("cf_c",foreground="#289D95")
                self.tag_configure("grey",foreground="#7C7C7C")
                self.bind('<Key>', self.updatetags)
            def removetags(self, start, end):
                self.tag_remove("blue", start, end)
                self.tag_remove("red", start, end)
                self.tag_remove("cf_v", start, end)
                self.tag_remove("cf_c", start, end)
                self.tag_remove("grey", start, end)
                # should probably make this automatic at some point
            def updatetags(self, data):
                self.removetags('1.0', 'end')
                if self.mode == 'HTML':
                    self.highlight(r'<[^<]+?>', 'blue')
                    self.highlight(r'(["\']).*?\1', 'red')
                    self.highlight(r'\[v:.*?\]', 'cf_v')
                    self.highlight(r'\[[cl]:.*?\]', 'cf_c')
                    self.highlight(r'\[/\]', 'cf_c')
                    self.highlight(r'<!--.*?-->', 'grey')
                else:
                    self.highlight(r'[^{}]+ {', 'blue')
                    self.highlight(r'}', 'blue')
                    self.highlight(r'[^{}]+:.+?;', 'red')
                    self.highlight(r'\[v:.*?\]', 'cf_v')
                    self.highlight(r'\[[cl]:.*?\]', 'cf_c')
                    self.highlight(r'\[/\]', 'cf_c')
                    self.highlight(r'/\*.*?\*/', 'grey')
            def highlight(self, pattern, tag):
                start = self.index('1.0')
                end = self.index('end')
                self.mark_set("matchStart",start)
                self.mark_set("matchEnd",start)
                self.mark_set("searchLimit", end)

                count = IntVar()
                while True:
                    index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=True)
                    if index == "":
                        break
                    self.mark_set("matchStart", index)
                    self.mark_set("matchEnd", "%s+%sc" % (index,count.get()))
                    self.tag_add(tag, "matchStart","matchEnd")

root = Tk() # the window
root.title("CF Layout Editor")
iconimage = PhotoImage(file='icon.gif')
root.tk.call('wm', 'iconphoto', root._w, iconimage)

main = Main(root)
root.mainloop() # start window - events, redraws, geometry

