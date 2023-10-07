import datetime

import cv2
import numpy as np
import pytz
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from ttkbootstrap.tableview import Tableview
from ttkbootstrap import Style
from database import *
from tkinter import filedialog


profile_icon = None
DEFAULT_PROFILE_ICON_PATH = "images/Profile_Icon.png"
DEFAULT_BG_PATH = "images/wmsubg.png"


def create_driver(parent_tab):
    def selectPic():

        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        date = datetime.date.today().strftime("%Y-%m-%d")
        global img, filename
        filename = filedialog.askopenfilename(initialdir="/images", title="Select Image",
                                              filetypes=(("png images", "*.png"), ("jpg images", "*.jpg")))
        if filename:
            img = Image.open(filename)
            img = img.resize((250, 250), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(img)
            driver_image_label.image = img
            driver_image_label.config(image=driver_image_label.image)
        else:
            img = None
            driver_image_label.image = default_profile_icon
            driver_image_label.config(image=driver_image_label.image)

    def update_time_date(label):
        ph_tz = pytz.timezone('Asia/Manila')
        current_time = datetime.datetime.now(tz=ph_tz).strftime("%a, %Y-%m-%d %I:%M:%S %p")
        label.config(text=current_time)
        parent_tab.after(1000, lambda: update_time_date(label))


    colors = ttk.Style().colors

    drivers_data = db.child("Drivers").get().val()
    vehicles_data = db.child("Vehicles").get().val()

    coldata = [
        {"text": "Name", "stretch": True},
        {"text": "ID number", "stretch": True},
        {"text": "Plate number", "stretch": True},
        {"text": "Phone", "stretch": True},
        {"text": "Vehicle color", "stretch": True},
        {"text": "Vehicle type", "stretch": True},
        {"text": "Date", "stretch": True},
    ]

    rowdata = []

    # Populate rowdata with data from the database
    for driver_id, driver_info in drivers_data.items():
        if "name" in driver_info:
            driver_name = driver_info["name"]
            id_number = driver_info["id_number"]
            phone = driver_info["phone"]

            # Find the vehicles associated with this driver
            associated_vehicle_plate = []
            associated_vehicle_type = []
            associated_vehicle_color = []
            for vehicle_id, vehicle_info in vehicles_data.items():
                if "drivers" in vehicle_info and driver_id in vehicle_info["drivers"]:
                    associated_vehicle_plate.append(vehicle_info["plate_number"])
                    associated_vehicle_type.append(vehicle_info["vehicle_type"])
                    associated_vehicle_color.append(vehicle_info["vehicle_color"])

            # Add the driver's data to the rowdata
            rowdata.append([driver_name, id_number, ", ".join(associated_vehicle_plate), phone,
                            ", ".join(associated_vehicle_type), ", ".join(associated_vehicle_color),
                            ""])

    def save_driver():
        driver_id = id_entry.get()
        driver_name = name_entry.get()
        driver_phone = phone_entry.get()
        driver_plate = plate_entry.get()
        driver_vehicle_type = vehicle_type_entry.get()
        driver_vehicle_color = vehicle_color_entry.get()

        # Save driver's information
        driver_data = {
            'name': driver_name,
            'id_number': int(driver_id),
            'phone': int(driver_phone),
        }
        db.child('Drivers').child(driver_id).set(driver_data)

        # Check if the vehicle exists in Vehicles node
        vehicle_data = db.child('Vehicles').child(driver_plate).get().val()
        if vehicle_data is None:
            vehicle_data = {
                'plate_number': driver_plate,
                'vehicle_color': driver_vehicle_color,
                'vehicle_type': driver_vehicle_type,
                'drivers': {driver_id: True}
            }
        else:
            vehicle_data['drivers'][driver_id] = True
        db.child('Vehicles').child(driver_plate).set(vehicle_data)

        if driver_data:
            file = filename
            cloud_filename = f"driver images/{driver_id}.png"
            pyre_storage.child(cloud_filename).put(file)

        print("Driver Created")


    def view_driver():
        pass

    def update_driver():
        pass

    def delete_driver():
        pass

    def selected_row():

        id_entry.delete(0, END)
        name_entry.delete(0, END)
        plate_entry.delete(0, END)
        phone_entry.delete(0, END)
        vehicle_type_entry.delete(0, END)
        vehicle_color_entry.delete(0, END)

        selected_indices = tree_view.view.selection()  # Get the selected indices
        print('selected_indices: ', selected_indices)

        selected = tree_view.view.focus()
        values = tree_view.view.item(selected, 'values')

        id_nums = values[1]
        if len(id_nums) < 5:
            # Add leading zeros to make it 5 characters long
            id_nums = id_nums.zfill(5)

        name_entry.insert(0, values[0])
        id_entry.insert(0, values[1])
        plate_entry.insert(0, values[2])
        phone_entry.insert(0, values[3])
        vehicle_type_entry.insert(0, values[4])
        vehicle_color_entry.insert(0, values[5])

        print("id: ", id_nums)

        bucket = storage.bucket()
        blob = bucket.blob(f'driver images/{id_nums}.png')
        array = np.frombuffer(blob.download_as_string(), np.uint8)
        img_driver = cv2.imdecode(array, cv2.COLOR_BGR2RGB)

        driver_image = Image.fromarray(img_driver)
        driver_image = driver_image.resize((250, 250), Image.Resampling.LANCZOS)

        # Convert color channels from BGR to RGB
        driver_image = Image.merge("RGB", driver_image.split()[::-1])

        driver_image = ImageTk.PhotoImage(driver_image)

        driver_image_label.image = driver_image
        driver_image_label.config(image=driver_image_label.image)

    # Configure row and column weights
    parent_tab.grid_rowconfigure(0, weight=1)
    parent_tab.grid_columnconfigure(0, weight=1)
    parent_tab.grid_columnconfigure(1, weight=1)

    # Profile driver frame
    profile_driver_frame = ttk.Frame(parent_tab, width=200)
    profile_driver_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
    profile_driver_frame.grid_rowconfigure(0, weight=1)
    profile_driver_frame.grid_columnconfigure(0, weight=1)

    separator = ttk.Separator(parent_tab, orient=VERTICAL)
    separator.grid(row=0, column=2, rowspan=2, sticky="ns")

    # Daily logs table
    table_frame = ttk.Frame(parent_tab)
    table_frame.grid(row=0, column=3, sticky="nsew", padx=20, pady=20)
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # time date
    time_date_frame = ttk.Frame(table_frame)
    time_date_frame.grid(row=0, column=0, sticky="nsew", pady=20)
    time_date_frame.grid_rowconfigure(0, weight=1)
    time_date_frame.grid_columnconfigure(0, weight=1)

    # Label to display the time and date
    time_date_label = ttk.Label(time_date_frame, text="",
                                width=50, font=("Arial", 20, "bold"),
                                anchor='center')

    registered_label_text = ttk.Label(time_date_frame, text="REGISTERED DRIVER AND VEHICLE",
                                width=50, font=("Arial", 20, "bold"))

    # Center the label within the time_date_frame
    time_date_label.grid(row=0, column=0, sticky="nsew")
    registered_label_text.grid(row=1, column=0, sticky="nsew")

    # Start updating the time and date label
    update_time_date(time_date_label)

    # Specify a custom width for the Tableview (e.g., 800 pixels)
    tree_view = Tableview(
        master=table_frame,
        coldata=coldata,
        rowdata=rowdata,
        paginated=True,
        searchable=True,
        bootstyle=PRIMARY,
        stripecolor=None,
        autoalign=True,
    )
    tree_view.grid(row=1, column=0, rowspan=2, sticky="nsew")

    # Configure row and column weights for plate_frame
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_rowconfigure(1, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    # Profile icon label
    default_profile_icon_image = Image.open(DEFAULT_PROFILE_ICON_PATH)
    default_profile_icon_image = default_profile_icon_image.resize((250, 250), Image.Resampling.LANCZOS)
    default_profile_icon = ImageTk.PhotoImage(default_profile_icon_image)

    # Replace profile_icon_label with driver_image_label
    driver_image_label = ttk.Label(profile_driver_frame, image=default_profile_icon)
    driver_image_label.pack(pady=(10, 30))

    instruction_text = "Driver Details: "
    instruction = ttk.Label(profile_driver_frame, text=instruction_text, width=50)
    instruction.pack(fill=X, pady=10)

    name_label = ttk.Label(profile_driver_frame, text="Name:")
    name_label.pack(padx=5, pady=5, fill=BOTH)
    name_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    name_entry.pack(padx=5, pady=5, fill=BOTH)

    id_label = ttk.Label(profile_driver_frame, text="ID:")
    id_label.pack(padx=5, pady=5, fill=BOTH)
    id_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    id_entry.pack(padx=5, pady=5, fill=BOTH)

    phone_label = ttk.Label(profile_driver_frame, text="Phone:")
    phone_label.pack(padx=5, pady=5, fill=BOTH)
    phone_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    phone_entry.pack(padx=5, pady=5, fill=BOTH)

    plate_label = ttk.Label(profile_driver_frame, text="Plate number:")
    plate_label.pack(padx=5, pady=5, fill=BOTH)
    plate_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    plate_entry.pack(padx=5, pady=5, fill=BOTH)

    vehicle_type_label = ttk.Label(profile_driver_frame, text="Vehicle type:")
    vehicle_type_label.pack(padx=5, pady=5, fill=BOTH)
    vehicle_type_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    vehicle_type_entry.pack(padx=5, pady=5, fill=BOTH)

    vehicle_color_label = ttk.Label(profile_driver_frame, text="Vehicle color:")
    vehicle_color_label.pack(padx=5, pady=5, fill=BOTH)
    vehicle_color_entry = ttk.Entry(profile_driver_frame, font=('Helvetica', 13))
    vehicle_color_entry.pack(padx=5, pady=5, fill=BOTH)

    anchors = ttk.Style().configure('TButton', anchor='SW')

    insert_image_button = ttk.Button(profile_driver_frame, text="Insert Image", bootstyle=SUCCESS, style=anchors)
    insert_image_button.pack(padx=5, pady=(10), side=LEFT)
    insert_image_button['command'] = selectPic

    # Create a new frame for CRUD buttons
    crud_frame = ttk.LabelFrame(parent_tab, text='Actions')
    crud_frame.grid(row=1, column=3, sticky="nsew", padx=5, pady=5)
    crud_frame.grid_rowconfigure(0, weight=1)
    crud_frame.grid_columnconfigure(0, weight=1)

    # Add CRUD buttons
    create_button = ttk.Button(crud_frame, text="SAVE", command=save_driver, bootstyle=SUCCESS)
    read_button = ttk.Button(crud_frame, text="SELECT", command=selected_row, bootstyle=PRIMARY)
    update_button = ttk.Button(crud_frame, text="UPDATE", command=update_driver, bootstyle=PRIMARY)
    delete_button = ttk.Button(crud_frame, text="DELETE", command=delete_driver, bootstyle=DANGER)

    # Pack the buttons
    create_button.pack(side=LEFT, padx=10, pady=10)
    read_button.pack(side=LEFT, padx=10, pady=10)
    update_button.pack(side=LEFT, padx=10, pady=10)
    delete_button.pack(side=LEFT, padx=10, pady=10)






