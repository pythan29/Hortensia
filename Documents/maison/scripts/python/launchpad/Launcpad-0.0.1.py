#!/usr/bin/env python3.4
from tkinter import *

from tkinter.filedialog import asksaveasfile, askopenfile 
from tkinter import messagebox

import time, threading

import sfml as sf
import os

SPACE=10
TOUCH=70
BORD=SPACE+(TOUCH+SPACE)*8

DEFAULT="gray"
RED="red"
ORANGE="orange"
YELLOW="yellow"
GREEN="green"

CODICO={DEFAULT:b"\x00", RED:b"\x0b", ORANGE:b"\x7f", YELLOW:b"\x3a", GREEN:b"\x70", "light gray":b"\x00"}

FILE=os.open("/dev/snd/midiC1D0", os.O_RDWR)

def GETCOORDS(id):
    return ((id-1)%8+1, (id-1)//8+1)

def GETCASE(evx, evy):
    return int(int(evy/(TOUCH+SPACE))*8+(evx/(TOUCH+SPACE)))+1


class Motif:
    def __init__(self, boss, cboss):
        self.boss=boss
        self.cboss=cboss
        self.motif=[]
    
    def play(self):self.boss.after(0, self._play)
    
    def _play(self):
        for i, j in enumerate(self.motif):
            self.cboss.getButton(i+1).chcolor(j)
    
    def stop(self):self.boss.after(0, self._stop)
    
    def _stop(self):
        for i, j in enumerate(self.motif):
            if j!=DEFAULT:
                self.cboss.getButton(i+1).chcolor(DEFAULT)
    
    def modifier(self):
        self.motif=[DEFAULT]*64
        self.top=Toplevel(self.boss)
        self.launchpad=DerivatedLaunchpad(self.top)
        self.launchpad.grid(row=0, column=0)
        Button(self.top, text="Ok", command=self.create).grid(row=1, column=0, sticky="e")
    
    def create(self):
        for i, _ in enumerate(self.motif):
            self.motif[i]=self.launchpad.getButton(i+1).state[0]
        self.cboss.void()
        self.top.destroy()

class Buttonproperties(Toplevel):
    def __init__(self, button):
        Toplevel.__init__(self,button.canvas.boss)
        self.button=button
        
        self.motif=None
        
        self.transient(self.button.canvas.boss)
        self.bind("<Destroy>", lambda event:self.button.chcolor(DEFAULT))
        self.title("Motif {}".format(self.button.id))
        
        self.frame1=Frame(self)
        Label(self.frame1, text="Son joué:").grid(row=0, column=0)
        self.song=Entry(self.frame1)
        self.song.insert(END,self.button.state[1])
        self.song.grid(row=0, column=1)
        self.navigate=Button(self.frame1, text="...", command=self.opensound).grid(row=0, column=2)
        self.frame1.grid(row=0, column=0)
        
        Label(self, text="Lors de l'appui sur la touche:").grid(row=1, column=0, columnspan=3, sticky="w")
        
        self.frame2=Frame(self)
        
        self.choixmode=StringVar()
        self.choixmode.set("color")
        
        self.choixcouleur=StringVar()
        self.choixcouleur.set("red")
        
        self.radbuttons=[None, None]
        for n in range(2):
            self.radbuttons[n] = Radiobutton(self.frame2,
                               text = ("Allumer la case en :", "Creer un motif :")[n],
                               variable = self.choixmode,
                               value = ("color", "motif")[n],
                               command=self.EvRadiobutton)
            self.radbuttons[n].grid(row=n, column=0, sticky="w")
        
        self.radbuttons[1 if self.button.state[0]=="m" else 0].select()
        
        self.opmen=OptionMenu(self.frame2, self.choixcouleur, "Off", "red", "green", "orange", "yellow")
        self.opmen.grid(row=0, column=1)
        self.modif=Button(self.frame2, text="Modifier...", command=self.createMotif)
        self.modif.grid(row=1, column=1)
        
        self.frame2.grid(row=2, column=0, columnspan=3, sticky="w")
        
        Button(self, text="Annuler", command=self.destroy).grid(row=3, column=0, sticky="e")
        Button(self, text="Ok", command=self.valid).grid(row=3, column=2, sticky="w")
        
        self.EvRadiobutton()
        
    def EvRadiobutton(self):
        if self.choixmode.get()=="motif":
            self.modif.config(state=NORMAL)
            self.opmen.config(state=DISABLED)
        else:
            self.modif.config(state=DISABLED)
            self.opmen.config(state=NORMAL)
    
    def opensound(self):
        ofi =askopenfile(filetypes=[("Son wav",".wav"),("Son mp3",".mp3"),("Son ogg",".ogg")]) 
        self.song.delete(0, END)
        self.song.insert(END, ofi.name)
    
    def createMotif(self):
        self.motif=Motif(self, self.button.canvas)
        self.motif.modifier()
        
    
    def valid(self):
        if self.choixmode.get()=="motif":
            color="m"
        else:
            color=self.choixcouleur.get()
            
            
        file=self.song.get()
        ext=file.split(".")[-1] 
        if ext not in ["wav","mp3","ogg"]:
            messagebox.showerror("Error","{}:File extention not supported".format(ext))
            return
        
        try:
            buf=sf.SoundBuffer.from_file(file)
        except Exception as e:
            messagebox.showerror("Error","{}:File not found".format(file))
            print(e)
            return
        
        sound=sf.Sound(buf)
        self.button.config([color, file, buf, sound, self.motif])
        #print(self.button.id, ":", self.button.state)
        self.destroy()
        
class Bouton:
    def __init__(self, id, canvas):
        self.id=id
        self.canvas=canvas
        self.x, self.y=GETCOORDS(self.id)
        self.x=self.x*(TOUCH+SPACE)
        self.y=self.y*(TOUCH+SPACE)
        self.me=None
        self.prop=None
        self.state=[DEFAULT,"",None, None, None]
        self.event=False
        
    def draw(self):
        self.me=self.canvas.create_rectangle(self.x, self.y, self.x-TOUCH, self.y-TOUCH, fill="gray")
    
    def chcolor(self, color):
        self.canvas.itemconfigure(self.me, fill=color)
        os.write(FILE, b'\x90'+bytes(chr((self.id-1)//8*16+(self.id-1)%8), encoding="ascii")+CODICO[color])
    
    def chcolorc(self, color):
        self.canvas.itemconfigure(self.me, fill=color)
        os.write(FILE, b'\x90'+bytes(chr((self.id-1)//8*16+(self.id-1)%8), encoding="ascii")+CODICO[color])
        self.state[0]=color
    
    def properties(self):
        self.prop=Buttonproperties(self)
    
    def activate(self):self.canvas.boss.after(0, self._activate)
    
    def _activate(self):
        if self.state[3]:
            if self.state[3].STOPPED:
                self.desactivate()
        if self.event:
            return
        self.event=True
        if self.state[0]!="m":
            self.canvas.itemconfigure(self.me, fill=self.state[0])
            os.write(FILE, b'\x90'+bytes(chr((self.id-1)//8*16+(self.id-1)%8), encoding="ascii")+CODICO[self.state[0]])
        else:
            self.state[4].play()
        
        if self.state[3]!=None:
            self.state[3].play()
    
    def desactivate(self):self.canvas.boss.after(0, self._desactivate)
    
    def _desactivate(self):
        if not self.event:
            return
        self.event=False
        if self.state[0]!="m":
            self.canvas.itemconfigure(self.me, fill=DEFAULT)
            os.write(FILE, b'\x90'+bytes(chr((self.id-1)//8*16+(self.id-1)%8), encoding="ascii")+b"\x00")
        else:
            self.state[4].stop()
        if self.state[3]!=None:
            self.state[3].stop()
        
    def config(self, state):
        #print(state)
        self.state=state
    
    def void(self):
        self.chcolor(DEFAULT)
        self.state=[DEFAULT,"",None, None]

class DerivatedLaunchpad(Canvas):
    def __init__(self, boss):
        Canvas.__init__(self, boss,  width=BORD, height=BORD, bg="black")
        self.boss=boss
        self.colors={DEFAULT:RED, RED:ORANGE, ORANGE:YELLOW, YELLOW:GREEN, GREEN:DEFAULT}
        self.boutons=[]
        self.drawButtons()
        self.bind("<Button-1>", self.change)
    
    def drawButtons(self):
        for i in range(1, 65):
            self.boutons.append(Bouton(i, self))
            self.boutons[i-1].draw()
    
    def getButton(self, id):
        return self.boutons[id-1]
    
    def change(self, event=None, case=None):
        if (not case) and event:
            case=GETCASE(event.x, event.y)
        button=self.getButton(case)
        button.chcolorc(self.colors[button.state[0]])
    
    def void(self):
        for i in self.boutons:
            i.void()

class Launchpad(Canvas):
    def __init__(self, boss):
        Canvas.__init__(self, boss,  width=BORD, height=BORD, bg="black")
        self.boss=boss
        self.boutons=[]
        self.motifmodif=False
        self.drawButtons()
        self.bind("<Button-1>", self.opts)
        #for i, j in enumerate([chr(x) for x in range(97, 123)]):
            #print("self.boss.bind("<KeyPress-{}>", lambda event:self.playbutt({}))".format(j, i+1))
            #print("self.boss.bind("<KeyRelease-{}>", lambda event:self.stopbutt({}))".format(j, i+1))
            #print("<KeyPress-{}>".format(j), ":" ,i+1)
        self.binds_force()
    
    def drawButtons(self):
        for i in range(1, 65):
            self.boutons.append(Bouton(i, self))
            self.boutons[i-1].draw()
    
    def getButton(self, id):
        return self.boutons[id-1]
    
    def opts(self, event=None, case=None):
        if (not case) and event:
            case=GETCASE(event.x, event.y)
        button=self.getButton(case)
        button.chcolor("light gray")
        button.properties()
            
    
    def playbutt(self, id):
        self.getButton(id).activate()
    
    def stopbutt(self, id):
        self.getButton(id).desactivate()
    
    def void(self):
        for i in self.boutons:
            i.void()
    
    
    def binds_force(self):
        self.boss.bind("<KeyPress-a>", lambda event:self.playbutt(1))
        self.boss.bind("<KeyRelease-a>", lambda event:self.stopbutt(1))
        self.boss.bind("<KeyPress-z>", lambda event:self.playbutt(2))
        self.boss.bind("<KeyRelease-z>", lambda event:self.stopbutt(2))
        self.boss.bind("<KeyPress-e>", lambda event:self.playbutt(3))
        self.boss.bind("<KeyRelease-e>", lambda event:self.stopbutt(3))
        self.boss.bind("<KeyPress-r>", lambda event:self.playbutt(4))
        self.boss.bind("<KeyRelease-r>", lambda event:self.stopbutt(4))
        self.boss.bind("<KeyPress-t>", lambda event:self.playbutt(5))
        self.boss.bind("<KeyRelease-t>", lambda event:self.stopbutt(5))
        self.boss.bind("<KeyPress-y>", lambda event:self.playbutt(6))
        self.boss.bind("<KeyRelease-y>", lambda event:self.stopbutt(6))
        self.boss.bind("<KeyPress-u>", lambda event:self.playbutt(7))
        self.boss.bind("<KeyRelease-u>", lambda event:self.stopbutt(7))
        self.boss.bind("<KeyPress-i>", lambda event:self.playbutt(8))
        self.boss.bind("<KeyRelease-i>", lambda event:self.stopbutt(8))
        self.boss.bind("<KeyPress-q>", lambda event:self.playbutt(9))
        self.boss.bind("<KeyRelease-q>", lambda event:self.stopbutt(9))
        self.boss.bind("<KeyPress-s>", lambda event:self.playbutt(10))
        self.boss.bind("<KeyRelease-s>", lambda event:self.stopbutt(10))
        self.boss.bind("<KeyPress-d>", lambda event:self.playbutt(11))
        self.boss.bind("<KeyRelease-d>", lambda event:self.stopbutt(11))
        self.boss.bind("<KeyPress-f>", lambda event:self.playbutt(12))
        self.boss.bind("<KeyRelease-f>", lambda event:self.stopbutt(12))
        self.boss.bind("<KeyPress-g>", lambda event:self.playbutt(13))
        self.boss.bind("<KeyRelease-g>", lambda event:self.stopbutt(13))
        self.boss.bind("<KeyPress-h>", lambda event:self.playbutt(14))
        self.boss.bind("<KeyRelease-h>", lambda event:self.stopbutt(14))
        self.boss.bind("<KeyPress-j>", lambda event:self.playbutt(15))
        self.boss.bind("<KeyRelease-j>", lambda event:self.stopbutt(15))
        self.boss.bind("<KeyPress-k>", lambda event:self.playbutt(16))
        self.boss.bind("<KeyRelease-k>", lambda event:self.stopbutt(16))
        self.boss.bind("<KeyPress-w>", lambda event:self.playbutt(17))
        self.boss.bind("<KeyRelease-w>", lambda event:self.stopbutt(17))
        self.boss.bind("<KeyPress-x>", lambda event:self.playbutt(18))
        self.boss.bind("<KeyRelease-x>", lambda event:self.stopbutt(18))
        self.boss.bind("<KeyPress-c>", lambda event:self.playbutt(19))
        self.boss.bind("<KeyRelease-c>", lambda event:self.stopbutt(19))
        self.boss.bind("<KeyPress-v>", lambda event:self.playbutt(20))
        self.boss.bind("<KeyRelease-v>", lambda event:self.stopbutt(20))
        self.boss.bind("<KeyPress-b>", lambda event:self.playbutt(21))
        self.boss.bind("<KeyRelease-b>", lambda event:self.stopbutt(21))
        self.boss.bind("<KeyPress-n>", lambda event:self.playbutt(22))
        self.boss.bind("<KeyRelease-n>", lambda event:self.stopbutt(22))
        self.boss.bind("<KeyPress-l>", lambda event:self.playbutt(23))
        self.boss.bind("<KeyRelease-l>", lambda event:self.stopbutt(23))
        self.boss.bind("<KeyPress-m>", lambda event:self.playbutt(24))
        self.boss.bind("<KeyRelease-m>", lambda event:self.stopbutt(24))
    

class EventNlp(threading.Thread):
    def __init__(self, nlp):
        threading.Thread.__init__(self)
        self.nlp=nlp
        self.running=True
    
    def run(self):
        while 1:
            now=os.read(FILE,3)
            if self.running == False: break
            #print(now)
            #print(str(now[1]))
            key=int(str(now[1]))//16*8+int(str(now[1]))%16+1
            velocity=bool(int(str(now[2]), 16))
            #print(now)
            #print(int(str(now[1]))//16*8+int(str(now[1]))%16+1)
            self.nlp.event(key, velocity)
            
            #os.write(FILE, b'\x90'+now[1:2]+now[2:3])
    
    def stop(self):
        self.running=False

class Master(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("Launchpad")
        self.fr=Frame(self)
        self.bout=Button(self.fr, text="Jouer", command=self.modifyButton)
        self.bout.pack(side="left")
        self.fr.pack(expand="yes", fill="x")
        self.nlp=Launchpad(self)
        self.nlp.pack()
        self.mixing=False
        self.thev=EventNlp(self)
        self.thev.start()

    
    def event(self, pad, val):
        self.after(0, lambda : self._event(pad, val))
    
    def _event(self, pad, val):
        if self.mixing:
            if val:
                self.nlp.getButton(pad).activate()
            else:
                self.nlp.getButton(pad).desactivate()
        else:
            if val:
                self.nlp.opts(case=pad)
    
    def modifyButton(self):
        self.mixing = not self.mixing
        self.bout.config(text="Configurer" if self.mixing else "Jouer")

a=Master()
a.mainloop()
print("exit")
os.close(FILE)
print("please touch your launchpad to exit...")
a.thev.stop()
