# setup for idcam 18

# setting area for counting
draw_area = False
area_bawah = [(0,440), (0,390), (320,390), (320, 440), (0,440)]
area_atas = [(0,350), (0,300), (320,300), (320, 350), (0,350)]

area_bawah2 = [(340,440), (340,390), (640,390), (640, 440), (340,440)]
area_atas2 = [(340,350), (340,300), (640,300), (640, 350), (340,350)]


pedestrian = False
motorcycle = False
stuck = True
stuck_time = 180                        # detik

# 1 = flow dari atas ke bawah
# 2 = flow dari bawah ke atas
direction = 2
direction2 = 1
contraflow = True

speed_recognition = True
area_distance = 8                      # meter
traffic_jam = False
traffic_jam_count = 15                  # jumlah kendaraan sehingga disebut antrean
other_objects = False
vehicle_counting = False