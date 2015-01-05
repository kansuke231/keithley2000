
import os
import wx
from visa import instrument


class Menu(wx.MenuBar):

    def __init__(self):
        wx.MenuBar.__init__(self)

        menu_file = wx.Menu()
        menu_id = wx.ID_ANY
        menu_file.Append(menu_id,"Output")

        self.Append(menu_file,"File")
        wx.EVT_MENU(self,menu_id,self.save)

        self.dirname = ''

    def save(self,event):
        dialog = wx.FileDialog(self, "Choose a file", self.dirname, "", ".txt", wx.SAVE | wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            # Grab the content to be saved
            data = self.GetParent().data

            # Open the file for write, close
            self.filename = dialog.GetFilename()
            self.dirname = dialog.GetDirectory()
            filehandle = open(os.path.join(self.dirname, self.filename),'w')

            for element in data:
                filehandle.write(str(element)+"\n")

            filehandle.close()
        # Get rid of the dialog to keep things tidy
        dialog.Destroy()



class DisplayPanel(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)

        self.display = wx.TextCtrl(self,wx.ID_ANY,"Select GPIB address and press *IDN?",style = wx.TE_RIGHT)
        #self.display.Disable()
        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(self.display,1)
        self.SetSizer(layout)

class SettingPanel(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)

        grid = wx.GridSizer(4,2)

        #GPIB adress
        elements_gpib_tuple = tuple([str(x) for x in range(1,31)])

        self.combo_box1 = wx.ComboBox(self,wx.ID_ANY,choices = elements_gpib_tuple,size=(50,-1),\
                                      style = wx.CB_READONLY,value = "16")
        grid.Add(wx.StaticText(self,wx.ID_ANY,"GPIB Address:"),0)
        grid.Add(self.combo_box1)

        #Measurement setting
        elements_measurement_tuple = (("DCV",":measure:voltage:dc?"),("DCI",":measure:current:dc?"),\
                                      ("R",":measure:resistance?"))

        self.combo_box2 = wx.ComboBox(self,wx.ID_ANY,size=(50,-1),style = wx.CB_READONLY)
        for element in elements_measurement_tuple:
            self.combo_box2.Append(element[0],element[1])
        grid.Add(wx.StaticText(self,wx.ID_ANY,"Measurement:"),0)
        grid.Add(self.combo_box2)

        #Sampling Period
        self.combo_box3 = wx.ComboBox(self,wx.ID_ANY,size=(50,-1),style = wx.CB_READONLY)
        for element in ("0.5","1","2","5","10","20"):
            self.combo_box3.Append(element)
        grid.Add(wx.StaticText(self,wx.ID_ANY,"Sampling Period [s]:"),0)
        grid.Add(self.combo_box3)

        #Single Shot
        self.check_box = wx.CheckBox(self,wx.ID_ANY)
        grid.Add(wx.StaticText(self,wx.ID_ANY,"Single Shot:"),0)
        grid.Add(self.check_box)

        self.SetSizer(grid)

class ControlPanel(wx.Panel):

    def __init__(self,parent):
        wx.Panel.__init__(self,parent,wx.ID_ANY)

        button1 = wx.Button(self,wx.ID_ANY,"START")
        button2 = wx.Button(self,wx.ID_ANY,"STOP")
        button3 = wx.Button(self,wx.ID_ANY,"*IDN?")

        layout = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(button1,flag=wx.GROW)
        layout.Add(button2,flag=wx.GROW)
        layout.Add(button3,flag=wx.GROW)
        self.SetSizer(layout)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,lambda event:self.consecutive_measurement(event,parent.GetParent().setting_panel,
                                                                         parent.GetParent().display_panel.display,
                                                                         parent.GetParent().keithley,
                                                                         parent.GetParent().data))

        self.Bind(wx.EVT_BUTTON,lambda event: self.start(event,parent),id = button1.GetId())
        self.Bind(wx.EVT_BUTTON,lambda event: self.stop(event),id = button2.GetId())
        self.Bind(wx.EVT_BUTTON,lambda event: self.askidn(event,parent),id = button3.GetId())


    def start(self,event,parent):
        try:
            #extract reference to each object used later from parent
            set_panel = parent.GetParent().setting_panel
            dis_panel = parent.GetParent().display_panel.display
            local_inst = parent.GetParent().keithley

            if set_panel.check_box.GetValue():
                self.single_measurement(set_panel,dis_panel,local_inst)
            else:
                parent.GetParent().data.append("Measurement: " + set_panel.combo_box2.GetStringSelection() +\
                 " "+ " Sampling Period: " + set_panel.combo_box3.GetStringSelection())
                self.timer.Start(float(set_panel.combo_box3.GetStringSelection())*1000)
        except:
            dis_panel.Clear()
            dis_panel.WriteText("ERROR!")

    def stop(self,event):
        self.timer.Stop()

    def single_measurement(self,set_panel,dis_panel,local_inst,flag = False):
        dis_panel.Clear()
        obtained_value = local_inst.ask_for_values(set_panel.combo_box2.GetClientData(set_panel.combo_box2.GetSelection()))[0]
        dis_panel.WriteText(str(obtained_value))
        if flag:
            return obtained_value

    def consecutive_measurement(self,event,set_panel,dis_panel,local_inst,data):
        obtained_value = self.single_measurement(set_panel,dis_panel,local_inst,flag = True)
        data.append(obtained_value)



    def askidn(self,event,parent):
        try:
            dis_panel = parent.GetParent().display_panel.display
            local_inst = parent.GetParent().keithley = instrument("GPIB::"\
                +parent.GetParent().setting_panel.combo_box1.GetStringSelection())
            local_inst.write("*RST; status:preset; *cls")
            dis_panel.Clear()
            dis_panel.WriteText(local_inst.ask("*IDN?"))
        except:
            dis_panel.Clear()
            dis_panel.WriteText("Error! Please Check GPIB Address")


class TopFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self,None,wx.ID_ANY,"Keithley 2000",
            size=(300,250),style= wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

        #GPIB Instrument
        self.keithley = None

        #Accumulated data
        self.data = []

        #Initializing menu bar

        self.SetMenuBar(Menu())

        #Constructing main parts of a window

        root_panel = wx.Panel(self,wx.ID_ANY)
        self.display_panel = DisplayPanel(root_panel)
        self.setting_panel = SettingPanel(root_panel)
        self.control_panel = ControlPanel(root_panel)

        root_layout = wx.BoxSizer(wx.VERTICAL)
        root_layout.Add(self.display_panel,0,wx.GROW|wx.ALL,border =10)
        root_layout.Add(self.setting_panel,0,wx.GROW|wx.LEFT|wx.RIGHT,border=20)
        root_layout.Add(self.control_panel,0,wx.GROW|wx.LEFT|wx.RIGHT,border=20)
        root_panel.SetSizer(root_layout)
        root_layout.Fit(root_panel)





if __name__ == "__main__":
    app = wx.App()
    frame = TopFrame()
    frame.Show()
    app.MainLoop()




