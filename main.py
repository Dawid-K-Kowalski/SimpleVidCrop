import tkinter
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from tkinter import filedialog
import math
from pyffmpeg import FFmpeg
import sys
#import time
import datetime


class VideoPlayer(tk.Canvas):
    def __init__(self, root, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.root = root
        self.video_path = None
        self.cap = None
        self.fps = None
        self.delay = None
        self.photo = None

        self.load_button = tk.Button(self.root, text="Load", command=self.load_video)
        self.play_button = tk.Button(self.root, text="Play", command=self.play)
        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause)
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop)
        self.export_button = tk.Button(self.root, text="Export", command=self.save_video)
        self.time_stamp = None
        self.time_display = tk.Label(self.root, text="0:00:00/0:00:00")
        self.is_playing = False
        self.seconds_passed = 0
        self.minutes_passed = 0
        self.frame = None

        self.screen_width = None
        self.video_width = None
        self.video_height = None

        self.begin = None
        self.end = None
        self.rectangle_border_width = 2

        self.vertical_edit = False
        self.horizontal_edit = False
        self.crop_box = self.create_rectangle(0, 0, 0, 0, width=self.rectangle_border_width, outline="red")

        self.end_width = None
        self.end_height = None
        self.ratio = None
        self.scale = None
        self.max_width = 1280
        self.max_height = 720

        self.frames = None
        self.duration = None
        self.time_slider = tk.Scale(self.root, orient="horizontal", showvalue=True, from_=0, label="0:00:00/0:00:00",
                                    length=self.max_width, command=self.update_time)
        self.time_slider.bind("<ButtonPress-1>", self.slider_press)
        self.time_slider.bind("<ButtonRelease-1>", self.slider_release)

        self.manual_slide = False
        self.previous_state = None
        self.first_press = True
        self.anchor = "center"
        if len(sys.argv) > 1:
            print(f"sys_arg={sys.argv}")
            self.load_video(sys.argv[1])

    def update_frame(self):
        if self.is_playing:
            print("is playing")
            ret, frame = self.cap.read()
            # self.time_stamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            # self.seconds_passed = math.floor(self.time_stamp/1000) % 60
            # self.minutes_passed = math.floor(self.time_stamp/1000/60)
            # self.time_display.config(text=f"{self.minutes_passed if self.minutes_passed > 9 else '0'+str(self.minutes_passed)}:{self.seconds_passed if self.seconds_passed > 9 else '0'+str(self.seconds_passed)}")
            print(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            print(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            print(self.cap.get(cv2.CAP_PROP_POS_MSEC))
            self.manual_slide = False
            if self.cap.get(cv2.CAP_PROP_POS_FRAMES) < self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                print("cap")
                self.time_stamp = datetime.timedelta(seconds=math.floor(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000))
                self.time_display.config(text=f'{self.time_stamp}/{self.duration}')
                self.time_slider.config(label=f'{self.time_stamp}/{self.duration}')
                print("config")
            else:
                print("cap2")
                self.time_stamp = self.duration
                self.time_display.config(text=f'{self.duration}/{self.duration}')
                self.time_slider.config(label=f'{self.time_stamp}/{self.duration}')
                self.pause()
            if ret:
                print("ret")
                self.manual_slide = False
                self.time_slider.set(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame).resize((self.end_width, self.end_height))
                self.photo = ImageTk.PhotoImage(image)
                self.itemconfig(self.frame, image=self.photo)
                print("updated frame")

        # temporary
        tkinter.Tk.update(self.root)
        self.root.after(self.delay, self.update_frame)

    def play(self):
        if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def stop(self):
        self.is_playing = False
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def load_video(self, file_path=False):
        self.pause()
        if not file_path:
            file_path = filedialog.askopenfilename()
        print(f'file_path={file_path}')
        if file_path:
            self.video_path = file_path
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            self.duration = datetime.timedelta(seconds=math.floor(self.frames/self.fps))
            self.time_display.config(text=f'0:00:00/{self.duration}')
            self.time_slider.set(0)
            self.time_slider.config(to=self.frames, label=f'0:00:00/{self.duration}')

            self.delay = int(1 / self.fps * 1000)
            print(f'delay={self.delay} fps={self.fps}')

            ret, frame = self.cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            self.video_width, self.video_height = image.size
            self.ratio = self.video_width/self.video_height
            print(f'ratio={self.ratio}')
            print(f'16/9={16/9}')
            print(self.ratio <= 16/9)
            if self.ratio <= 16/9:
                self.scale = self.max_height/self.video_height
                print("ratio>=16/9")
                self.end_width = int(self.video_width*self.scale)
                self.end_height = int(self.video_height*self.scale)
            else:
                self.scale = self.max_width / self.video_width
                self.end_width = int(self.video_width*self.scale)
                self.end_height = int(self.video_height*self.scale)
            print(f'end_width={self.end_width} end_height={self.end_height}')
            image = image.resize((self.end_width, self.end_height))
            # image = Image.fromarray(frame).resize((1280, 720))
            self.photo = ImageTk.PhotoImage(image)

            self.bind("<Button-1>", self.on_click)
            self.bind('<Button1-Motion>', self.on_motion)
            self.begin = {'x': self.rectangle_border_width*1.5, 'y': self.rectangle_border_width*1.5}
            print(f'begin={self.begin}')

            self.end = {'x': self.end_width-self.rectangle_border_width/2,
                        'y': self.end_height-self.rectangle_border_width/2}
            print(f'end={self.end}')
            print(f'video_width={self.video_width} video_height={self.video_height}')
            self.coords(self.crop_box, self.begin['x'], self.begin['y'], self.end['x'], self.end['y'])
            self.frame = self.create_image(0, 0, image=self.photo, anchor=tk.NW, )
            self.tag_raise(self.crop_box)
            self.configure(width=self.end_width, height=self.end_height)
            self.pack(anchor="center")
            self.update_frame()

    def save_video(self):
        file_name = self.video_path.split('/')[-1]
        file_path = filedialog.asksaveasfilename(initialfile=file_name)
        if file_path:
            ff = FFmpeg()
            x = int(round((self.begin["x"] - self.rectangle_border_width*1.5)/self.scale, 0))
            y = int(round((self.begin["y"] - self.rectangle_border_width*1.5)/self.scale, 0))
            output_width = int(round((self.end["x"]+self.rectangle_border_width/2 - (self.begin["x"] - self.rectangle_border_width*1.5))/self.scale, 0))
            output_height = int(round((self.end["y"]+self.rectangle_border_width/2 - (self.begin["y"] - self.rectangle_border_width*1.5))/self.scale, 0))
            print(f'video_width={self.video_width} video_height={self.video_height}')
            command = fr'-i "{self.video_path}" -filter:v "crop={output_width}:{output_height}:{x}:{y}" "{file_path}"'
            print(command)
            ff.options(command)

    def export(self):
        ff = FFmpeg()
        x = int(round(self.begin["x"]-self.rectangle_border_width/2, 0))
        y = int(round(self.begin["y"]-self.rectangle_border_width/2, 0))
        output_width = int(round(self.end["x"]-self.begin["x"]+self.rectangle_border_width, 0))
        output_height = int(round(self.end["y"]-self.begin["y"]+self.rectangle_border_width, 0))
        command = fr'-i "{self.video_path}" -filter:v "crop={output_width}:{output_height}:{x}:{y}" out.mp4'
        print(command)
        ff.options(command)

    def on_click(self, event):
        if abs(self.begin['y'] - event.y) < 10:
            print("top")
            self.vertical_edit = "top"
        elif abs(self.end['y'] - event.y) < 10:
            print("bottom")
            self.vertical_edit = "bottom"
        else:
            self.vertical_edit = False
        if abs(self.begin['x'] - event.x) < 10:
            print("left")
            self.horizontal_edit = "left"
        elif abs(self.end['x'] - event.x) < 10:
            print("right")
            self.horizontal_edit = "right"
        else:
            self.horizontal_edit = False

    def on_motion(self, event):
        if self.rectangle_border_width < event.y < self.end_height:
            if self.vertical_edit == "top":
                self.begin['y'] = event.y
            elif self.vertical_edit == "bottom":
                self.end['y'] = event.y
        if self.rectangle_border_width < event.x < self.end_width:
            if self.horizontal_edit == "left":
                self.begin['x'] = event.x
            elif self.horizontal_edit == "right":
                self.end['x'] = event.x

        if self.vertical_edit or self.horizontal_edit:
            self.coords(self.crop_box, self.begin['x'], self.begin['y'], self.end['x'], self.end['y'])

    def update_time(self, val):
        if self.video_path is not None:
            print(f'val={val} frame={self.cap.get(cv2.CAP_PROP_POS_FRAMES)}')
            if self.manual_slide:
                # self.cap.set(cv2.CAP_PROP_POS_FRAMES, float(val))
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame).resize((self.end_width, self.end_height))
                    self.photo = ImageTk.PhotoImage(image)
                    self.itemconfig(self.frame, image=self.photo)

                if self.cap.get(cv2.CAP_PROP_POS_FRAMES) < self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                    self.time_stamp = datetime.timedelta(seconds=math.floor(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000))
                    self.time_display.config(text=f'{self.time_stamp}/{self.duration}')
                    self.time_slider.config(label=f'{self.time_stamp}/{self.duration}')
                else:
                    self.time_stamp = self.duration
                    self.time_display.config(text=f'{self.duration}/{self.duration}')
                    self.time_slider.config(label=f'{self.time_stamp}/{self.duration}')
                    self.pause()
            self.manual_slide = True

    def slider_press(self, event):
        if self.video_path is not None:
            if self.first_press:
                self.first_press = False
                self.previous_state = self.is_playing

            self.pause()

    def slider_release(self, event):
        if self.video_path is not None:
            self.first_press = True
            self.is_playing = self.previous_state


player = VideoPlayer(tk.Tk())
player.pack()
player.time_slider.pack()
# player.time_display.pack()
player.load_button.pack()
player.play_button.pack()
player.pause_button.pack()
player.stop_button.pack()
player.export_button.pack()
player.mainloop()
