# setup for idcam 18
# crop frame
x1 = 0
x2 = 300
y1 = 300
y2 = 440


# setting area for counting
draw_area = True
area_bawah = [(0,120), (0,70), (300,70), (300, 120), (0,120)]
area_atas = [(70,40), (70,20), (300,20), (300, 40), (70,40)]


pedestrian = False
motorcycle = False
stuck = True
stuck_time = 180                        # detik

# 1 = flow dari atas ke bawah
# 2 = flow dari bawah ke atas
direction = 2
contraflow = True

speed_recognition = True
area_distance = 15                      # meter
traffic_jam = True
traffic_jam_count = 15                  # jumlah kendaraan sehingga disebut antrean
other_objects = False
vehicle_counting = False