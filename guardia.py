import tkinter
from tkinter import Canvas
from tkinter import messagebox
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
import time
import socket
import sys
import pickle
import struct
from data import DataSerializer
import requests
from ttkthemes import themed_tk as tk
import asyncio
import threading

class App:
    def __init__(self, root,w,h,async_loop):
        self.cards_detected=[]
        self.async_loop=async_loop
        ##Cameras on System
        index = 0
        OPTIONS_CAMERA = []
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                break
            else:
                OPTIONS_CAMERA.append(index)
                self.video_source=index
            cap.release()
            index += 1
        ##Variables
        self.student_id = 0
        self.w = w
        self.h = h
        self.connected= False
        self.client_soc = ClientSocket()
        self.count_canvas_unknown = -100
        self.count_canvas_detected = -100
        self.img_ref = []
        self.window=root

        ##Frame LeftSide Scene
        self.leftFrame = ttk.Frame(root, width=w/2, height = h-50)
        self.leftFrame.grid(row=1, column=0)
        self.leftFrame.grid_propagate(False)


        ##Frame RightSide Scene
        self.rightFrame = ttk.Frame(root, width=w-5/2, height = h-50)
        self.rightFrame.grid(row=1, column=1)
        self.rightFrame.grid_propagate(False)     

        ##ComboBox Camera
        self.cameraFrame = ttk.Frame(root,width=w/2,height=45)
        self.cameraFrame.grid(row=0, column=0)
        self.cameraFrame.grid_propagate(False)
        ttk.Label(self.cameraFrame, text="Seleccionar Cámara",font = "Arial 12").grid(row=0, column=0,pady=10,padx=10)
        self.combo_camera  = ttk.Combobox(self.cameraFrame, state="readonly")
        self.combo_camera .grid(row=0,column=1)
        self.combo_camera ["values"] = OPTIONS_CAMERA
        self.combo_camera .bind("<<ComboboxSelected>>", self.selection_changed)
        self.searchCamerasBtn = ttk.Button(self.cameraFrame, text="Buscar Cámaras", command=lambda:self.search_camera())
        self.searchCamerasBtn.grid(row=0, column=2, padx=10, pady=10)

        ##Exit Frame
        exitFrame = ttk.Frame(root,width=w,height=45)
        exitFrame.grid(row=0, column=1)
        exitFrame.grid_propagate(False)
        resizeBtn = ttk.Button(exitFrame, text="Salir de Programa", command=root.destroy)
        resizeBtn.grid(row=0, column=int(w/3),columnspan=int(w/3), pady=10)


        ##LeftSide
        ##Video Canvas Camera
        self.canvas_video = tkinter.Canvas(self.leftFrame, highlightthickness=1, highlightbackground="#C9D7DC",width = (w-10)/2, height = h-100)
        self.canvas_video.grid(row=0,column=0)
        ##Frame connect Server
        self.btnFrame = ttk.Frame(self.leftFrame,width=w/2,height=45)
        self.btnFrame.grid(row=1, column=0)
        self.btnFrame.grid_propagate(False)
        ttk.Label(self.btnFrame, text="IP/Name",font = "Arial 12").grid(row=1, column=0,pady=10)
        ttk.Label(self.btnFrame, text="Port",font = "Arial 12").grid(row=1, column=2,pady=10,padx=10)
        self.e1 = ttk.Entry(self.btnFrame)
        self.e2 = ttk.Entry(self.btnFrame)
        self.e1.grid(row=1, column=1,columnspan=1)
        self.e2.grid(row=1, column=3,columnspan=1)
        self.connectBtn = ttk.Button(self.btnFrame, text="Connect", command=lambda:self.connect_server(self.e1.get(),self.e2.get()))
        self.connectBtn.grid(row=1, column=4, padx=10, pady=10)



        #RigthSide
        # # Create a canvas that can fit faces  detected
        label_title_unknown = ttk.Label(self.rightFrame,text="Desconocidos",font = "Arial 15 bold")
        label_title_unknown.grid(row=0,column=0,padx=w/6,columnspan=w)
        self.canvas_faces_unknown = tkinter.Canvas(self.rightFrame, highlightthickness=1, highlightbackground="#C9D7DC",width =(w-10)/2, height = 100)
        self.canvas_faces_unknown.grid(row=1,column=0)
        label_title_detected = ttk.Label(self.rightFrame,text="Identificados",font = "Arial 15 bold")
        label_title_detected.grid(row=2,column=0,padx=w/6,columnspan=w)
        self.canvas_faces_detected = tkinter.Canvas(self.rightFrame, highlightthickness=1, highlightbackground="#C9D7DC",width =(w-10)/2, height = 100)
        self.canvas_faces_detected.grid(row=3,column=0)

        studentFrame = ttk.Frame(self.rightFrame,width=w/2,height=h-200)
        studentFrame.grid(row=4, column=0)
        studentFrame.grid_propagate(False)
        ttk.Label(studentFrame, text="Información Estudiante",font = "Arial 15 bold").grid(row=0,column=0,pady=20,padx=w/6,columnspan=w)
        self.canvas_face_student = tkinter.Canvas(studentFrame,highlightthickness=1, highlightbackground="#C9D7DC", width =100, height = 100)
        self.canvas_face_student.grid(row=1, column=0,pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Matricula",font = "Arial 12",width=12,anchor="w").grid(row=2, column=0,pady=10,padx=20)
        self.string_card_id = tkinter.StringVar()
        self.label_card_id = ttk.Label(studentFrame, textvariable=self.string_card_id,font = "Arial 12")
        self.label_card_id.grid(row=2, pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Nombre",font = "Arial 12",width=12,anchor="w").grid(row=3, column=0,pady=10,padx=20)
        self.string_name = tkinter.StringVar()
        self.label_name = ttk.Label(studentFrame, textvariable=self.string_name,font = "Arial 12")
        self.label_name.grid(row=3, pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Apellidos",font = "Arial 12",width=12,anchor="w").grid(row=4, column=0,pady=10,padx=20)
        self.string_last_name = tkinter.StringVar()
        self.label_last_name = ttk.Label(studentFrame, textvariable=self.string_last_name,font = "Arial 12")
        self.label_last_name.grid(row=4, pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Carrera",font = "Arial 12",width=12,anchor="w").grid(row=5, column=0,pady=10,padx=20)
        self.string_major = tkinter.StringVar()
        self.label_major = ttk.Label(studentFrame, textvariable=self.string_major,font = "Arial 12")
        self.label_major.grid(row=5, pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Cuatrimestre",font = "Arial 12",width=12,anchor="w").grid(row=6, column=0,pady=10,padx=20)
        self.string_quarter = tkinter.StringVar()
        self.label_quarter = ttk.Label(studentFrame, textvariable=self.string_quarter,font = "Arial 12")
        self.label_quarter.grid(row=6, pady=10,padx=w/5,columnspan=w)

        ttk.Label(studentFrame, text="Curp",font = "Arial 12",width=12,anchor="w").grid(row=8, column=0,pady=10,padx=20)
        self.string_curp = tkinter.StringVar()
        self.label_curp = ttk.Label(studentFrame, textvariable=self.string_curp,font = "Arial 12")
        self.label_curp.grid(row=8,pady=10,padx=w/5,columnspan=w)


        # # self.scroll_x = tkinter.Scrollbar(window, orient="horizontal", command=self.canvas_faces_detected.xview)
        # # self.scroll_x.grid(row=2, column=0, sticky="ew")
        # # self.canvas_faces_detected.configure(xscrollcommand=self.scroll_x.set)
        # # self.canvas_faces_detected.configure(scrollregion=self.canvas_faces_detected.bbox("all"))


 
        # Button that lets the user take a snapshot
        # self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=10, command=self.snapshot)
        # self.btn_snapshot.place(x=505,y=505)

    
        # After it is c
        # alled once, the update method will be automatically called every delay milliseconds
        self.delay = 10
        self.select_method_update()

    def search_camera(self):
        self.canvas_video = tkinter.Canvas(self.leftFrame, highlightthickness=1, highlightbackground="#C9D7DC",width = (w-10)/2, height = h-100)
        self.canvas_video.grid(row=0,column=0)
        if hasattr(self, 'vid') and self.vid.vid.isOpened():
            self.vid.vid.release()
        index = 0
        OPTIONS_CAMERA = []
        while True:
            cap = cv2.VideoCapture(index)
            if not cap.read()[0]:
                break
            else:
                OPTIONS_CAMERA.append(index)
                self.vid = MyVideoCapture(index)
            cap.release()
            index += 1
        self.combo_camera ["values"] = OPTIONS_CAMERA
        self.combo_camera .bind("<<ComboboxSelected>>", self.selection_changed)
        ##self.select_method_update()

    def selection_changed(self, event):
        #open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(int(self.combo_camera.get()))
        print("Nuevo elemento seleccionado:", self.combo_camera.get())
        
 
    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()
        if ret:
            cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
 
    def connect_server(self,host,port):
        if hasattr(self, 'vid'):
            try:
                self.client_soc = ClientSocket()
                port = int(port)
                print("connecting to: ", host, " | ", port)	
                self.client_soc.soc.settimeout(10)
                self.client_soc.soc.connect((host, port))
                print("Connected")
                self.connected = True
                self.connectBtn = ttk.Button(self.btnFrame, text="Disconnect", command=lambda:self.disconnect_server())
                self.connectBtn.grid(row=1, column=4, padx=10, pady=10)
            except:
                messagebox.showwarning(message="Punto de Acceso invalido o inaccesible", title="Info")
                self.connected = False
                #sys.exit()
        else :
            messagebox.showwarning(message="Cámara no Detectada", title="Info")
    
    def disconnect_server(self):
        self.client_soc.soc.close()
        self.connected = False
        self.connectBtn = ttk.Button(self.btnFrame, text="Connect", command=lambda:self.connect_server(self.e1.get(),self.e2.get()))
        self.connectBtn.grid(row=1, column=4, padx=10, pady=10)
        self.select_method_update()


    def _asyncio_thread(self,async_loop,card_id,crop_img):
        async_loop.run_until_complete(self.getStudentInfo(card_id,crop_img))

    def select_face_detected(self,card_id,crop_img): 
        threading.Thread(target=self._asyncio_thread, args=(self.async_loop,card_id,crop_img)).start()
       

    async def getStudentInfo(self,card_id,crop_img):
        url = "https://catalogoestudiantes.herokuapp.com/api/v1/student-card/"+card_id
        response =requests.get(
            url,
            headers={'Accept': 'application/json'})
        if response.status_code == 201:
            student = response.json()
            self.string_card_id.set(card_id)
            self.photo_face = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(crop_img))
            self.canvas_face_student.create_image(0, 0,image=self.photo_face, anchor = tkinter.NW)
            if student :
                self.string_name.set(student[0]["first_name"])
                self.string_last_name.set(student[0]["last_name"])
                self.string_major.set(student[0]["major_name"])
                self.string_quarter.set(student[0]["grade"])
                self.string_curp.set(student[0]["curp"])
        elif response.status_code == 404:
            print("Not Found")
       
        
    
    def show_camera(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()
        w =  int((self.w-10)/2)
        h = int(self.h-100)
        if ret:
            frame= cv2.resize(frame, (w,h), interpolation=cv2.INTER_AREA)
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas_video.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        self.select_method_update()
    
    def select_method_update(self):
        if hasattr(self, 'vid') and self.vid.vid.isOpened():
            if self.connected :
                self.window.after(self.delay, self.update)
            else:
                self.window.after(self.delay, self.show_camera)
        else:
            self.window.after(self.delay,self.select_method_update)

  
    def update(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()
        if ret:
            frame_original = frame.copy()
            try :
                names,pos_faces,probabilities = self.client_soc.sendFrame(frame)
            except (ConnectionResetError, ConnectionAbortedError):
                print("Connection Error")
                self.connected=False
                self.select_method_update()
            faces_detected,faces_unknown = self.drawFaces(frame,names,pos_faces,probabilities)
            w =  int((self.w-10)/2)
            h = int(self.h-100)
            frame= cv2.resize(frame, (w,h), interpolation=cv2.INTER_AREA)
            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
            self.canvas_video.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
            if len(faces_unknown) !=0 :
                for i in faces_unknown:
                    crop_img = frame_original[pos_faces[i][1]:pos_faces[i][3], pos_faces[i][0]:pos_faces[i][2]]            
                    crop_img = cv2.resize(crop_img, (100,100), interpolation=cv2.INTER_AREA)
                    if(self.count_canvas_unknown<=w):
                        self.count_canvas_unknown = self.count_canvas_unknown+100
                        self.photo_cut = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(crop_img))
                        self.canvas_faces_unknown.create_image(self.count_canvas_unknown, 0, image = self.photo_cut, anchor = tkinter.NW)
                        self.img_ref.append(self.photo_cut)
                    else :
                        self.count_canvas_unknown=-100
            if len(faces_detected) !=0 :
                for i in faces_detected:
                    if(self.count_canvas_detected<=w):
                        if(names[i] not in self.cards_detected):
                            print(self.count_canvas_detected)
                            self.count_canvas_detected = self.count_canvas_detected+100
                            crop_img = frame_original[pos_faces[i][1]:pos_faces[i][3], pos_faces[i][0]:pos_faces[i][2]]
                            crop_img = cv2.resize(crop_img, (100,100), interpolation=cv2.INTER_AREA)
                            self.photo_cut = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(crop_img))
                            #self.student_id=names[i]
                            self.cards_detected.append(names[i])
                            button1 = tkinter.Button(self.rightFrame,command=lambda: self.select_face_detected(names[i],crop_img))
                            button1.configure(image=self.photo_cut)
                            self.canvas_faces_detected.create_window(self.count_canvas_detected, 0,window=button1, anchor = tkinter.NW)
                            self.img_ref.append(self.photo_cut)
                    else:
                        self.count_canvas_detected=-100
        self.select_method_update()

    def drawFaces(self,frame,names,pos_faces,probabilities):
        faces_detected = []
        faces_unknown = []
        for i in range(0,len(names)):
            text_x = pos_faces [i][0]
            text_y = pos_faces [i][3] + 20
            if probabilities [i] >= 0.68:
                cv2.rectangle(frame,(pos_faces[i][0],pos_faces[i][1]),(pos_faces[i][2],pos_faces[i][3]),(0,255,0),2)
                cv2.putText(frame, names[i],(text_x,text_y),cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            1.5,(0,0,255),thickness=2,lineType=2)
                faces_detected.append(i)
                
            elif probabilities [i] >= 0.50:
                cv2.rectangle(frame,(pos_faces[i][0],pos_faces[i][1]),(pos_faces[i][2],pos_faces[i][3]),(255,255,0),2)
                cv2.putText(frame, "Duda :"+names[i],(text_x,text_y),cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            1.5,(0,0,255),thickness=2,lineType=2)
            else :
                cv2.rectangle(frame,(pos_faces[i][0],pos_faces[i][1]),(pos_faces[i][2],pos_faces[i][3]),(255,0,0),2)
                cv2.putText(frame, "Desconocido",(text_x,text_y),cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            1.5,(0,0,255),thickness=2,lineType=2)
                faces_unknown.append(i)
                
        return faces_detected,faces_unknown
        
  
class ClientSocket:

    def __init__(self):
        self.encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def sendFrame(self,frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result, frame = cv2.imencode('.jpg', frame, self.encode_param)
        
        ''' Se crea un data serializer con el frame y un mensaje '''
        send_data = DataSerializer(frame, "Saludos del cliente")
        data = pickle.dumps(send_data, 0)
        size = len(data)
        self.soc.sendall(struct.pack(">L", size) + data)
        data = b""
        payload_size = struct.calcsize(">L")
        while len(data) < payload_size:
            data += self.soc.recv(4096)
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        while len(data) < msg_size:
            data += self.soc.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]
        recv_data=pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        names = recv_data.detected_name
        pos_faces = recv_data.detected_pos
        probabilities = recv_data.detected_precision
        return names,pos_faces,probabilities


class MyVideoCapture:
    def __init__(self, video_source):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        self.vid.set(cv2.CAP_PROP_FPS, 60)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
 
    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)
 
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

def exit(event):
    root.overrideredirect(0)
    ##root.quit()
# Create a window and pass it to the Application object
root = tk.ThemedTk()
root.get_themes()
root.set_theme("arc")

#root = tkinter.Tk()
root.title("SIDRIE")
#root.config(background = "#FFFFFF")
w, h = root.winfo_screenwidth(),root.winfo_screenheight()
root.overrideredirect(1)
root.geometry("%dx%d+0+0" % (w, h))
root.focus_set() 
#root.bind("<Escape>", exit)
async_loop = asyncio.get_event_loop()
app  = App(root,w,h,async_loop)
root.mainloop()